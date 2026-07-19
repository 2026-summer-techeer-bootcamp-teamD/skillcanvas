"""노드 타입별 실행 + 하네스 중복체크(processed). PoC execNode 이식.

반환: {"result": str, "pause"?: bool, "stop"?: bool}
  - pause: 승인 게이트 → 실행 멈춤(awaiting_approval)
  - stop: 중복 등으로 실행 중단(stopped)

중복체크(processed)는 SQLite(core/db.py)에 저장 → 서버 재시작에도 유지.
"""

from app.core import api_tools, db, mcp
from app.core.claude import claude_call

# claude가 가끔 붙이는 메타 서두(결과 아님) — 이런 줄은 건너뛴다
_META_HINTS = (
    "출력합니다",
    "출력하겠습니다",
    "결과물만",
    "결과만 출력",
    "단계군요",
    "단계의 결과물",
)

# agent 노드가 웹검색을 켤지 판단하는 키워드. label/detail에 이게 있으면 검색 허용.
# 기본은 검색 끔 — 답변·요약·판단 노드는 검색이 필요 없는데 켜두면 모델이 괜히
# 웹검색을 시도해 느려지거나 간헐적으로 타임아웃 난다. (뉴스 수집은 보통 web-search
# tool 노드가 따로 하므로 agent는 검색이 거의 불필요.)
_SEARCH_HINTS = ("검색", "뉴스", "조사", "찾아", "최신", "search", "news")


def _needs_search(label: str, detail: str) -> bool:
    hay = f"{label} {detail}".lower()
    return any(h in hay for h in _SEARCH_HINTS)


