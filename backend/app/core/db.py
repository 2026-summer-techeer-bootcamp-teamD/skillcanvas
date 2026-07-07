from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, echo=False, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """모든 모델(SQLAlchemy 클래스)의 부모.

    모델은 app/models/ 에 정의한다. (ERD 확정 후 추가)
    """


def get_db() -> Generator[Session, None, None]:
    """엔드포인트에서 Depends(get_db) 로 DB 세션을 주입받는다."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
