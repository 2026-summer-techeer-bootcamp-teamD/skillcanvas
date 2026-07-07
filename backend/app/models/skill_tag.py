from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import TimestampMixin


class SkillTag(TimestampMixin, Base):
    """스킬 ↔ 태그 연결(M:N). surrogate PK(id) + 두 FK.

    UNIQUE(skills_id, master_tags_id) 로 같은 쌍 중복 방지(비식별관계).
    """

    __tablename__ = "skill_tags"
    __table_args__ = (UniqueConstraint("skills_id", "master_tags_id", name="uq_skill_tag"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    skills_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("skills.id"), nullable=False, index=True
    )
    master_tags_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("master_tags.id"), nullable=False, index=True
    )
