"""자연어 조립 API. (API 명세서 3-1)

사용자의 자연어 업무 설명을 워크플로우(또는 스킬) 그래프로 변환한다.
Claude 호출은 app/core/llm.py 공용 모듈이 처리(502/422 처리 포함) —
여기서는 ① 카탈로그 제약이 담긴 프롬프트를 짜고 ② 응답을 검증만 한다.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.llm import ask_claude_json
from app.models.tool_catalog import ToolCatalog
from app.models.user import User
from app.schemas.assemble import AssembleRequest, AssembleResponse

router = APIRouter(prefix="/assemble", tags=["자연어 조립"])


def _catalog_keys(db: Session) -> list[str]:
    return list(db.scalars(select(ToolCatalog.key).order_by(ToolCatalog.key)))


def _system_prompt(catalog_keys: list[str], target: str) -> str:
    kind = "스킬" if target == "skill" else "워크플로우"
    return (
        f"너는 SkillCanvas의 {kind} 조립기다. 사용자의 자연어 업무 설명을 읽고 "
        "노드·엣지로 이루어진 그래프로 변환한다.\n"
        "도구가 필요한 노드는 반드시 아래 카탈로그 key 안에서만 골라라. "
        "카탈로그에 없는 도구는 절대 지어내지 마라.\n"
        f"카탈로그: {', '.join(catalog_keys) if catalog_keys else '(없음)'}\n"
        "다른 설명 없이 반드시 아래 형태의 JSON만 답한다:\n"
        '{"name": "kebab-case 이름", '
        '"nodes": [{"id": str, "type": "trigger|tool|agent|approve", '
        '"label": str, "detail": str}], '
        '"edges": [{"from": 노드id, "to": 노드id}], '
        '"used_mcps": [실제로 쓴 카탈로그 key]}'
    )


# ── 3-1. 워크플로우 자동생성 ──────────────────────────
@router.post("", response_model=AssembleResponse, summary="워크플로우 자동생성")
def assemble(
    payload: AssembleRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    catalog_keys = _catalog_keys(db)
    system = _system_prompt(catalog_keys, payload.target)
    user_message = "\n".join([*payload.context, payload.text])

    data = ask_claude_json(
        system,
        user_message,
        fail_code="ASSEMBLE_FAILED",
        model="claude-sonnet-5",
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
