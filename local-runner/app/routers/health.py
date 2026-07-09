"""헬스체크 — 로컬 실행기가 떠 있는지 확인용."""

from fastapi import APIRouter

router = APIRouter(tags=["상태"])


@router.get("/health", summary="로컬 실행기 상태 확인")
def health() -> dict:
    return {"status": "ok"}
