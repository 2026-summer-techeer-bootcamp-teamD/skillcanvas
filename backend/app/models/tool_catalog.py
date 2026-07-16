from sqlalchemy import BigInteger, Boolean, String, Text, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.db import Base
from app.models.mixins import TimestampMixin


class ToolCatalog(TimestampMixin, Base):
    """도구 카탈로그 — 우리가 시드로 넣는 지원 도구(MCP·API) 목록. 참조/lookup 테이블.

    - type: "mcp" | "api"
    - auth_owner: "user"(유저 본인 붙여넣기) | "developer"(우리 공용키)
    - metadata_json: 키 붙여넣기 팝업 세부(field·help·placeholder 등)
    """

    __tablename__ = "tool_catalog"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    key_issue_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    auth_owner: Mapped[str] = mapped_column(String(20), nullable=False)


def list_catalog_keys(db: Session) -> list[str]:
    """전체 카탈로그 key 목록 (assemble/skills/workflows 라우터가 공유하는 단일 소스).

    "실제 존재하는 도구인가"를 검증하는 모든 곳(AI 프롬프트 제약, 발행 시 used_mcps
    필터링, 목록 조회 시 스푸핑 방지)이 이 하나의 쿼리 결과를 기준으로 판단한다.
    """
    return list(db.scalars(select(ToolCatalog.key).order_by(ToolCatalog.key)))
