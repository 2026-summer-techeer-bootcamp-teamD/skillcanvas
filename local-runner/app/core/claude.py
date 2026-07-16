"""로컬 Claude CLI 호출 래퍼 — agent 노드가 `claude -p`로 판단/생성.

PoC의 execFile('claude', ['-p', prompt]) 이식.
claude 미설치·타임아웃·실패해도 **예외를 던지지 않고** {"text": ...} 또는
{"error": ...} 를 돌려준다 → 워크플로우 실행이 중간에 죽지 않게.
"""

import subprocess


def claude_call(
    prompt: str,
    timeout: int = 180,
    allowed_tools: str | None = None,
    mcp_config: str | None = None,
) -> dict:
    """allowed_tools: `claude -p`에 넘길 도구 허용 목록(쉼표 구분, 예: "WebSearch,WebFetch").

    없으면 도구 없이 텍스트만 생성한다 → 최신 정보가 필요한 단계는 사실을 지어내거나
    "데이터가 없다"고 거절한다. 실제 뉴스·검색이 필요한 노드는 반드시 넘길 것.
    timeout이 180인 이유: WebSearch가 붙으면 검색+본문읽기로 30초 이상 걸린다(측정 41초).

    mcp_config: core/mcp.py 가 만든 임시 MCP 설정 파일 경로. --strict-mcp-config 를 같이
    붙여서 **이 파일의 서버만** 쓰게 한다(사용자 개인 ~/.claude 설정이 섞여 데모가
    예측 불가능해지는 걸 막는다).
    """
    cmd = ["claude", "-p", prompt]
    if allowed_tools:
        cmd += ["--allowed-tools", allowed_tools]
    if mcp_config:
        cmd += ["--mcp-config", mcp_config, "--strict-mcp-config"]
    try:
        proc = subprocess.run(
            cmd,
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
