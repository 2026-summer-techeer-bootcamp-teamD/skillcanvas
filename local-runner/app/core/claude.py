"""로컬 Claude CLI 호출 래퍼 — agent 노드가 `claude -p`로 판단/생성.

PoC의 execFile('claude', ['-p', prompt]) 이식.
claude 미설치·타임아웃·실패해도 **예외를 던지지 않고** {"text": ...} 또는
{"error": ...} 를 돌려준다 → 워크플로우 실행이 중간에 죽지 않게.
"""

import subprocess


def claude_call(prompt: str, timeout: int = 60) -> dict:
    try:
        proc = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return {"error": "claude CLI를 찾을 수 없습니다(미설치)"}
    except subprocess.TimeoutExpired:
        return {"error": "claude 호출 시간 초과"}

    if proc.returncode != 0:
        return {"error": "claude 호출 실패: " + proc.stderr.strip()[:200]}
    return {"text": proc.stdout}
