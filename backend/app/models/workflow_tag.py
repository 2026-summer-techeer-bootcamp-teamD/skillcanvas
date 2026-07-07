from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import TimestampMixin


class WorkflowTag(TimestampMixin, Base):
    """워크플로우 ↔ 태그 연결(M:N). surrogate PK(id) + 두 FK.

    UNIQUE(workflows_id, master_tags_id) 로 같은 쌍 중복 방지(비식별관계).
    """

    __tablename__ = "workflow_tags"
    __table_args__ = (UniqueConstraint("workflows_id", "master_tags_id", name="uq_workflow_tag"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    workflows_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("workflows.id"), nullable=False, index=True
    )
    master_tags_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("master_tags.id"), nullable=False, index=True
    )