def _clean(text: str, limit: int = 1200) -> str:
    """claude 응답에서 앞쪽 메타 서두 줄만 걷어내고 본문은 그대로 살린다.

    예전엔 '첫 유효 한 줄'만 200자로 잘랐다. 그러면 뉴스 요약처럼 불릿 여러 줄인
    결과물이 첫 줄 하나로 뭉개져서, 실제로 검색해 온 내용이 대부분 버려졌다.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return ""
    for i, ln in enumerate(lines):
        if not any(h in ln for h in _META_HINTS):
            return "\n".join(lines[i:])[:limit]
    return lines[-1][:limit]  # 전부 메타 서두인 경우


def _agent_prompt(
    label: str, detail: str, history: list[dict] | None, can_search: bool = False
) -> str:
    """이전 단계 결과를 맥락으로 넣어, agent가 흐름을 반영해 판단/생성하게 한다.

    can_search=False면 이 노드는 WebSearch가 꺼진 상태 → "검색해서 쓰라"는 지시를
    빼야 한다(도구 없이 검색하라고 하면 모델이 거절하거나 사실을 지어낸다).
    """
    steps = "\n".join(f"- {h['label']}: {h['result']}" for h in history) if history else ""
    if can_search:
        search_rule = (
            "- 최신 정보·뉴스·외부 사실이 필요하면 WebSearch/WebFetch로 직접 찾아서 쓴다. "
            "절대 지어내지 말고, 못 찾으면 못 찾았다고 쓴다.\n"
            "- 이전 단계의 '🔌 도구 실행' 줄은 실제 데이터가 아니라 실행 기록일 뿐이다. "
            "거기서 데이터를 기대하지 말고 필요하면 직접 검색해라.\n"
        )
    else:
        # 검색 없는 노드(답변·요약·판단): 앞 단계가 준 내용만으로 처리. 외부 사실을
        # 지어내지 말고, 정보가 부족하면 부족하다고 쓴다.
        search_rule = (
            "- 앞 단계들이 준 내용만으로 이번 결과를 만든다. 외부 사실을 새로 지어내지 말고, "
            "필요한 정보가 없으면 '(정보 없음)'이라고 쓴다.\n"
        )
    return (
        "너는 업무 자동화 워크플로우의 한 단계를 수행하는 에이전트다.\n"
        f"[지금까지 진행된 단계와 결과]\n{steps or '(이전 단계 없음)'}\n\n"
        f"[이번 단계] {label} ({detail})\n\n"
        "규칙:\n"
        "- 위 맥락을 반영해 '이번 단계의 최종 결과물' 자체만 출력한다.\n"
        "- 인사말·상황설명·'~단계군요'·'~하겠습니다' 같은 메타 발언 절대 금지.\n"
        "- 예를 들어 '사과문 생성'이면 사과문 문장 자체를, '긴급도 판단'이면 판단 결과를 바로 쓴다.\n"
        f"{search_rule}"
        "- 앞 단계가 항목마다 `[출처: URL]`을 줬으면 **그 링크를 요약에도 항목별로 그대로 유지**한다. "
        "URL을 새로 지어내지는 마라.\n"
        "- 한국어, 결과 텍스트만. 요약·목록이면 불릿 5개 이내, 그 외엔 3문장 이내."
    )


def _branch_prompt(label: str, routes: list[str], history: list[dict] | None) -> str:
    """분기 노드용 — 앞 단계 내용을 보고 정해진 라벨 중 하나만 고르게 한다."""
    steps = "\n".join(f"- {h['label']}: {h['result']}" for h in history) if history else ""
    opts = " / ".join(routes)
    return (
        f"너는 업무 자동화 워크플로우의 분기 판단 단계 '{label}'다.\n"
        f"[지금까지 진행된 단계와 결과]\n{steps or '(이전 단계 없음)'}\n\n"
        f"위 내용을 읽고 아래 유형 중 **정확히 하나**로 분류하라.\n"
        f"[가능한 유형] {opts}\n\n"
        "규칙:\n"
        f"- 반드시 위 유형 중 하나의 라벨만 출력한다. 다른 말·설명·기호 절대 금지.\n"
        f"- 예: 답이 '{routes[0]}'이면 오직 '{routes[0]}' 다섯 글자 이내로만 출력.\n"
        "- 애매하면 가장 가까운 하나를 고른다. 여러 개 나열 금지."
    )


def _parse_route(text: str, routes: list[str]) -> str:
    """모델 출력에서 라벨 하나를 뽑는다. 정확 일치 → 포함 → 첫 라벨 폴백."""
    t = (text or "").strip()
    for r in routes:  # 정확히 그 라벨을 말했나
        if t == r:
            return r
    for r in routes:  # 문장 안에 라벨이 들어있나
        if r in t:
            return r
    return routes[0]  # 못 고르면 첫 번째(안전 폴백)


def _mcp_key(node: dict) -> str:
    """tool 노드가 쓸 카탈로그 key를 고른다.

    프론트가 mcp_key를 보내주면 그게 정답. 안 보내는 경우를 위해 detail·label로 폴백한다
    (assemble 노드는 detail이 key, 추천패널 노드는 detail이 "mcp.call"이고 label이 key).
    """
    known = set(mcp.MCP_SERVERS) | set(mcp.BUILTIN_TOOLS) | set(api_tools.API_TOOLS)
    for cand in (node.get("mcp_key"), node.get("detail"), node.get("label")):
        k = (cand or "").strip().lower()
        if k in known:
            return k
    return (node.get("mcp_key") or node.get("label") or "").strip().lower()


_COMMON_TOOL_RULES = (
    "- 도구를 실제로 호출하라. 호출한 척하고 보고만 하지 마라.\n"
    "- 인사말·해명·'짚어둘 점이 있습니다' 같은 메타 발언 절대 금지. 결과만 쓴다.\n"
    "- 이 단계에서 할 수 없는 일(다음 단계 몫)을 왜 안 했는지 설명하지 마라.\n"
)


def _tool_prompt(label: str, detail: str, history: list[dict] | None, role: str = "auto") -> str:
    """도구 노드용 프롬프트. role에 따라 지시가 완전히 달라진다.

    ⚠️ 예전엔 발송(telegram/discord) 전제로만 썼다("앞 결과물을 전송하라", "어디로 보냈는지
    보고하라"). 그러면 web-search 같은 **수집** 도구에서 AI가 혼란에 빠져
    "어디로도 전송하지 않았습니다 — 이번 단계는 검색 단계일 뿐이고..." 하는 해명을
    길게 늘어놓는다(실제로 그랬다).

    role: "fetch"(수집·조회) | "send"(발송) | "auto"(라벨 보고 판단 — gmail처럼 둘 다 되는 도구)
    """
    steps = "\n".join(f"- {h['label']}: {h['result']}" for h in history) if history else ""
    head = (
        f"너는 업무 자동화 워크플로우의 '{label}' 도구 단계다.\n"
        f"[지금까지 진행된 단계와 결과]\n{steps or '(이전 단계 없음)'}\n\n"
        f"[이번 단계] {label} ({detail})\n\n규칙:\n"
    )

    if role == "fetch":
        return head + (
            "- 이 단계는 **수집·조회** 단계다. 어디로도 보내지 않는다. 발송은 다음 단계 몫이다.\n"
            "- 도구로 가져온 내용을 **다음 단계가 바로 쓸 수 있게** 정리해 출력한다.\n"
            "- 한국어 불릿 5개 이내. 각 줄은 '제목 — 핵심 한 줄'.\n"
            "- **각 항목 끝에 그 내용을 실제로 확인한 기사 URL을 `[출처: https://...]` 형태로 붙인다.** "
            "항목마다 개별 링크가 원칙이고, 검색 결과에 그 항목의 URL이 없으면 링크를 지어내지 말고 생략한다.\n"
            "- 못 찾았으면 못 찾았다고만 쓴다. 없는 사실·없는 링크를 지어내지 마라.\n"
            + _COMMON_TOOL_RULES
        )

    if role == "send":
        return head + (
            "- 이 단계는 **발송** 단계다. 앞 단계들이 만든 **결과물**(요약·사과문 등, 보통 🧠 나 🔌 로 "
            "시작하는 줄의 내용)을 전송한다.\n"
            "- **사실은 앞 결과물에서만 가져온다. 없는 내용을 새로 지어내지 마라.** 다만 그대로 붙여넣지 말고 "
            "받는 사람이 읽기 좋게 **다듬어서** 보낸다.\n"
            "- 메신저(텔레그램·디스코드·슬랙)로 보내는 브리핑/요약이면 이 틀을 따른다:\n"
            "    · 첫 줄: 한 줄 제목 + 날짜 (예: 📱 오늘의 AI 브리핑 — 2026.7.16)\n"
            "    · 항목마다 '번호. 굵은 소제목 (관련 이모지)' 다음 줄에 2~3문장 설명, 항목 사이 빈 줄\n"
            "    · 앞 단계가 항목마다 `[출처: URL]`을 줬으면, 맨 아래 '🔗 출처'에 **항목 번호와 함께** "
            "'1. https://...' 처럼 개별 링크로 나열한다. 링크가 없는 항목은 번호만 두거나 생략한다. "
            "**URL을 새로 지어내지 마라 — 앞 단계가 준 것만 쓴다.**\n"
            "  이메일이면 인사–본문–맺음의 격식 있는 편지 형식으로. 내용 성격에 맞는 틀을 골라라.\n"
            "  **노션이면** 앞 결과물을 **새 페이지로 생성**한다. 제목은 **맨 앞에 유형 태그를 "
            "대괄호로** 붙이고(메일 제목에 이미 '[…]' 태그가 있으면 그대로 쓰고, 없으면 분류 결과로 "
            "만든다 — 예: [제휴 제안]), 그 뒤에 메일 핵심을 한 줄로, **끝에 앞 단계 '메일 읽기'에 "
            "나온 그 메일의 실제 수신일을 'YYYY-MM-DD' 형식으로 괄호에 넣는다**. ⚠️ 예시나 아무 날짜나 "
            "그대로 베끼지 말고, **반드시 이 메일의 실제 수신일**을 써라(형식만 참고: '[태그] 핵심 한 줄 "
            "(YYYY-MM-DD)'). 목록에서 열어보지 않고도 유형과 언제 온 메일인지 알 수 있게 한다. "
            "본문은 맨 위에 실제 수신일을 '수신일: YYYY-MM-DD'로 적고, 그 아래를 "
            "**굵은 소제목으로 구획을 나눠**(예: 제안사 / 제안 내용 / 조건 / 기대 효과 / "
            "요청·연락처) 각 항목을 **개별 불릿**으로 정리한다. 앞 결과물의 구체 정보(숫자·조건·기간·"
            "연락처 등)를 **한 줄에 뭉뚱그리지 말고 항목별로 그대로 살리고, 내용을 임의로 줄이지 마라**. "
            "만들 위치는 [이번 단계]의 detail에 적힌 페이지/DB 이름으로 **먼저 검색(search)** 해서 그 "
            "페이지를 부모로 삼고, detail이 비었으면 접근 가능한 페이지 중 적절한 곳에 만든다. "
            "**반드시 페이지 생성 도구를 실제로 호출**하고, 텍스트만 출력한 채 끝내지 마라.\n"
            "- ⏱ 트리거 / 🚨 승인 게이트 / 🔁 중복체크 / ✅ 검증 줄은 워크플로우 내부 실행 기록이다. "
            "**절대 전송 내용으로 쓰지 마라.** 결과물 앞의 이모지 접두사(🧠 🔌)도 빼고 보낸다.\n"
            "- 끝나면 무엇을 어디로 보냈는지 한국어 1문장으로만 보고한다.\n" + _COMMON_TOOL_RULES
        )

    return head + (
        "- 이번 단계의 목적은 위 [이번 단계]에 적혀 있다. 그 목적에 맞게 도구를 호출하라.\n"
        "- 목적이 **읽기·조회**면 가져온 내용을 정리해 출력한다(어디로도 보내지 않는다).\n"
        "- 목적이 **발송**이면 앞 단계 결과물을 그대로 보낸다. ⏱🚨🔁✅ 줄은 내부 기록이니 보내지 마라.\n"
        "- 한국어로 간결하게. 결과만 쓴다.\n" + _COMMON_TOOL_RULES
    )


def exec_node(node: dict, ctx: dict, history: list[dict] | None = None) -> dict:
    t = node.get("type")
    label = node.get("label", "")
    detail = node.get("detail", "")

    if t == "trigger":
        return {"result": "⏱ 트리거 발동 — 실행 시작"}

    if t in ("agent", "ai"):  # 에이전트 = Claude 두뇌 (이전 단계 맥락 반영해 실제 호출)
        # 기본은 검색 끔 — 답변·요약·판단 노드는 검색이 필요 없는데 WebSearch를 켜두면
        # 모델이 괜히 검색을 시도해 느려지고 간헐적으로 타임아웃 난다. label/detail에
        # 검색 관련 키워드(검색·뉴스·조사…)가 있을 때만 켠다. (뉴스 수집은 보통 web-search
        # tool 노드가 따로 하므로 agent는 대개 검색 불필요.)
        can_search = _needs_search(label, detail)
        allowed = "WebSearch,WebFetch" if can_search else None
        r = claude_call(_agent_prompt(label, detail, history, can_search), allowed_tools=allowed)
        if "error" in r:
            return {"result": "🧠 ⚠ " + r["error"]}  # 실패해도 런은 계속
        return {"result": "🧠 " + _clean(r["text"])}

    if t == "branch":  # 조건 분기 — 앞 내용 보고 유형 판단 → route로 경로 선택
        # detail에 라벨을 '|'로 정의한다. 예: "문의|제안". 엣지의 when이 이 라벨과 매칭.
        routes = [x.strip() for x in (detail or "").split("|") if x.strip()]
        if not routes:  # 라벨 미정의 → 분기 못 함, 그냥 통과(첫 엣지)
            return {"result": "🔀 분기: (라벨 미정의)"}
        r = claude_call(_branch_prompt(label, routes, history), allowed_tools=None)
        if "error" in r:
            # 판단 실패해도 런이 죽지 않게 첫 경로로 폴백
            return {"result": f"🔀 ⚠ 분기 판단 실패 → {routes[0]}", "route": routes[0]}
        route = _parse_route(r["text"], routes)
        return {"result": f"🔀 분류: {route}", "route": route}

    if t == "dedup":  # 하네스: 이미 처리한 건이면 중단 (SQLite 조회)
        key = ctx.get("item_key")
        if key and db.is_processed(key):
            return {
                "result": f"🔁 중복체크: 이미 처리한 건({key}) → 실행 중단",
                "stop": True,
            }
        return {"result": f"🔁 중복체크: 신규 건({key}) → 통과"}

    if t == "verify":  # 하네스: 가드레일
        return {"result": "✅ 검증 통과 — 조건 충족, 다음 단계로"}

    if t == "approve":  # 하네스: human-in-the-loop → 멈춤
        return {"result": "🚨 승인 게이트 — 사용자 확인 대기", "pause": True}

    if t == "tool":  # MCP — 실제 호출
        # mcp_key 우선(프론트가 보내는 카탈로그 key). 없으면 detail·label 순으로 추정한다:
        #  - assemble이 만든 노드는 detail이 카탈로그 key("discord")
        #  - 추천 패널로 추가한 노드는 detail이 "mcp.call"이고 label이 key
        key = _mcp_key(node)

        # ① MCP 서버가 없는 REST API(스마트택배 등) — 실행기가 직접 HTTP. 키는
        #    프롬프트에 안 들어가고 쿼리스트링으로만 나간다(core/api_tools.py).
        if key in api_tools.API_TOOLS:
            # detail이 비어도 앞 단계(메일 읽기)에서 송장번호·택배사를 자동 추출해 조회
            r = api_tools.call_api(key, detail, history)
            if "error" in r:
                return {"result": f"🔌 ⚠ {label}: {r['error']}"}
            return {"result": f"🔌 {label} — {r['text']}"}

        # ② MCP 서버 없이 Claude Code 내장 도구로 되는 것(web-search 등) — 키 불필요.
        if key in mcp.BUILTIN_TOOLS:
            spec = mcp.BUILTIN_TOOLS[key]
            r = claude_call(
                _tool_prompt(label, detail, history, role=spec["role"]),
                allowed_tools=spec["tools"],
            )
            if "error" in r:
                return {"result": "🔌 ⚠ " + r["error"]}
            return {"result": "🔌 " + _clean(r["text"])}

        # ③ 연결된 MCP 서버가 없는 도구는 **시나리오 스텁**이다. CS 데모(cs_demo.py)의
        #    tool 노드가 그 예로, detail에 시나리오 데이터를 담아두고("받은 메일: ...")
        #    그걸 결과로 흘려보내면 다음 agent 노드가 history로 읽어 판단한다.
        #    즉 여기서 mock은 버그가 아니라 데모의 작동 원리라 반드시 유지해야 한다.
        if key not in mcp.MCP_SERVERS:
            return {"result": "🔌 도구 실행: " + label + (f" — {detail}" if detail else "")}

        # ④ MCP 연결 도구 — 키가 있어야 실제 호출. 없으면 가짜로 때우지 않고 명확히 실패.
        with mcp.mcp_config_for(key) as (cfg_path, reason):
            if reason == "no_key":
                need = mcp.missing_fields_hint(key)
                return {"result": f"🔌 ⚠ {label}: 키 미등록 — 노드를 클릭해 {need} 를 넣어주세요"}
            if reason == "stale_format":
                # 키가 분명히 있는데 못 쓰는 경우 — "미등록"이라고 하면 유저가 갇힌다.
                need = mcp.missing_fields_hint(key)
                return {
                    "result": f"🔌 ⚠ {label}: 저장된 키가 예전 형식입니다 — "
                    f"노드를 클릭해 {need} 를 다시 저장해 주세요"
                }
            r = claude_call(
                _tool_prompt(label, detail, history, role=mcp.MCP_SERVERS[key].get("role", "auto")),
                allowed_tools=f"mcp__{key}",  # 이 서버의 도구만 허용
                mcp_config=cfg_path,
            )
        if "error" in r:
            return {"result": "🔌 ⚠ " + r["error"]}  # 실패해도 런은 계속
        return {"result": "🔌 " + _clean(r["text"])}

    if t == "output":  # 처리 완료 기록 → SQLite processed에 저장
        key = ctx.get("item_key")
        if key:
            db.mark_processed(key)
        return {"result": "📤 출력/기록 완료: " + label + " (처리이력 저장)"}

    return {"result": "완료: " + label}
