"""A-2: POST /save — 스킬 구조를 SKILL.md로 저장(본문 보존) 후 최신 그래프 반환."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.sync.graph import build_graph
from app.sync.save import save_skill

router = APIRouter(tags=["저장·동기화"])


class SaveIn(BaseModel):
    skill: str = Field(min_length=1, description="스킬 폴더명(식별자)")
    name: str = Field(min_length=1)
    description: str = ""
    allowed_tools: list[str] = Field(default_factory=list)


@router.post("/save", summary="저장·동기화 (그래프 → .claude, 본문 보존)")
def save(payload: SaveIn) -> dict:
    try:
        save_skill(payload.skill, payload.name, payload.description, payload.allowed_tools)
    except ValueError as e:
        raise HTTPException(400, {"code": "SAVE_INVALID_INPUT", "message": str(e)}) from e
    return build_graph()  # 저장 결과가 반영된 최신 그래프
