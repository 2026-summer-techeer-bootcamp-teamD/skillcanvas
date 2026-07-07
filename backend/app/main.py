from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import health, workflows

app = FastAPI(title="SkillCanvas API", version="0.1.0")

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

# ─────────────────────────────────────────────
# TODO: 아래 도메인도 workflows.py를 참고해 추가하세요. (API 명세서 기준)
#   from app.routers import users, skills, tags, tool_catalog, assemble
#   app.include_router(users.router, prefix="/api/v1")
#   app.include_router(skills.router, prefix="/api/v1")
#   ...
# ─────────────────────────────────────────────
