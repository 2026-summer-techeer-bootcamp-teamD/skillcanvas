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
import time

from anthropic import Anthropic, AnthropicError
from fastapi import HTTPException
from prometheus_client import Counter, Histogram

from app.core.config import settings

logger = logging.getLogger("skillcanvas.llm")

# Claude 호출 계측 (Grafana에서 model/status별로 조회). status: "success" | "error" | "parse_error"
# 기본 버킷(~10s)은 claude-sonnet-5 호출(10초 초과 흔함)이 전부 +Inf에 몰려 버킷 커스텀
AI_CALL_DURATION = Histogram(
    "ai_call_duration_seconds",
    "Claude API 호출 소요 시간(초)",
    ["model", "status"],
    buckets=(1, 2.5, 5, 10, 15, 20, 30, 45, 60, 90),
)
AI_CALL_TOTAL = Counter("ai_call_total", "Claude API 호출 횟수", ["model", "status"])

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
    used_model = model or settings.anthropic_model
    start = time.perf_counter()
    status = "error"
    try:
        client = _get_client()
        resp = client.messages.create(
            model=used_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        # content에 thinking 블록 등 text 아닌 블록이 섞일 수 있으니 text 블록만 모은다
        text = "".join(
            getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text"
        )
        status = "success"
        return text
    # AnthropicError=API/네트워크 실패, IndexError/AttributeError=빈/비-텍스트 응답.
    # 모두 Claude 쪽 문제이므로 명세서대로 502로 일관 처리한다.
    except (AnthropicError, IndexError, AttributeError) as e:
        # 실제 원인(크레딧 부족·레이트리밋·인증 등)은 서버 로그에 남긴다.
        # (외부 응답은 규격상 502 하나로 통일하되, 디버깅은 로그로)
        logger.warning("Claude 호출 실패 [%s]: %s", type(e).__name__, e)
        raise HTTPException(
            502, {"code": "CLAUDE_UNAVAILABLE", "message": "Claude 호출에 실패했습니다"}
        ) from e
    finally:
        # 키 미설정으로 _get_client()가 502를 던진 경우도 실패 호출로 집계된다.
        AI_CALL_DURATION.labels(model=used_model, status=status).observe(
            time.perf_counter() - start
        )
        # success는 여기서 세지 않는다 — ask_claude_json()이 JSON 파싱까지 끝난
        # 최종 결과(success/parse_error)를 보고 1건만 집계한다(이중 집계 방지).
        # error는 파싱 단계까지 갈 수 없는 경우라 여기서 확정 집계.
        if status == "error":
            AI_CALL_TOTAL.labels(model=used_model, status=status).inc()


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
    used_model = model or settings.anthropic_model
    text = ask_claude(system, user, model=model, max_tokens=max_tokens)
    try:
        data = json.loads(_strip_fence(text))
    except (json.JSONDecodeError, ValueError) as e:
        # Claude API 호출 자체는 성공했지만 응답을 못 써먹은 경우. ask_claude()는
        # 이 시점엔 아직 success를 집계하지 않았으므로 parse_error 1건만 남는다.
        AI_CALL_TOTAL.labels(model=used_model, status="parse_error").inc()
        raise HTTPException(
            422, {"code": fail_code, "message": "AI 응답을 해석하지 못했습니다"}
        ) from e
    # 유효한 JSON이라도 객체가 아니면(list/str/int/bool) 라우터가 dict로 다루다
    # AttributeError→500이 난다. 파싱 실패로 간주해 명세대로 422로 막는다.
    if not isinstance(data, dict):
        AI_CALL_TOTAL.labels(model=used_model, status="parse_error").inc()
        raise HTTPException(422, {"code": fail_code, "message": "AI 응답을 해석하지 못했습니다"})
    # 여기까지 왔다면 호출부터 파싱까지 완전히 성공한 논리적 요청 1건 → 여기서만 집계.
    AI_CALL_TOTAL.labels(model=used_model, status="success").inc()
    return data
