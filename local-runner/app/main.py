"""로컬 실행기 (Local Runner) — 사용자 PC에서 도는 FastAPI 앱.

실행: local-runner 폴더에서
    uvicorn app.main:app --reload --port 4737
확인: http://localhost:4737/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import graph, health

app = FastAPI(
    title="SkillCanvas Local Runner",
    description="사용자 PC의 .claude를 파싱·동기화·실행하는 로컬 실행기",
    version="0.1.0",
)

# 프론트(브라우저)가 localhost로 이 실행기를 호출하므로 CORS 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(graph.router)
