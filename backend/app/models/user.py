from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.skill import Skill
    from app.models.workflow import Workflow


class User(TimestampMixin, Base):
    """유저 — Clerk 계정을 우리 DB에 연결한 프로필.

    회원가입/로그인/비번은 Clerk가 담당. 우리는 clerk_user_id ↔ 우리 id 매칭 + nickname만 관리.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    clerk_user_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    nickname: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    workflows: Mapped[list[Workflow]] = relationship(back_populates="owner")
    skills: Mapped[list[Skill]] = relationship(back_populates="owner")
