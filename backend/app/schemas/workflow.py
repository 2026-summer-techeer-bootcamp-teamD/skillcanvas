"""워크플로우 API 스키마. (API 명세서 4번 기준)

스킬(5번)도 거의 동일 구조 — 이 파일을 복제해 graph_json→content_md로 바꾸면 된다.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OwnerOut(BaseModel):
    id: int
    nickname: str
    model_config = ConfigDict(from_attributes=True)


# ── 요청 ──────────────────────────────────────────────
class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    graph_json: dict
    tags: list[str] = Field(default_factory=list, max_length=5)
    is_public: bool = True  # 발행=공개 기본


class WorkflowUpdate(BaseModel):
    """변경할 필드만 보낸다. is_public 토글 = 나만보기."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = Field(default=None, max_length=5)
    is_public: bool | None = None


# ── 응답 ──────────────────────────────────────────────
class WorkflowListItem(BaseModel):
    id: int
    name: str
    description: str | None
    owner: OwnerOut
    tags: list[str]
    import_count: int
    is_public: bool  # 내 워크플로우 뷰에서 공개/비공개 배지 판단
    # tags/is_public처럼 기본값 없이 필수로 둔다 — _list_item이 항상 채우는 필드라
    # 기본값을 주면 나중에 빠뜨려도 조용히 []로 감춰지고 검증 에러가 나지 않는다.
    used_mcps: list[str]
    created_at: datetime


class WorkflowSummary(BaseModel):
    """발행/수정 응답 (graph_json 없는 요약형)."""

    id: int
    name: str
    owner: OwnerOut
    tags: list[str]
    import_count: int
    is_public: bool
    created_at: datetime
    updated_at: datetime


class WorkflowDetail(BaseModel):
    """상세 응답 (graph_json 포함)."""

    id: int
    name: str
    description: str | None
    owner: OwnerOut
    tags: list[str]
    graph_json: dict
    import_count: int
    is_public: bool
    created_at: datetime
    updated_at: datetime


class WorkflowImportOut(BaseModel):
    id: int
    name: str
    graph_json: dict
    import_count: int


class WorkflowPage(BaseModel):
    items: list[WorkflowListItem]
    total: int
    limit: int
    offset: int
