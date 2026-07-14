"""유형 판단 API 스키마. (API 명세서 3-4)

자연어 요청이 스킬에 가까운지 워크플로우에 가까운지 판단.
Claude가 점수를 매기고, 백엔드가 최종 closer_to를 계산한다.
"""

from typing import Literal

from pydantic import BaseModel, Field


# ── 요청 ──────────────────────────────────────────────
class ClassifyRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


# ── 응답 ──────────────────────────────────────────────
class ClassifyScores(BaseModel):
    skill: int = Field(ge=0, le=100)
    workflow: int = Field(ge=0, le=100)


class ClassifyResponse(BaseModel):
    closer_to: Literal["skill", "workflow", "neutral"]
    confidence: int = Field(ge=0, le=100)  # 이긴 쪽 점수
    scores: ClassifyScores
    reason: str | None = None  # 관측용. 프론트는 미표시
