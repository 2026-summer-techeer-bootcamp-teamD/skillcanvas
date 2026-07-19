"""MCP 서버가 없는 REST API 도구 실행 (카탈로그 type: "api").

왜 필요한가:
  MCP로 부르려면 npx로 뜨는 MCP 서버가 있어야 하는데, 스마트택배 같은 국내 API는
  MCP 서버가 존재하지 않는다. 그렇다고 Claude에게 WebFetch로 부르게 하면 API 키가
  프롬프트에 들어가 대화 로그에 그대로 남는다.
  → 실행기가 직접 HTTP를 친다. 키는 credentials에서 읽어 쿼리스트링으로만 나가고
    **프롬프트엔 절대 들어가지 않는다.** 의존성 없이 stdlib urllib만 쓴다.

파라미터는 노드 detail(쿼리스트링)에서 받되, **비어 있으면 앞 단계(메일 읽기) 내용에서
송장번호·택배사를 자동 추출**한다 — 그래서 노드에 값을 안 박아도 메일의 송장번호로 조회된다.
  {"type": "tool", "label": "택배 조회", "mcp_key": "sweettracker", "detail": ""}
  # ← detail 비어도, 앞 메일에 "송장번호: 511951252170 / 택배사: CJ대한통운" 있으면 조회됨
"""

import json
import re
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
    """스마트택배 응답 → 사람이 읽을 한 줄. 응답 스키마가 달라도 안 죽게 전부 .get().

    ⚠️ 성공 응답에는 `status` 필드가 **아예 없다**. 실패일 때만 status=false + msg/code가 온다.
    (`if not data.get("status")` 로 짜면 성공을 실패로 오판한다 — 실제 조회로 확인함)
    """
    if data.get("status") is False:
        return f"조회 실패: {data.get('msg') or data.get('code') or '알 수 없는 오류'}"

    details = data.get("trackingDetails") or []
    last = details[-1] if isinstance(details, list) and details else {}
    when = last.get("timeString") or "?"
    where = last.get("where") or "?"
    kind = last.get("kind") or "?"
    if where == "?" and kind == "?":  # 예상과 다른 스키마 → 원문을 넘겨 뒤 agent가 읽게
        return json.dumps(data, ensure_ascii=False)[:600]

    state = "배송완료" if data.get("complete") else "배송중"
    item = (data.get("itemName") or "").split(",")[0].strip()[:40]  # 상품명이 아주 길다
    line = f"{state} · 최근 {when} {where} ({kind}) · {len(details)}단계"
    return line + (f" · 상품: {item}" if item else "")


_SUMMARIZERS = {"sweettracker": _summarize_sweettracker}


# 스마트택배 택배사 코드(국내) — 메일 본문의 택배사명 → 코드 매핑.
# 긴 이름을 먼저 두어 부분일치 오인('cj'가 다른 데 섞이는 것)을 줄인다.
_COURIER_CODES = {
    "cj대한통운": "04",
    "대한통운": "04",
    "우체국": "01",
    "한진택배": "05",
    "한진": "05",
    "로젠택배": "06",
    "로젠": "06",
    "롯데택배": "08",
    "롯데글로벌": "08",
    "롯데": "08",
    "경동택배": "23",
    "경동": "23",
    "대신택배": "22",
    "일양로지스": "11",
    "gs postbox": "24",
    "gs25": "24",
    "cvsnet": "24",
    "cj": "04",  # 마지막 폴백(짧은 별칭)
}


def _extract_sweettracker(text: str) -> dict:
    """앞 단계(메일 등) 내용에서 송장번호·택배사코드를 자동으로 뽑는다.

    detail에 파라미터를 안 넣어도, 메일에 '송장번호: …', '택배사: CJ대한통운'이 있으면
    그걸로 조회한다(데모/실사용 모두 이게 자연스럽다). 규칙 기반이라 결정론적이다.
    """
    out: dict[str, str] = {}
    # 송장번호: '송장' 근처의 숫자열 우선, 없으면 10~14자리 숫자열 폴백(주문번호 오인 방지 위해 자릿수 제한)
    m = re.search(r"송장[^0-9]{0,10}(\d[\d-]{8,}\d)", text) or re.search(r"\b(\d{10,14})\b", text)
    if m:
        out["t_invoice"] = m.group(1).replace("-", "")
    low = text.lower()
    for name, code in _COURIER_CODES.items():
        if name in low:
            out["t_code"] = code
            break
    return out


_EXTRACTORS = {"sweettracker": _extract_sweettracker}


def _history_text(history: list[dict] | None) -> str:
    return "\n".join(str(h.get("result", "")) for h in (history or []))


def call_api(tool_key: str, detail: str, history: list[dict] | None = None) -> dict:
    """{"text": 요약} 또는 {"error": 사유}. 예외를 던지지 않는다(런이 중간에 죽지 않게).

    파라미터는 detail(명시)이 우선. detail에 없는 필수 파라미터는 앞 단계(메일 등)
    내용에서 자동 추출해 채운다 — 그래서 노드 detail을 비워도 메일의 송장번호로 조회된다.
    """
    spec = API_TOOLS[tool_key]

    secret = _secret_for(tool_key, spec)
    if not secret:
        return {"error": f"키 미등록 — {spec['env_fields'][0]} 를 넣어주세요"}

    given = {k: v[0] for k, v in urllib.parse.parse_qs(detail or "").items() if v}
    # detail에 없는 필수 파라미터는 앞 단계 내용에서 자동 추출(명시값은 덮어쓰지 않음)
    if [p for p in spec["params"] if not given.get(p)] and history:
        extractor = _EXTRACTORS.get(tool_key)
        if extractor:
            for k, v in extractor(_history_text(history)).items():
                given.setdefault(k, v)
    missing = [p for p in spec["params"] if not given.get(p)]
    if missing:
        return {
            "error": f"파라미터 부족({', '.join(missing)}) — 메일에서 못 찾았어요. "
            f"detail에 {spec['params_help']}"
        }

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
