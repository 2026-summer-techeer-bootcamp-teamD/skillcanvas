"""MCP 추천 API. (API 명세서 3-2)

자연어 요청 → 카탈로그 안에서 붙일 MCP를 추천.
Claude 호출은 app/core/llm.py 공용 모듈에 위임(502/422 에러도 모듈이 처리).
팀원은 프롬프트 작성 + 카탈로그 필터만 담당.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.llm import ask_claude_json
from app.models.tool_catalog import ToolCatalog
from app.models.user import User
from app.schemas.recommend import RecommendIn, RecommendOut

router = APIRouter(prefix="/recommend", tags=["자연어 추천"])


@router.post("", response_model=RecommendOut, summary="MCP 추천")
def recommend(
    payload: RecommendIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # ① 카탈로그에서 지원 도구 key 목록을 뽑는다 (추천은 이 안에서만)
    catalog = db.scalars(select(ToolCatalog.key)).all()

    # ② Claude에게 보낼 지시문. 카탈로그 제약 + JSON 형식을 명확히 지시.
    system = (
        "너는 SkillCanvas의 MCP 추천기다. 사용자의 자연어 요청을 읽고 "
        "아래 카탈로그 안에서만 붙일 MCP를 고른다. 없는 도구는 지어내지 마라.\n"
        "반드시 JSON만 답한다: "
        '{"skill": "추천 스킬명(kebab)", "description": "한 줄 설명", "mcps": ["카탈로그 key"]}\n'
        "맞는 도구가 없으면 mcps는 빈 배열로 둔다.\n"
        f"카탈로그: {list(catalog)}"
    )

    # ③ Claude 호출 (실패/파싱오류는 llm.py가 502/422로 처리)
    data = ask_claude_json(system, payload.text, fail_code="RECOMMEND_FAILED")

    # Claude가 필수 필드를 빠뜨렸으면 파싱 실패로 간주 → 422 (명세 3-2)
    if "skill" not in data or "description" not in data:
        raise HTTPException(
            422, {"code": "RECOMMEND_FAILED", "message": "AI 응답을 해석하지 못했습니다"}
        )

    # ④ 안전장치: Claude가 카탈로그에 없는 key를 냈으면 걸러낸다
    data["mcps"] = [m for m in data.get("mcps", []) if m in catalog]

    return data
