"""A-3: POST /run — 그래프를 받아 실행, 승인게이트서 멈춤.
A-4: GET /run/{id}/status — 실행 상태 조회.
A-5: POST /run/{id}/approve — 승인 대기 실행을 이어서 재개.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.engine.runner import get_run, resume_run, start_run

router = APIRouter(tags=["실행"])


class RunIn(BaseModel):
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)
    item_key: str = "demo-001"  # 중복체크용 식별자


def _run_or_404(out: dict | None) -> dict:
    if out is None:
        raise HTTPException(404, {"code": "RUN_NOT_FOUND", "message": "실행을 찾을 수 없습니다"})
    return out


@router.post("/run", summary="워크플로우 실행 (노드 순서 실행, 승인게이트서 중단)")
def run(payload: RunIn) -> dict:
    try:
        return start_run(payload.nodes, payload.edges, payload.item_key)
    except ValueError as e:
        raise HTTPException(400, {"code": "RUN_INVALID_INPUT", "message": str(e)}) from e


@router.get("/run/{run_id}/status", summary="실행 상태 조회")
def run_status(run_id: str) -> dict:
    return _run_or_404(get_run(run_id))


@router.post("/run/{run_id}/approve", summary="승인 게이트 재개 (이어서 실행)")
def run_approve(run_id: str) -> dict:
    return _run_or_404(resume_run(run_id))
