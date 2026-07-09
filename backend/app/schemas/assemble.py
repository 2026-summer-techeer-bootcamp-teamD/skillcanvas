"""자연어 조립 API 스키마. (API 명세서 3-1)"""

from pydantic import BaseModel, ConfigDict, Field


# ── 요청 ──────────────────────────────────────────────
class AssembleRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    context: list[str] = Field(default_factory=list)
    target: str = "workflow"  # workflow(기본) / skill


# ── 응답 ──────────────────────────────────────────────
class AssembleNode(BaseModel):
    id: str
    type: str
    label: str
    detail: str | None = None


class AssembleEdge(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_: str = Field(alias="from")
    to: str


class AssembleResponse(BaseModel):
    name: str
    nodes: list[AssembleNode]
    edges: list[AssembleEdge]
    used_mcps: list[str] = Field(default_factory=list)
