from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import assemble, health, recommend, skills, tags, tool_catalog, users, workflows

app = FastAPI(
    title="SkillCanvas API",
    description="스킬 부품을 워크플로우로 조립하고 갤러리로 공유하는 플랫폼의 서버 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
