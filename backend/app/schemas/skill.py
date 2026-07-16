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
    # /assemble이 이미 카탈로그 대비 검증해 둔 key 목록. 서버에서 다시 한 번 필터링 후 저장
    # (content_md에서 regex로 역추출하던 방식의 위양성/위음성을 없애기 위함 — 이슈 #115).
    used_mcps: list[str] = Field(default_factory=list, max_length=20)


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
    is_public: bool  # 내 스킬 뷰에서 공개/비공개 배지 판단
    # tags/is_public처럼 기본값 없이 필수로 둔다 — _list_item이 항상 채우는 필드라
    # 기본값을 주면 나중에 빠뜨려도 조용히 []로 감춰지고 검증 에러가 나지 않는다.
    used_mcps: list[str]
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
