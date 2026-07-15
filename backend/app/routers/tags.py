"""태그 API. (API 명세서 6-1)

- 필터 UI용 — 실제로 워크플로우·스킬에 연결되어 "사용 중"인 태그만 반환한다.
- 태그는 개수가 적어 페이지네이션 없이 전체 반환(명세서 의도된 예외).
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.master_tag import MasterTag
from app.models.skill_tag import SkillTag
from app.models.workflow_tag import WorkflowTag
from app.schemas.tag import TagPage

router = APIRouter(prefix="/tags", tags=["태그"])


# ── 6-1. 태그 목록 조회 ────────────────────────────────
@router.get("", response_model=TagPage, summary="태그 목록 조회")
def list_tags(db: Session = Depends(get_db)):
    stmt = select(MasterTag).where(
        or_(
            MasterTag.id.in_(select(WorkflowTag.master_tags_id)),
            MasterTag.id.in_(select(SkillTag.master_tags_id)),
        )
    )
    rows = db.scalars(stmt.order_by(MasterTag.name)).all()
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    return {"items": rows, "total": total}
