"""노드 타입별 실행 + 하네스 중복체크(processed). PoC execNode 이식.

반환: {"result": str, "pause"?: bool, "stop"?: bool}
  - pause: 승인 게이트 → 실행 멈춤(awaiting_approval)
  - stop: 중복 등으로 실행 중단(stopped)

중복체크(processed)는 SQLite(core/db.py)에 저장 → 서버 재시작에도 유지.
"""

from app.core import db
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


def _clean(text: str) -> str:
    """claude 응답에서 메타 서두 줄을 걸러 실제 결과 줄만 뽑는다."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in lines:
        if not any(h in ln for h in _META_HINTS):
            return ln[:200]
    return lines[-1][:200] if lines else ""


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
        "- 한국어 1~2문장, 결과 텍스트만."
    )


def exec_node(node: dict, ctx: dict, history: list[dict] | None = None) -> dict:
    t = node.get("type")
    label = node.get("label", "")
    detail = node.get("detail", "")

    if t == "trigger":
        return {"result": "⏱ 트리거 발동 — 실행 시작"}

    if t in ("agent", "ai"):  # 에이전트 = Claude 두뇌 (이전 단계 맥락 반영해 실제 호출)
        r = claude_call(_agent_prompt(label, detail, history))
        if "error" in r:
            return {"result": "🧠 ⚠ " + r["error"]}  # 실패해도 런은 계속
        return {"result": "🧠 " + _clean(r["text"])}

    if t == "dedup":  # 하네스: 이미 처리한 건이면 중단 (SQLite 조회)
        key = ctx.get("item_key")
        if key and db.is_processed(key):
            return {"result": f"🔁 중복체크: 이미 처리한 건({key}) → 실행 중단", "stop": True}
        return {"result": f"🔁 중복체크: 신규 건({key}) → 통과"}

    if t == "verify":  # 하네스: 가드레일
        return {"result": "✅ 검증 통과 — 조건 충족, 다음 단계로"}

    if t == "approve":  # 하네스: human-in-the-loop → 멈춤
        return {"result": "🚨 승인 게이트 — 사용자 확인 대기", "pause": True}

    if t == "tool":  # MCP (데모는 모의)
        return {"result": "🔌 도구 실행: " + label + (f" — {detail}" if detail else "")}

    if t == "output":  # 처리 완료 기록 → SQLite processed에 저장
        key = ctx.get("item_key")
        if key:
            db.mark_processed(key)
        return {"result": "📤 출력/기록 완료: " + label + " (처리이력 저장)"}

    return {"result": "완료: " + label}
