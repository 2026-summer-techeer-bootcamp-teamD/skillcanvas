"""도구 카탈로그 API 스키마. (API 명세서 2-1 기준)"""

from pydantic import BaseModel, ConfigDict


class ToolCatalogItem(BaseModel):
    id: int
    key: str
    name: str
    type: str
    auth_owner: str
    key_required: bool
    key_issue_url: str | None
    description: str | None
    metadata_json: dict | None
    model_config = ConfigDict(from_attributes=True)


class ToolCatalogPage(BaseModel):
    items: list[ToolCatalogItem]
    total: int
    limit: int
    offset: int
