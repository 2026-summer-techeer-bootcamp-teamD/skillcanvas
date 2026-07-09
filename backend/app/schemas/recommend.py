"""MCP 추천 API 스키마. (API 명세서 3-2)

자연어 요청 → 카탈로그 안에서 붙일 MCP를 추천.
백엔드가 Claude를 호출해 결과를 만들며, 이 파일은 그 요청/응답 형태만 정의한다.
"""

from pydantic import BaseModel, Field


# ── 요청 ──────────────────────────────────────────────
class RecommendIn(BaseModel):
    text: str = Field(min_length=1, max_length=500)  # 자연어 요청


# ── 응답 ──────────────────────────────────────────────
class RecommendOut(BaseModel):
    skill: str  # 추천 스킬명
    description: str  # 한 줄 설명
    mcps: list[str] = Field(default_factory=list)  # 추천 MCP key (카탈로그 내). 없으면 []