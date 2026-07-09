"""스킬 갤러리 API. (API 명세서 5번)

워크플로우(4번)의 app/routers/workflows.py를 복제해 만든 것.
바꾼 것 : Workflow→Skill, WorkflowTag→SkillTag, graph_json→content_md,
         에러코드 WORKFLOW_*→SKILL_*, prefix /workflows→/skills.
공유하는 것 : MasterTag(태그 마스터)는 워크플로우와 그대로 공유(새로 안 만듦).

핵심 규칙(컨벤션):
  - 소유권 판정은 **항상 토큰 유저(current_user)** 로. 쿼리 owner_id는 공개 필터로만.
  - 비공개(is_public=false)를 남이 조회/가져오기 → **404로 숨김**(403 아님).
  - 에러는 HTTPException(status, detail={code, message}).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_optional_user
from app.models.master_tag import MasterTag
from app.models.skill import Skill
from app.models.skill_tag import SkillTag
from app.models.user import User
from app.schemas.skill import (
    SkillCreate,
    SkillDetail,
    SkillImportOut,
    SkillPage,
    SkillSummary,
    SkillUpdate,
)

router = APIRouter(prefix="/skills", tags=["스킬"])


# ── 헬퍼: 태그 ────────────────────────────────────────
def _tag_names(db: Session, skill_id: int) -> list[str]:
    return list(
        db.scalars(
            select(MasterTag.name)
            .join(SkillTag, SkillTag.master_tags_id == MasterTag.id)
            .where(SkillTag.skills_id == skill_id)
            .order_by(MasterTag.name)
        )
    )


def _sync_tags(db: Session, skill_id: int, tag_names: list[str]) -> None:
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
            select(SkillTag).where(
                SkillTag.skills_id == skill_id,
                SkillTag.master_tags_id == tag.id,
            )
        )
        if link is None:
            db.add(SkillTag(skills_id=skill_id, master_tags_id=tag.id))


# ── 헬퍼: 응답 조립 ───────────────────────────────────
def _list_item(db: Session, sk: Skill) -> dict:
    return {
        "id": sk.id,
        "name": sk.name,
        "description": sk.description,
        "owner": sk.owner,
        "tags": _tag_names(db, sk.id),
        "import_count": sk.import_count,
        "created_at": sk.created_at,
    }


def _summary(db: Session, sk: Skill) -> dict:
    return {
        "id": sk.id,
        "name": sk.name,
        "owner": sk.owner,
        "tags": _tag_names(db, sk.id),
        "import_count": sk.import_count,
        "is_public": sk.is_public,
        "created_at": sk.created_at,
        "updated_at": sk.updated_at,
    }


def _detail(db: Session, sk: Skill) -> dict:
    # ★ 워크플로우는 graph_json, 스킬은 content_md
    return {**_summary(db, sk), "description": sk.description, "content_md": sk.content_md}


# ── 5-1. 목록 조회 ────────────────────────────────────
@router.get("", response_model=SkillPage, summary="스킬 목록 조회")
def list_skills(
    tag: str | None = None,
    sort: str = "recent",
    mine: bool = False,
    owner_id: int | None = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    stmt = select(Skill)
    if mine:
        if user is None:
            raise HTTPException(
                401, {"code": "AUTH_UNAUTHORIZED", "message": "로그인이 필요합니다"}
            )
        stmt = stmt.where(Skill.users_id == user.id)  # 내 것: 비공개 포함
    else:
        stmt = stmt.where(Skill.is_public.is_(True))  # 공개만
        if owner_id is not None:
            stmt = stmt.where(Skill.users_id == owner_id)  # 남의 공개만

    if tag:
        stmt = (
            stmt.join(SkillTag, SkillTag.skills_id == Skill.id)
            .join(MasterTag, MasterTag.id == SkillTag.master_tags_id)
            .where(MasterTag.name == tag.strip().lower())
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    order = Skill.import_count.desc() if sort == "popular" else Skill.created_at.desc()
    rows = db.scalars(stmt.order_by(order).limit(limit).offset(offset)).all()
    return {
        "items": [_list_item(db, sk) for sk in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ── 5-2. 상세 조회 ────────────────────────────────────
@router.get("/{skill_id}", response_model=SkillDetail, summary="스킬 상세 조회")
def get_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    sk = db.get(Skill, skill_id)
    # 없거나, 비공개인데 소유자가 아니면 → 404(존재 숨김)
    if sk is None or (not sk.is_public and (user is None or sk.users_id != user.id)):
        raise HTTPException(404, {"code": "SKILL_NOT_FOUND", "message": "스킬을 찾을 수 없습니다"})
    return _detail(db, sk)


# ── 5-3. 발행 ────────────────────────────────────────
@router.post("", response_model=SkillSummary, status_code=201, summary="스킬 발행")
def create_skill(
    payload: SkillCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sk = Skill(
        users_id=user.id,  # 소유자 = 토큰 유저 (요청으로 안 받음)
        name=payload.name,
        description=payload.description,
        content_md=payload.content_md,  # ★ 워크플로우는 graph_json
        is_public=payload.is_public,
    )
    db.add(sk)
    db.flush()  # id 확보
    _sync_tags(db, sk.id, payload.tags)
    db.commit()
    db.refresh(sk)
    return _summary(db, sk)


# ── 5-4. 수정 (is_public 토글 = 나만보기) ─────────────
@router.patch("/{skill_id}", response_model=SkillSummary, summary="스킬 수정 (나만보기 토글)")
def update_skill(
    skill_id: int,
    payload: SkillUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sk = db.get(Skill, skill_id)
    if sk is None:
        raise HTTPException(404, {"code": "SKILL_NOT_FOUND", "message": "스킬을 찾을 수 없습니다"})
    if sk.users_id != user.id:
        raise HTTPException(403, {"code": "SKILL_FORBIDDEN", "message": "소유자가 아닙니다"})

    if payload.name is not None:
        sk.name = payload.name
    if payload.description is not None:
        sk.description = payload.description
    if payload.is_public is not None:
        sk.is_public = payload.is_public
    if payload.tags is not None:
        db.execute(delete(SkillTag).where(SkillTag.skills_id == sk.id))
        _sync_tags(db, sk.id, payload.tags)

    db.commit()
    db.refresh(sk)
    return _summary(db, sk)


# ── 5-5. 삭제 ────────────────────────────────────────
@router.delete("/{skill_id}", status_code=204, summary="스킬 삭제")
def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sk = db.get(Skill, skill_id)
    if sk is None:
        raise HTTPException(404, {"code": "SKILL_NOT_FOUND", "message": "스킬을 찾을 수 없습니다"})
    if sk.users_id != user.id:
        raise HTTPException(403, {"code": "SKILL_FORBIDDEN", "message": "소유자가 아닙니다"})
    # 연결(정션) 먼저 삭제 후 본체 삭제 (FK 제약)
    db.execute(delete(SkillTag).where(SkillTag.skills_id == sk.id))
    db.delete(sk)
    db.commit()


# ── 5-6. 가져오기 ─────────────────────────────────────
@router.post("/{skill_id}/import", response_model=SkillImportOut, summary="스킬 가져오기")
def import_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sk = db.get(Skill, skill_id)
    # 비공개+남의 것이면 가져올 수 없음 → 404(숨김)
    if sk is None or (not sk.is_public and sk.users_id != user.id):
        raise HTTPException(404, {"code": "SKILL_NOT_FOUND", "message": "스킬을 찾을 수 없습니다"})
    sk.import_count += 1
    db.commit()
    db.refresh(sk)
    return {
        "id": sk.id,
        "name": sk.name,
        "content_md": sk.content_md,  # ★ 워크플로우는 graph_json
        "import_count": sk.import_count,
    }
