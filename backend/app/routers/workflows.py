"""워크플로우 갤러리 API — **팀원 복제용 예시 템플릿**. (API 명세서 4번)

스킬(5번)은 이 파일을 복제해서:
  - Workflow → Skill, WorkflowTag → SkillTag
  - graph_json → content_md
  - 도메인 에러코드 WORKFLOW_* → SKILL_*
만 바꾸면 거의 그대로 된다.

핵심 규칙(컨벤션):
  - 소유권 판정은 **항상 토큰 유저(current_user)** 로. 쿼리 owner_id는 공개 필터로만.
  - 비공개(is_public=false)를 남이 조회/가져오기 → **404로 숨김**(403 아님).
  - 에러는 HTTPException(status, detail={code, message}).
"""

from fastapi import APIRouter, Depends, HTTPException
from prometheus_client import Counter
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_optional_user
from app.models.master_tag import MasterTag
from app.models.user import User
from app.models.workflow import Workflow
from app.models.workflow_tag import WorkflowTag
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowDetail,
    WorkflowImportOut,
    WorkflowPage,
    WorkflowSummary,
    WorkflowUpdate,
)

router = APIRouter(prefix="/workflows", tags=["워크플로우"])

# 비즈니스 지표 (Grafana에서 "오늘 발행 수" 등에 사용)
WORKFLOW_PUBLISHED = Counter("workflow_published_total", "발행된 워크플로우 수")


# ── 헬퍼: 태그 ────────────────────────────────────────
def _tag_names(db: Session, workflow_id: int) -> list[str]:
    return list(
        db.scalars(
            select(MasterTag.name)
            .join(WorkflowTag, WorkflowTag.master_tags_id == MasterTag.id)
            .where(WorkflowTag.workflows_id == workflow_id)
            .order_by(MasterTag.name)
        )
    )


def _sync_tags(db: Session, workflow_id: int, tag_names: list[str]) -> None:
    """태그명 리스트를 받아 get-or-create 후 연결(중복 링크는 건너뜀)."""
    for raw in tag_names:
        name = raw.strip().lower()  # 정규화(대소문자·공백) → 중복 방지
        if not name:
            continue
        tag = db.scalar(select(MasterTag).where(MasterTag.name == name))
        if tag is None:
            tag = MasterTag(name=name)
            db.add(tag)
            db.flush()  # id 확보
        link = db.scalar(
            select(WorkflowTag).where(
                WorkflowTag.workflows_id == workflow_id,
                WorkflowTag.master_tags_id == tag.id,
            )
        )
        if link is None:
            db.add(WorkflowTag(workflows_id=workflow_id, master_tags_id=tag.id))


# ── 헬퍼: 응답 조립 ───────────────────────────────────
def _list_item(db: Session, wf: Workflow) -> dict:
    return {
        "id": wf.id,
        "name": wf.name,
        "description": wf.description,
        "owner": wf.owner,
        "tags": _tag_names(db, wf.id),
        "import_count": wf.import_count,
        "created_at": wf.created_at,
    }


def _summary(db: Session, wf: Workflow) -> dict:
    return {
        "id": wf.id,
        "name": wf.name,
        "owner": wf.owner,
        "tags": _tag_names(db, wf.id),
        "import_count": wf.import_count,
        "is_public": wf.is_public,
        "created_at": wf.created_at,
        "updated_at": wf.updated_at,
    }


def _detail(db: Session, wf: Workflow) -> dict:
    return {**_summary(db, wf), "description": wf.description, "graph_json": wf.graph_json}


