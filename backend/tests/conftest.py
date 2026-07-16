"""테스트 공용 픽스처. (pytest가 자동으로 읽음)

- db_session : 테스트마다 트랜잭션 → 끝나면 rollback (개발 DB 안 더럽힘)
- client     : get_db가 위 세션을 쓰도록 오버라이드한 FastAPI TestClient
- auth       : Bearer 헤더 생성 (스텁 인증 — 토큰 문자열 = 유저 식별자)
- mock_claude: AI 엔드포인트(assemble/recommend/map-node)의 Claude 호출 목킹

실행:  backend 폴더에서  `pytest`
전제:  개발 Postgres(docker) 실행 중 + `alembic upgrade head` 완료.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.models  # noqa: F401  모든 모델 등록(create_all 대비)
from app.core.db import Base, engine, get_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _tables():
    # 없는 테이블만 생성(있으면 그대로). 개발 DB엔 이미 마이그레이션돼 있음.
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session():
    """외부 트랜잭션에 세션을 묶고, 테스트 끝나면 rollback → 완전 격리."""
    connection = engine.connect()
    trans = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    """엔드포인트의 get_db가 위 트랜잭션 세션을 쓰게 오버라이드한 TestClient."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth():
    """auth('alice') -> {'Authorization': 'Bearer alice'}.

    인증 스텁: 토큰 문자열이 곧 유저 식별자(없으면 자동 생성).
    다른 유저 흉내 = 다른 문자열. 예) auth('alice') vs auth('bob').
    """

    def _headers(user_token: str = "tester"):
        return {"Authorization": f"Bearer {user_token}"}

    return _headers


@pytest.fixture
def mock_claude(monkeypatch):
    """AI 엔드포인트의 Claude 호출을 가짜로 대체(실제 Claude 안 부름 → 빠르고 무료).

    사용:
        mock_claude(return_value={"skill": "x", "description": "d", "mcps": []})
        mock_claude(raise_exc=HTTPException(502, {...}))   # 실패 케이스

    라우터가 `from app.core.llm import ask_claude_json` 로 가져다 쓰므로
    각 라우터 모듈의 이름을 패치한다.
    """

    def _set(return_value=None, raise_exc=None):
        def fake(*args, **kwargs):
            if raise_exc is not None:
                raise raise_exc
            return return_value

        for mod in ("app.routers.recommend", "app.routers.assemble", "app.routers.skills"):
            monkeypatch.setattr(f"{mod}.ask_claude_json", fake, raising=False)

    return _set
