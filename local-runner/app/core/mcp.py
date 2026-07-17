"""MCP 서버 레지스트리 + 실행용 임시 설정 생성.

왜 sandbox/.mcp.json 을 안 쓰고 임시 파일을 만드나:
  봇 토큰 같은 키를 정적 .mcp.json 에 적으면 커밋 시 그대로 유출된다.
  그래서 실행 시점에 SQLite(credentials)에서 키를 읽어 **임시 설정 파일**을 만들고
  `claude -p --mcp-config <임시파일>` 로 넘긴 뒤 즉시 지운다(파일 권한 0600).

키 저장 형식(secret 컬럼)은 두 가지를 지원한다:
  - JSON 객체  : {"BOT_TELEGRAM_TOKEN": "...", "BOT_TELEGRAM_CHAT_ID": "..."}  ← 값 여러 개
  - 평문 문자열: 필드가 1개인 도구의 단일 키                                    ← 기존 저장분 호환
"""

import json
import os
import tempfile
from contextlib import contextmanager

from app.core import db

# 카탈로그 key → MCP 서버 실행 방법.
# ⚠️ 버전을 반드시 핀한다. npx는 버전을 안 쓰면 latest를 받아오므로, 데모 당일 upstream이
#    breaking change를 내면 그대로 터진다(우리 코드는 그대로인데 재현이 안 되는 최악의 형태).
#    올릴 땐 의도적으로 올리고 실제로 돌려본 뒤 커밋할 것.
# env_fields 는 카탈로그 metadata_json.fields 의 name 과 일치해야 한다
# (프론트 키 모달이 그 이름으로 입력칸을 만들고, 여기서 그대로 env 에 넣는다).
MCP_SERVERS: dict[str, dict] = {
    "gmail": {
        "command": "npx",
        "args": ["-y", "@codefuturist/email-mcp@0.2.3"],
        "env_fields": ["MCP_EMAIL_ADDRESS", "MCP_EMAIL_PASSWORD"],
        # 읽기(IMAP)·발송(SMTP) 둘 다 하는 도구 — 노드 라벨을 보고 판단하게 한다
        "role": "auto",
        # 호스트는 키가 아니라 상수다 — 유저에게 물을 이유가 없어서 여기 박는다.
        # IMAP+SMTP 둘 다 되는 서버라 CS 시나리오의 '컴플레인 읽기'와 '사과메일 발송'을
        # 하나로 커버한다.
        "static_env": {
            "MCP_EMAIL_IMAP_HOST": "imap.gmail.com",
            "MCP_EMAIL_SMTP_HOST": "smtp.gmail.com",
        },
    },
    "slack": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-slack@2025.4.25"],
        "env_fields": ["SLACK_BOT_TOKEN", "SLACK_TEAM_ID"],
        "role": "send",
    },
    "discord": {
        "command": "npx",
        "args": ["-y", "discord-mcp@2.4.0"],
        "env_fields": ["DISCORD_BOT_TOKEN"],
        "role": "send",
    },
    "telegram": {
        "command": "npx",
        "args": ["-y", "mcp-telegram-agent@0.6.1"],
        "env_fields": ["BOT_TELEGRAM_TOKEN", "BOT_TELEGRAM_CHAT_ID"],
        "role": "send",
    },
    "notion": {
        "command": "npx",
        # 공식 서버. Option 1(NOTION_TOKEN 단일 토큰) 지원 — 헤더 JSON(OPENAPI_MCP_HEADERS)
        # 없이 토큰 하나면 된다. 통합(integration) 시크릿은 ntn_ 로 시작.
        "args": ["-y", "@notionhq/notion-mcp-server@2.4.1"],
        "env_fields": ["NOTION_TOKEN"],
        # 제안 요약을 노션에 '정리해 기록'하는 용도 — 발송 계열
        "role": "send",
    },
}

# MCP 서버 없이 Claude Code 내장 도구로 처리하는 것들 — **키가 필요 없다.**
# web-search는 원래 Brave API 팀 공용키를 사려 했지만(카탈로그 주석), claude -p 가
# Claude Code CLI라 WebSearch가 내장돼 있어 키 없이 실제 검색이 된다(측정 41초).
# role: 프롬프트를 발송용/수집용 중 뭘로 줄지 결정한다(engine/nodes.py의 _tool_prompt).
# 둘 다 **수집** 도구다 — 발송 전제로 프롬프트를 주면 AI가 "왜 안 보냈는지"를 해명한다.
BUILTIN_TOOLS: dict[str, dict] = {
    "web-search": {"tools": "WebSearch,WebFetch", "role": "fetch"},
    "fetch": {"tools": "WebFetch", "role": "fetch"},
}


def _env_for(tool_key: str, spec: dict) -> tuple[dict[str, str] | None, str | None]:
    """저장된 secret → (env dict, 실패사유).

    실패사유를 구분하는 이유: 값이 여러 개인 도구(gmail 등)를 예전 단일 필드 시절에
    평문으로 저장해 뒀다면, 키가 분명히 있는데도 못 쓴다. 그때 "키 미등록"이라고만 하면
    이미 넣은 유저가 왜 안 되는지 알 수 없다 → "다시 저장해 주세요"로 안내한다.
    """
    secret = db.get_credential(tool_key)
    if not secret:
        return None, "no_key"

    fields: list[str] = spec["env_fields"]
    try:
        parsed = json.loads(secret)
    except (json.JSONDecodeError, ValueError):
        parsed = None

    if isinstance(parsed, dict):
        env = {f: str(parsed[f]).strip() for f in fields if str(parsed.get(f, "")).strip()}
        # JSON인데 필드가 빈다 = 저장 당시와 요구 필드가 달라진 것
        return (env, None) if len(env) == len(fields) else (None, "stale_format")
    if len(fields) == 1:
        v = secret.strip()
        return ({fields[0]: v}, None) if v else (None, "no_key")
    # 필드가 여러 개인데 평문 한 덩어리 = 단일 필드 시절에 저장된 값
    return None, "stale_format"


@contextmanager
def mcp_config_for(tool_key: str):
    """(config_path, reason) 를 내준다. 끝나면 임시 파일을 지운다.

    - 정상        : (경로, None)
    - 미지원 도구  : (None, "unsupported")
    - 키 없음      : (None, "no_key")
    - 옛 형식으로 저장 : (None, "stale_format")  ← 키는 있는데 못 씀. 다시 저장해야 함
    """
    spec = MCP_SERVERS.get(tool_key)
    if not spec:
        yield None, "unsupported"
        return

    env, reason = _env_for(tool_key, spec)
    if not env:
        yield None, reason
        return

    env = {**spec.get("static_env", {}), **env}  # 상수 호스트 등 + 유저 키
    cfg = {"mcpServers": {tool_key: {"command": spec["command"], "args": spec["args"], "env": env}}}
    fd, path = tempfile.mkstemp(prefix=f"mcp-{tool_key}-", suffix=".json")
    try:
        os.chmod(path, 0o600)  # 토큰이 들어있다 — 본인만 읽게
        with os.fdopen(fd, "w") as f:
            json.dump(cfg, f)
        yield path, None
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def missing_fields_hint(tool_key: str) -> str:
    """키 미등록 안내에 붙일 '필요한 값' 문구."""
    spec = MCP_SERVERS.get(tool_key)
    return ", ".join(spec["env_fields"]) if spec else ""
