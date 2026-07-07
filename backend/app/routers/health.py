from fastapi import APIRouter
from sqlalchemy import text

from app.core.db import engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """서버·DB 연결 상태 확인 (환경 세팅이 됐는지 테스트용).

    - Swagger(`/docs`)에서 이게 200 뜨면 환경 세팅 완료.
    - `db_connected: true` 면 Docker Postgres 연결까지 성공.
    """
    db_connected = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False
    return {"status": "ok", "db_connected": db_connected}
