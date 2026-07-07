from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """created_at / updated_at 공통 컬럼 (전 테이블 공통, TIMESTAMPTZ).

    - `DateTime(timezone=True)` = Postgres TIMESTAMPTZ (타임존 포함, UTC 저장)
    - `server_default=func.now()` = INSERT 시 DB가 현재시각 자동 입력
    - `onupdate=func.now()` = UPDATE 시 updated_at 자동 갱신
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
