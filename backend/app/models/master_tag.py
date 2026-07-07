from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import TimestampMixin


class MasterTag(TimestampMixin, Base):
    """마스터 태그 — 태그 원본 풀. 발행 시 없으면 자동 생성(get-or-create). name UNIQUE."""

    __tablename__ = "master_tags"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