# ── 4-1. 목록 조회 ────────────────────────────────────
@router.get("", response_model=WorkflowPage, summary="워크플로우 목록 조회")
def list_workflows(
    tag: str | None = None,
    sort: str = "recent",
    mine: bool = False,
    owner_id: int | None = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    stmt = select(Workflow)
    if mine:
        if user is None:
            raise HTTPException(
                401, {"code": "AUTH_UNAUTHORIZED", "message": "로그인이 필요합니다"}
            )
        stmt = stmt.where(Workflow.users_id == user.id)  # 내 것: 비공개 포함
    else:
        stmt = stmt.where(Workflow.is_public.is_(True))  # 공개만
        if owner_id is not None:
            stmt = stmt.where(Workflow.users_id == owner_id)  # 남의 공개만

    if tag:
        stmt = (
            stmt.join(WorkflowTag, WorkflowTag.workflows_id == Workflow.id)
            .join(MasterTag, MasterTag.id == WorkflowTag.master_tags_id)
            .where(MasterTag.name == tag.strip().lower())
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    order = Workflow.import_count.desc() if sort == "popular" else Workflow.created_at.desc()
    rows = db.scalars(stmt.order_by(order).limit(limit).offset(offset)).all()
    return {
        "items": [_list_item(db, wf) for wf in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ── 4-2. 상세 조회 ────────────────────────────────────
@router.get("/{workflow_id}", response_model=WorkflowDetail, summary="워크플로우 상세 조회")
def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    wf = db.get(Workflow, workflow_id)
    # 없거나, 비공개인데 소유자가 아니면 → 404(존재 숨김)
    if wf is None or (not wf.is_public and (user is None or wf.users_id != user.id)):
        raise HTTPException(
            404, {"code": "WORKFLOW_NOT_FOUND", "message": "워크플로우를 찾을 수 없습니다"}
        )
    return _detail(db, wf)


# ── 4-3. 발행 ────────────────────────────────────────
@router.post("", response_model=WorkflowSummary, status_code=201, summary="워크플로우 발행")
def create_workflow(
    payload: WorkflowCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    wf = Workflow(
        users_id=user.id,  # 소유자 = 토큰 유저 (요청으로 안 받음)
        name=payload.name,
        description=payload.description,
        graph_json=payload.graph_json,
        is_public=payload.is_public,
    )
    db.add(wf)
    db.flush()  # id 확보
    _sync_tags(db, wf.id, payload.tags)
    db.commit()
    db.refresh(wf)
    if wf.is_public:
        WORKFLOW_PUBLISHED.inc()
    return _summary(db, wf)


# ── 4-4. 수정 (is_public 토글 = 나만보기) ─────────────
@router.patch(
    "/{workflow_id}", response_model=WorkflowSummary, summary="워크플로우 수정 (나만보기 토글)"
)
def update_workflow(
    workflow_id: int,
    payload: WorkflowUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    wf = db.get(Workflow, workflow_id)
    if wf is None:
        raise HTTPException(
            404, {"code": "WORKFLOW_NOT_FOUND", "message": "워크플로우를 찾을 수 없습니다"}
        )
    if wf.users_id != user.id:
        raise HTTPException(403, {"code": "WORKFLOW_FORBIDDEN", "message": "소유자가 아닙니다"})

    was_public = wf.is_public

    if payload.name is not None:
        wf.name = payload.name
    if payload.description is not None:
        wf.description = payload.description
    if payload.is_public is not None:
        wf.is_public = payload.is_public
    if payload.tags is not None:
        db.execute(delete(WorkflowTag).where(WorkflowTag.workflows_id == wf.id))
        _sync_tags(db, wf.id, payload.tags)

    db.commit()
    db.refresh(wf)
    if wf.is_public and not was_public:
        WORKFLOW_PUBLISHED.inc()
    return _summary(db, wf)


# ── 4-5. 삭제 ────────────────────────────────────────
@router.delete("/{workflow_id}", status_code=204, summary="워크플로우 삭제")
def delete_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    wf = db.get(Workflow, workflow_id)
    if wf is None:
        raise HTTPException(
            404, {"code": "WORKFLOW_NOT_FOUND", "message": "워크플로우를 찾을 수 없습니다"}
        )
    if wf.users_id != user.id:
        raise HTTPException(403, {"code": "WORKFLOW_FORBIDDEN", "message": "소유자가 아닙니다"})
    # 연결(정션) 먼저 삭제 후 본체 삭제 (FK 제약)
    db.execute(delete(WorkflowTag).where(WorkflowTag.workflows_id == wf.id))
    db.delete(wf)
    db.commit()


# ── 4-6. 가져오기 ─────────────────────────────────────
@router.post(
    "/{workflow_id}/import", response_model=WorkflowImportOut, summary="워크플로우 가져오기"
)
def import_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    wf = db.get(Workflow, workflow_id)
    # 비공개+남의 것이면 가져올 수 없음 → 404(숨김)
    if wf is None or (not wf.is_public and wf.users_id != user.id):
        raise HTTPException(
            404, {"code": "WORKFLOW_NOT_FOUND", "message": "워크플로우를 찾을 수 없습니다"}
        )
    wf.import_count += 1
    db.commit()
    db.refresh(wf)
    return {
        "id": wf.id,
        "name": wf.name,
        "graph_json": wf.graph_json,
        "import_count": wf.import_count,
    }
