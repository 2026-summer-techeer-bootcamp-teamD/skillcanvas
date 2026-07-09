"""노드 타입별 실행 + 하네스 중복체크(processed). PoC execNode 이식.

반환: {"result": str, "pause"?: bool, "stop"?: bool}
  - pause: 승인 게이트 → 실행 멈춤(awaiting_approval)
  - stop: 중복 등으로 실행 중단(stopped)

중복체크(processed)는 SQLite(core/db.py)에 저장 → 서버 재시작에도 유지.
"""

from app.core import db
from app.core.claude import claude_call


def _first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()[:120]
    return ""


def exec_node(node: dict, ctx: dict) -> dict:
    t = node.get("type")
    label = node.get("label", "")
    detail = node.get("detail", "")

    if t == "trigger":
        return {"result": "⏱ 트리거 발동 — 실행 시작"}

    if t in ("agent", "ai"):  # 에이전트 = Claude 두뇌 (실제 claude 호출)
        r = claude_call(
            f'너는 워크플로우의 에이전트 단계다. 단계: "{label}" ({detail}). '
            "수행 결과를 한국어 한 줄로만. 서론 없이 결과만."
        )
        if "error" in r:
            return {"result": "🧠 ⚠ " + r["error"]}  # 실패해도 런은 계속
        return {"result": "🧠 " + _first_line(r["text"])}

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
