"""MCP 서버가 없는 REST API 도구 실행 (카탈로그 type: "api").

왜 필요한가:
  MCP로 부르려면 npx로 뜨는 MCP 서버가 있어야 하는데, 스마트택배 같은 국내 API는
  MCP 서버가 존재하지 않는다. 그렇다고 Claude에게 WebFetch로 부르게 하면 API 키가
  프롬프트에 들어가 대화 로그에 그대로 남는다.
  → 실행기가 직접 HTTP를 친다. 키는 credentials에서 읽어 쿼리스트링으로만 나가고
    **프롬프트엔 절대 들어가지 않는다.** 의존성 없이 stdlib urllib만 쓴다.

파라미터는 노드 detail에서 받는다(쿼리스트링 형식):
  {"type": "tool", "label": "택배 조회", "mcp_key": "sweettracker",
   "detail": "t_code=04&t_invoice=1234567890"}
"""

import json
import urllib.error
import urllib.parse
import urllib.request

from app.core import db

API_TOOLS: dict[str, dict] = {
    "sweettracker": {
        "url": "https://info.sweettracker.co.kr/api/v1/trackingInfo",
        "key_param": "t_key",  # 키가 들어갈 쿼리 파라미터명
        "env_fields": ["SWEETTRACKER_API_KEY"],
        "params": ["t_code", "t_invoice"],  # detail에서 받아야 하는 것
        "params_help": "t_code=택배사코드&t_invoice=송장번호 (예: t_code=04&t_invoice=1234567890)",
    },
}


def _secret_for(tool_key: str, spec: dict) -> str | None:
    """저장된 secret에서 API 키 한 개를 꺼낸다. JSON/평문 둘 다 지원."""
    raw = db.get_credential(tool_key)
    if not raw:
        return None
    field = spec["env_fields"][0]
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        parsed = None
    if isinstance(parsed, dict):
        val = str(parsed.get(field, "")).strip()
        return val or None
    return raw.strip() or None


def _summarize_sweettracker(data: dict) -> str:
    """스마트택배 응답 → 사람이 읽을 한 줄. 응답 스키마가 달라도 안 죽게 전부 .get()."""
    if not data.get("status"):
        return f"조회 실패: {data.get('msg') or data.get('code') or '알 수 없는 오류'}"
    details = data.get("trackingDetails") or []
    last = details[-1] if isinstance(details, list) and details else {}
    when = last.get("timeString") or "?"
    where = last.get("where") or "?"
    kind = last.get("kind") or "?"
    state = "배송완료" if data.get("complete") else "배송중"
    item = data.get("itemName") or ""
    if where == "?" and kind == "?":  # 예상과 다른 스키마 → 원문을 넘겨 AI가 읽게
        return json.dumps(data, ensure_ascii=False)[:600]
    line = f"{state} · 최근 {when} {where} ({kind})"
    return line + (f" · 상품: {item}" if item else "")


_SUMMARIZERS = {"sweettracker": _summarize_sweettracker}


def call_api(tool_key: str, detail: str) -> dict:
    """{"text": 요약} 또는 {"error": 사유}. 예외를 던지지 않는다(런이 중간에 죽지 않게)."""
    spec = API_TOOLS[tool_key]

    secret = _secret_for(tool_key, spec)
    if not secret:
        return {"error": f"키 미등록 — {spec['env_fields'][0]} 를 넣어주세요"}

    given = {k: v[0] for k, v in urllib.parse.parse_qs(detail or "").items() if v}
    missing = [p for p in spec["params"] if not given.get(p)]
    if missing:
        return {"error": f"파라미터 부족({', '.join(missing)}) — detail에 {spec['params_help']}"}

    query = {spec["key_param"]: secret, **{p: given[p] for p in spec["params"]}}
    url = f"{spec['url']}?{urllib.parse.urlencode(query)}"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            body = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")  # 400에도 사유 JSON이 담겨 온다
    except (urllib.error.URLError, TimeoutError) as e:
        return {"error": f"호출 실패: {e}"}

    try:
        data = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        return {"error": f"응답 파싱 실패: {body[:120]}"}

    summarize = _SUMMARIZERS.get(tool_key)
    return {"text": summarize(data) if summarize else json.dumps(data, ensure_ascii=False)[:600]}
