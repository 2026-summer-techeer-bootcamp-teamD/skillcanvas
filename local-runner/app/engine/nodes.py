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


def _agent_prompt(label: str, detail: str, history: list[dict] | None) -> str:
    """이전 단계 결과를 맥락으로 넣어, agent가 흐름을 반영해 판단/생성하게 한다."""
    steps = "\n".join(f"- {h['label']}: {h['result']}" for h in history) if history else ""
    return (
        "너는 업무 자동화 워크플로우의 한 단계를 수행하는 에이전트다.\n"
        f"[지금까지 진행된 단계와 결과]\n{steps or '(이전 단계 없음)'}\n\n"
        f"[이번 단계] {label} ({detail})\n\n"
        "규칙:\n"
        "- 위 맥락을 반영해 '이번 단계의 최종 결과물' 자체만 출력한다.\n"
        "- 인사말·상황설명·'~단계군요'·'~하겠습니다' 같은 메타 발언 절대 금지.\n"
        "- 예를 들어 '사과문 생성'이면 사과문 문장 자체를, '긴급도 판단'이면 판단 결과를 바로 쓴다.\n"
        "- 최신 정보·뉴스·외부 사실이 필요하면 WebSearch/WebFetch로 직접 찾아서 쓴다. "
        "절대 지어내지 말고, 못 찾으면 못 찾았다고 쓴다.\n"
        "- 이전 단계의 '🔌 도구 실행' 줄은 실제 데이터가 아니라 실행 기록일 뿐이다. "
        "거기서 데이터를 기대하지 말고 필요하면 직접 검색해라.\n"
        "- 한국어, 결과 텍스트만. 요약·목록이면 불릿 5개 이내, 그 외엔 3문장 이내."
    )


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


def _tool_prompt(label: str, detail: str, history: list[dict] | None) -> str:
    """도구 노드용 — 앞 단계 **결과물**을 실제로 전송시킨다.

    '바로 앞 단계'를 쓰라고 하면 안 된다. 승인 게이트 뒤에 발송 노드가 오는 그래프(CS
    시나리오)에서 바로 앞은 "🚨 승인 게이트 — 사용자 확인 대기"라, 사과문 대신 그 문구를
    메일로 보내버린다. 하네스 줄(🚨/🔁/✅/⏱)과 실제 결과물(🧠)을 구분해서 알려준다.
    """
    steps = "\n".join(f"- {h['label']}: {h['result']}" for h in history) if history else ""
    return (
        f"너는 업무 자동화 워크플로우의 '{label}' 도구 단계다. "
        f"연결된 {label} 도구를 실제로 호출해 작업을 수행하라.\n"
        f"[지금까지 진행된 단계와 결과]\n{steps or '(이전 단계 없음)'}\n\n"
        f"[이번 단계] {label} ({detail})\n\n"
        "규칙:\n"
        "- 전송할 내용은 앞 단계들이 만든 **결과물**(사과문·요약문 등, 보통 🧠 로 시작)이다. "
        "여러 개면 이번 단계 목적에 맞는 것을 고른다. 내용을 새로 지어내지 마라.\n"
        "- ⏱ 트리거 / 🚨 승인 게이트 / 🔁 중복체크 / ✅ 검증 줄은 워크플로우 내부 실행 기록이다. "
        "**절대 전송 내용으로 쓰지 마라.**\n"
        "- 결과물 앞의 이모지 접두사(🧠 🔌 등)는 내부 표시이므로 빼고 보낸다.\n"
        "- 도구를 실제로 호출하라. 호출한 척하고 보고만 하지 마라.\n"
        "- 끝나면 무엇을 어디로 보냈는지 한국어 1문장으로만 보고한다."
    )


def exec_node(node: dict, ctx: dict, history: list[dict] | None = None) -> dict:
    t = node.get("type")
    label = node.get("label", "")
    detail = node.get("detail", "")

    if t == "trigger":
        return {"result": "⏱ 트리거 발동 — 실행 시작"}

    if t in ("agent", "ai"):  # 에이전트 = Claude 두뇌 (이전 단계 맥락 반영해 실제 호출)
        # WebSearch/WebFetch 허용 — 이게 없으면 최신 정보가 필요한 단계에서 모델이
        # 사실을 지어내거나 "데이터가 없다"고 거절한다(둘 다 쓸모없음).
        r = claude_call(_agent_prompt(label, detail, history), allowed_tools="WebSearch,WebFetch")
        if "error" in r:
            return {"result": "🧠 ⚠ " + r["error"]}  # 실패해도 런은 계속
        return {"result": "🧠 " + _clean(r["text"])}

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
            r = api_tools.call_api(key, detail)
            if "error" in r:
                return {"result": f"🔌 ⚠ {label}: {r['error']}"}
            return {"result": f"🔌 {label} — {r['text']}"}

        # ② MCP 서버 없이 Claude Code 내장 도구로 되는 것(web-search 등) — 키 불필요.
        if key in mcp.BUILTIN_TOOLS:
            r = claude_call(
                _tool_prompt(label, detail, history),
                allowed_tools=mcp.BUILTIN_TOOLS[key],
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
            r = claude_call(
                _tool_prompt(label, detail, history),
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
