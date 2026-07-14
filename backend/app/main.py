from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.access_log import AccessLogMiddleware
from app.core.config import settings
from app.core.logging_config import configure_logging
from app.routers import assemble, health, recommend, skills, tags, tool_catalog, users, workflows


@asynccontextmanager
async def lifespan(app: FastAPI):
    # import 시점이 아니라 앱이 실제로 뜰 때만 루트 로거를 JSON 포맷으로 교체
    # (모듈 최상위에서 호출하면 테스트가 app.main을 import하기만 해도 로깅이 바뀌어버림)
    configure_logging()
    yield


app = FastAPI(
    title="SkillCanvas API",
    description="스킬 부품을 워크플로우로 조립하고 갤러리로 공유하는 플랫폼의 서버 API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청 단위 구조화(JSON) 로그. Loki+Promtail이 stdout을 스크랩해 handler/status/fail_code로 조회.
app.add_middleware(AccessLogMiddleware)

# Prometheus가 스크랩할 /metrics 노출 (Swagger 목록에는 안 뜨게 숨김)
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# 뼈대 확인용 (환경 세팅 됐는지 테스트)
app.include_router(health.router, prefix="/api/v1")

# 도메인 라우터. workflows = 팀원 복제용 예시 템플릿.
app.include_router(workflows.router, prefix="/api/v1")
app.include_router(skills.router, prefix="/api/v1")


app.include_router(users.router, prefix="/api/v1")
app.include_router(tags.router, prefix="/api/v1")
app.include_router(tool_catalog.router, prefix="/api/v1")
app.include_router(recommend.router, prefix="/api/v1")
app.include_router(assemble.router, prefix="/api/v1")
# ─────────────────────────────────────────────
