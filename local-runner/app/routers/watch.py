"""스케줄러 감시 워크플로우 API.

새 메일이 오면 자동 실행할 워크플로우를 로컬(runner.db)에 저장하고 on/off 한다.
실제 폴링 루프는 별도(스케줄러). 여기선 '무엇을 감시할지'만 저장·조회·해제한다.

- POST /watch        : 그래프 저장 + 감시 시작(enabled=1)
- GET  /watch        : 현재 감시 상태 조회
- POST /watch/stop   : 감시 중지(enabled=0, 그래프는 남겨둠)
"""

import json

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core import db

router = APIRouter(tags=["스케줄러"])


class WatchIn(BaseModel):
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)
    # 폴링 주기(초). 너무 짧으면 gmail을 과하게 두드린다 — 최소 10초.
    interval_sec: int = Field(default=30, ge=10, le=3600)


def _status() -> dict:
    """감시 상태를 그래프 본문 없이 요약해서 돌려준다(프론트 토글·표시용)."""
    w = db.get_watch()
    if w is None:
        return {"watching": False, "saved": False}
    try:
        graph = json.loads(w["graph_json"])
        node_count = len(graph.get("nodes", []))
    except (json.JSONDecodeError, TypeError):
        node_count = 0
    return {
        "watching": w["enabled"],
        "saved": True,
        "interval_sec": w["interval_sec"],
        "node_count": node_count,
        "updated_at": w["updated_at"],
    }


@router.post("/watch", summary="감시 워크플로우 저장 + 감시 시작")
def watch_start(payload: WatchIn) -> dict:
    graph_json = json.dumps({"nodes": payload.nodes, "edges": payload.edges}, ensure_ascii=False)
    db.save_watch(graph_json, payload.interval_sec)
    return _status()


@router.get("/watch", summary="감시 상태 조회")
def watch_status() -> dict:
    return _status()


@router.post("/watch/stop", summary="감시 중지 (그래프는 보존)")
def watch_stop() -> dict:
    db.set_watch_enabled(False)
    return _status()
