"""A-1: GET /graph — .claude 파싱 결과(노드 그래프) 반환."""

from fastapi import APIRouter

from app.sync.graph import build_graph

router = APIRouter(tags=["부품 시각화"])


@router.get("/graph", summary="부품 시각화 (.claude → 노드 그래프)")
def get_graph() -> dict:
    return build_graph()
