"""A-3: POST /run — 그래프를 받아 실행, 승인게이트서 멈춤."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.engine.runner import start_run

router = APIRouter(tags=["실행"])


class RunIn(BaseModel):
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)
    item_key: str = "demo-001"  # 중복체크용 식별자


@router.post("/run", summary="워크플로우 실행 (노드 순서 실행, 승인게이트서 중단)")
def run(payload: RunIn) -> dict:
    return start_run(payload.nodes, payload.edges, payload.item_key)
