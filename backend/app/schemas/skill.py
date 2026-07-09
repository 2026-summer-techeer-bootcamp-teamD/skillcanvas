"""스킬 API 스키마. (API 명세서 5번 기준)

워크플로우(4번)와 동일 구조 — schemas/workflow.py를 복제해
graph_json(dict) → content_md(str) 로만 바꾼 것.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OwnerOut(BaseModel):
    id: int
    nickname: str
    model_config = ConfigDict(from_attributes=True)


# ── 요청 ──────────────────────────────────────────────
class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    content_md: str  # ★ 워크플로우의 graph_json(dict) 자리. 스킬은 SKILL.md 원문(str)
    tags: list[str] = Field(default_factory=list, max_length=5)
    is_public: bool = True  # 발행=공개 기본


class SkillUpdate(BaseModel):
    """변경할 필드만 보낸다. is_public 토글 = 나만보기.

    본문(content_md) 수정은 재발행 권장 → 여기 없음(워크플로우 방침과 동일).
    """

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = Field(default=None, max_length=5)
    is_public: bool | None = None


# ── 응답 ──────────────────────────────────────────────
class SkillListItem(BaseModel):
    id: int
    name: str
    description: str | None
    owner: OwnerOut
    tags: list[str]
    import_count: int
    created_at: datetime


class SkillSummary(BaseModel):
    """발행/수정 응답 (content_md 없는 요약형)."""

    id: int
    name: str
    owner: OwnerOut
    tags: list[str]
    import_count: int
    is_public: bool
    created_at: datetime
    updated_at: datetime


class SkillDetail(BaseModel):
    """상세 응답 (content_md 포함)."""

    id: int
    name: str
    description: str | None
    owner: OwnerOut
    tags: list[str]
    content_md: str  # ★ 워크플로우의 graph_json 자리
    import_count: int
    is_public: bool
    created_at: datetime
    updated_at: datetime


class SkillImportOut(BaseModel):
    id: int
    name: str
    content_md: str  # ★ 워크플로우의 graph_json 자리
    import_count: int


class SkillPage(BaseModel):
    items: list[SkillListItem]
    total: int
    limit: int
    offset: int
