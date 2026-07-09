"""도구 카탈로그 API. (API 명세서 2-1)

- 지원하는 도구(MCP·API) 목록과 키 메타데이터를 반환한다.
- 키 붙여넣기 팝업(기능 3.4)이 이 응답으로 자동 생성된다.
- 카탈로그 데이터는 기본적으로 DB 시드(python -m app.seed_tools)로 채워진다. (2-2)
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.tool_catalog import ToolCatalog
from app.schemas.tool_catalog import ToolCatalogPage

router = APIRouter(prefix="/tool-catalog", tags=["도구 카탈로그"])


# ── 2-1. 카탈로그 목록 조회 ────────────────────────────
@router.get("", response_model=ToolCatalogPage, summary="카탈로그 목록 조회")
def list_tool_catalog(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    stmt = select(ToolCatalog)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(ToolCatalog.id.asc()).limit(limit).offset(offset)).all()
    return {
        "items": rows,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
