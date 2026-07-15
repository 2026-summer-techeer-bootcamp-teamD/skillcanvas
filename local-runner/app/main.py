"""로컬 실행기 (Local Runner) — 사용자 PC에서 도는 FastAPI 앱.

실행: local-runner 폴더에서
    uvicorn app.main:app --reload --port 4737
확인: http://localhost:4737/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import config
from app.routers import credential, graph, health, run, save

app = FastAPI(
    title="SkillCanvas Local Runner",
    description="사용자 PC의 .claude를 파싱·동기화·실행하는 로컬 실행기",
    version="0.1.0",
)

# 프론트(브라우저)가 localhost로 이 실행기를 호출하므로 CORS 허용.
# 허용 오리진은 config.CORS_ORIGINS (env RUNNER_CORS_ORIGINS로 배포 도메인 추가)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # 공개 HTTPS 사이트(배포 프론트) → localhost 러너 호출 시 Chrome이 보내는
    # Private Network Access 프리플라이트에 응답(없으면 오리진 허용해도 크롬이 차단).
    allow_private_network=True,
)

app.include_router(health.router)
app.include_router(graph.router)
app.include_router(save.router)
app.include_router(run.router)
app.include_router(credential.router)
