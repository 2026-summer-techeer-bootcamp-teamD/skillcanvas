"""자연어 조립/추천/매핑 API. (API 명세서 3장: 3-1 assemble / 3-3 map-node)

사용자의 자연어 업무 설명을 워크플로우(또는 스킬) 그래프로 변환하거나(3-1),
기존 노드를 자연어 지시로 재분류·재매핑한다(3-3).
Claude 호출은 app/core/llm.py 공용 모듈이 처리(502/422 처리 포함) —
여기서는 ① 카탈로그 제약이 담긴 프롬프트를 짜고 ② 응답을 검증만 한다.

경로가 도메인별로 다르므로(/assemble, /recommend, /map-node) 라우터에는
prefix를 두지 않고 엔드포인트마다 전체 경로를 명시한다.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.llm import ask_claude_json
from app.models.tool_catalog import list_catalog_keys
from app.models.user import User
from app.schemas.assemble import (
    AssembleRequest,
    AssembleResponse,
    MapNodeRequest,
    MapNodeResponse,
)

router = APIRouter(tags=["자연어 조립"])


def _system_prompt(catalog_keys: list[str], target: str) -> str:
    kind = "스킬" if target == "skill" else "워크플로우"
    return (
        f"너는 SkillCanvas의 {kind} 조립기다. 사용자의 자연어 업무 설명을 읽고 "
        "노드·엣지로 이루어진 그래프로 변환한다.\n"
        "도구가 필요한 노드는 반드시 아래 카탈로그 key 안에서만 골라라. "
        "카탈로그에 없는 도구는 절대 지어내지 마라.\n"
        f"카탈로그: {', '.join(catalog_keys) if catalog_keys else '(없음)'}\n"
        "detail 규칙: tool 노드의 detail은 반드시 위 카탈로그 key 하나만 넣어라(예: notion). "
        "trigger·agent·approve 노드의 detail은 10자 이내 짧은 힌트로. 긴 문장은 절대 쓰지 마라.\n"
        "트리거·읽기 규칙: 트리거(trigger) 노드는 '언제 시작하는가'만 알릴 뿐 데이터를 직접 "
        "가져오지 않는다. 그러니 업무가 외부에서 뭔가를 읽으며 시작하면(예: 새 메일을 읽고…), "
        "트리거 다음에 그 데이터를 **실제로 가져오는 도구(tool) 노드를 반드시** 둔다"
        "(예: gmail로 메일 읽기). 뒤의 판단·요약·분기 노드는 그 도구가 가져온 내용을 근거로 "
        "동작하므로, 이 읽기 노드가 없으면 뒤 단계가 빈손이 되어 오작동한다.\n"
        "분기(branch) 규칙: 업무가 '유형·조건을 판단해 경우에 따라 다르게 처리'하는 흐름이면 "
        "branch 노드를 써라. branch 노드의 detail은 가능한 갈래 라벨을 '|'로 이어 넣는다"
        "(예: 문의|제안). 그리고 그 branch 노드에서 나가는 엣지마다 when에 갈래 라벨을 정확히 "
        "적어라(그 라벨은 detail의 '|' 라벨 중 하나와 글자까지 똑같아야 한다). 갈래마다 엣지 "
        "하나씩, 각 갈래는 서로 다른 후속 노드로 이어진다. 조건 분기가 필요 없는 단순 흐름이면 "
        "branch를 쓰지 말고 when도 넣지 마라.\n"
        "다른 설명 없이 반드시 아래 형태의 JSON만 답한다:\n"
        '{"name": "kebab-case 이름", '
        '"nodes": [{"id": str, "type": "trigger|tool|agent|approve|branch", '
        '"label": str, "detail": str}], '
        '"edges": [{"from": 노드id, "to": 노드id, "when": "분기 갈래 라벨(분기 엣지만, 아니면 생략)"}], '
        '"used_mcps": [실제로 쓴 카탈로그 key]}'
    )


# ── 3-1. 워크플로우 자동생성 ──────────────────────────
@router.post("/assemble", response_model=AssembleResponse, summary="워크플로우 자동생성")
def assemble(
    payload: AssembleRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    catalog_keys = list_catalog_keys(db)
    system = _system_prompt(catalog_keys, payload.target)
    user_message = "\n".join([*payload.context, payload.text])

    data = ask_claude_json(
        system,
        user_message,
        fail_code="ASSEMBLE_FAILED",
        feature="assemble",
        model=settings.anthropic_assemble_model,
    )

    try:
        result = AssembleResponse(**data)
    except (ValidationError, TypeError) as e:
        raise HTTPException(
            422, {"code": "ASSEMBLE_FAILED", "message": "AI 응답 구조가 올바르지 않습니다"}
        ) from e

    # 카탈로그에 없는 key가 섞여 들어왔으면 서버에서 걸러낸다 (지어낸 도구 방지)
    catalog_set = set(catalog_keys)
    result.used_mcps = [m for m in result.used_mcps if m in catalog_set]
    return result


def _map_node_system_prompt(catalog_keys: list[str]) -> str:
    return (
        "너는 SkillCanvas의 노드 매핑기다. 현재 노드와 사용자의 수정 지시를 읽고 "
        "노드를 재분류·재매핑한다.\n"
        "도구가 필요한 노드는 반드시 아래 카탈로그 key 안에서만 골라라. "
        "카탈로그에 없는 도구는 절대 지어내지 마라.\n"
        f"카탈로그: {', '.join(catalog_keys) if catalog_keys else '(없음)'}\n"
        "detail 규칙: tool 노드의 detail은 반드시 위 카탈로그 key 하나만 넣어라(예: notion). "
        "trigger·agent·approve 노드의 detail은 10자 이내 짧은 힌트로. 긴 문장은 절대 쓰지 마라.\n"
        "다른 설명 없이 반드시 아래 형태의 JSON만 답한다:\n"
        '{"node": {"type": "trigger|tool|agent|approve|branch", "label": str, "detail": str}, '
        '"mcp_added": "새로 필요해진 카탈로그 key 또는 null"}'
    )


# ── 3-3. 노드 자연어 편집/매핑 ────────────────────────
@router.post("/map-node", response_model=MapNodeResponse, summary="노드 자연어 편집/매핑")
def map_node(
    payload: MapNodeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    catalog_keys = list_catalog_keys(db)
    system = _map_node_system_prompt(catalog_keys)
    user_message = f"현재 노드: {payload.node.model_dump_json()}\n수정 지시: {payload.instruction}"

    data = ask_claude_json(system, user_message, fail_code="MAP_NODE_FAILED", feature="map_node")

    try:
        result = MapNodeResponse(**data)
    except (ValidationError, TypeError) as e:
        raise HTTPException(
            422, {"code": "MAP_NODE_FAILED", "message": "AI 응답 구조가 올바르지 않습니다"}
        ) from e

    # 카탈로그에 없는 key가 섞여 들어왔으면 무시한다 (지어낸 도구 방지)
    catalog_set = set(catalog_keys)
    if result.mcp_added not in catalog_set:
        result.mcp_added = None
    return result
