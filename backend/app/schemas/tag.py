"""태그 API 스키마. (API 명세서 6-1 기준)"""

from pydantic import BaseModel, ConfigDict


class TagItem(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class TagPage(BaseModel):
    items: list[TagItem]
    total: int
