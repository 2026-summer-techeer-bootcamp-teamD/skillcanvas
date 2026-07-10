"""A-3: POST /run — 그래프를 받아 실행, 승인게이트서 멈춤.
A-4: GET /run/{id}/status — 실행 상태 조회.
A-5: POST /run/{id}/approve — 승인 대기 실행을 이어서 재개.
"""

from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core import db
from app.engine.runner import get_run, resume_run, start_run

router = APIRouter(tags=["실행"])


class RunIn(BaseModel):
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)
    # 중복체크용 식별자. 기본은 런마다 유니크 → 안 넘기면 항상 '신규'(사고 방지).
    # dedup을 시연/사용하려면 같은 값을 의도적으로 넘긴다.
    item_key: str = Field(default_factory=lambda: f"auto-{uuid4().hex[:8]}")


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


@router.post("/processed/reset", summary="중복체크 기록 초기화 (데모 리허설용)")
def processed_reset() -> dict:
    return {"ok": True, "deleted": db.clear_processed()}
