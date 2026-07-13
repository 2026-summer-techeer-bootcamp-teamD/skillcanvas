"""Claude(Anthropic) 공용 호출 모듈 — 백엔드 AI 기능(API 명세서 3장)용.

**팀원(3-1 assemble / 3-2 recommend / 3-3 map-node)은 이 모듈만 import 하면 됨.**
각자 client 만들지 말 것. deps.py(인증)/db.py(세션)처럼 core 공용부품.

이 모듈이 대신 처리해주는 것:
  - Anthropic client 준비 (키는 .env의 ANTHROPIC_API_KEY)
  - Claude 호출 실패 → **502 CLAUDE_UNAVAILABLE** (명세서 규격 그대로)
  - JSON 응답 파싱 실패 → **422 {도메인}_FAILED** (fail_code로 전달)
  - ```json 코드펜스 자동 제거

그래서 팀원은 **① 프롬프트(카탈로그 제약 포함) 작성 ② 결과 dict 쓰기** 만 하면 됨.

────────────────────────────────────────────────────────────
사용 예시 — 3-2 MCP 추천 (app/routers/recommend.py 에서):

    from app.core.llm import ask_claude_json

    SYSTEM = (
        "너는 SkillCanvas의 MCP 추천기다. 사용자의 자연어 요청을 읽고 "
        "아래 카탈로그 안에서만 붙일 MCP를 고른다. 없는 도구는 지어내지 마라.\\n"
        "반드시 JSON만 답한다: "
        '{"skill": str, "description": str, "mcps": [카탈로그 key]}\\n'
        "카탈로그: " + catalog_keys_str  # tool_catalog에서 뽑은 key 목록
    )
    data = ask_claude_json(SYSTEM, payload.text, fail_code="RECOMMEND_FAILED")
    # data["mcps"] 를 카탈로그 존재하는 key만 필터 후 반환
────────────────────────────────────────────────────────────
"""

import json
import logging

from anthropic import Anthropic, AnthropicError
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger("skillcanvas.llm")

# 키가 없으면 client 생성이 실패하므로 지연 생성(lazy). AI 안 쓰는 팀원도 앱은 뜸.
_client: Anthropic | None = None


def _get_client() -> Anthropic:
    global _client
    if not settings.anthropic_api_key:
        # 키 미설정 → 호출 시점에만 502 (앱 부팅은 막지 않음)
        raise HTTPException(
            502,
            {"code": "CLAUDE_UNAVAILABLE", "message": "Claude API 키가 설정되지 않았습니다"},
        )
    if _client is None:
        _client = Anthropic(api_key=settings.anthropic_api_key)
    return _client


def _strip_fence(text: str) -> str:
    """Claude가 ```json ... ``` 로 감싸 답할 때가 있어 펜스를 벗겨낸다."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]  # 첫 줄(``` 또는 ```json) 제거
        if t.endswith("```"):
            t = t[:-3]
    return t.strip()


def ask_claude(
    system: str,
    user: str,
    *,
    model: str | None = None,
    max_tokens: int = 2048,
) -> str:
    """Claude에 한 번 물어 **텍스트**를 받는다. 호출 실패 시 502.

    model 미지정 시 settings.anthropic_model(기본 haiku). 품질 필요한
    assemble(3-1)은 model="claude-sonnet-5" 로 넘겨 쓰길 권장.
    """
    client = _get_client()
    try:
        resp = client.messages.create(
            model=model or settings.anthropic_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        # content에 thinking 블록 등 text 아닌 블록이 섞일 수 있으니 text 블록만 모은다
        return "".join(
            getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text"
        )
    # AnthropicError=API/네트워크 실패, IndexError/AttributeError=빈/비-텍스트 응답.
    # 모두 Claude 쪽 문제이므로 명세서대로 502로 일관 처리한다.
    except (AnthropicError, IndexError, AttributeError) as e:
        # 실제 원인(크레딧 부족·레이트리밋·인증 등)은 서버 로그에 남긴다.
        # (외부 응답은 규격상 502 하나로 통일하되, 디버깅은 로그로)
        logger.warning("Claude 호출 실패 [%s]: %s", type(e).__name__, e)
        raise HTTPException(
            502, {"code": "CLAUDE_UNAVAILABLE", "message": "Claude 호출에 실패했습니다"}
        ) from e


def ask_claude_json(
    system: str,
    user: str,
    *,
    fail_code: str,
    model: str | None = None,
    max_tokens: int = 2048,
) -> dict:
    """Claude에 **JSON**을 시켜 dict로 파싱해 돌려준다. (3장 엔드포인트 공용)

    - Claude 호출 실패 → 502 CLAUDE_UNAVAILABLE (ask_claude가 던짐)
    - JSON 파싱 실패   → 422 fail_code (예: "RECOMMEND_FAILED")

    system 프롬프트에 "반드시 JSON만 답하라"를 꼭 넣을 것.
    """
    text = ask_claude(system, user, model=model, max_tokens=max_tokens)
    try:
        data = json.loads(_strip_fence(text))
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            422, {"code": fail_code, "message": "AI 응답을 해석하지 못했습니다"}
        ) from e
    # 유효한 JSON이라도 객체가 아니면(list/str/int/bool) 라우터가 dict로 다루다
    # AttributeError→500이 난다. 파싱 실패로 간주해 명세대로 422로 막는다.
    if not isinstance(data, dict):
        raise HTTPException(422, {"code": fail_code, "message": "AI 응답을 해석하지 못했습니다"})
    return data
