"""자연어 조립/추천/매핑 API 스키마. (API 명세서 3장: 3-1 assemble / 3-3 map-node)"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

NodeType = Literal["trigger", "tool", "agent", "approve", "branch"]


# ── 요청 ──────────────────────────────────────────────
class AssembleRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    context: list[str] = Field(default_factory=list)
    target: str = "workflow"  # workflow(기본) / skill


# ── 응답 ──────────────────────────────────────────────
class AssembleNode(BaseModel):
    id: str
    type: NodeType
    label: str
    detail: str | None = None


class AssembleEdge(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_: str = Field(alias="from")
    to: str
    # 분기 노드에서 나가는 엣지의 조건 라벨(branch 노드 detail의 '|' 라벨과 매칭).
    # 일반 엣지는 없음. 실행기가 이 값으로 어느 갈래를 탈지 고른다.
    when: str | None = None


class AssembleResponse(BaseModel):
    name: str
    nodes: list[AssembleNode]
    edges: list[AssembleEdge]
    used_mcps: list[str] = Field(default_factory=list)


# ── 3-3. 노드 자연어 편집/매핑 ────────────────────────
class MapNodeNode(BaseModel):
    type: NodeType
    label: str
    detail: str | None = None


class MapNodeRequest(BaseModel):
    node: MapNodeNode
    instruction: str


class MapNodeResponse(BaseModel):
    node: MapNodeNode
    mcp_added: str | None = None
