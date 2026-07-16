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
# env_fields 는 카탈로그 metadata_json.fields 의 name 과 일치해야 한다
# (프론트 키 모달이 그 이름으로 입력칸을 만들고, 여기서 그대로 env 에 넣는다).
MCP_SERVERS: dict[str, dict] = {
    "gmail": {
        "command": "npx",
        "args": ["-y", "@codefuturist/email-mcp"],
        "env_fields": ["MCP_EMAIL_ADDRESS", "MCP_EMAIL_PASSWORD"],
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
        "args": ["-y", "@modelcontextprotocol/server-slack"],
        "env_fields": ["SLACK_BOT_TOKEN", "SLACK_TEAM_ID"],
    },
    "discord": {
        "command": "npx",
        "args": ["-y", "discord-mcp@latest"],
        "env_fields": ["DISCORD_BOT_TOKEN"],
    },
    "telegram": {
        "command": "npx",
        "args": ["-y", "mcp-telegram-agent"],
        "env_fields": ["BOT_TELEGRAM_TOKEN", "BOT_TELEGRAM_CHAT_ID"],
    },
}

# MCP 서버 없이 Claude Code 내장 도구로 처리하는 것들 — **키가 필요 없다.**
# web-search는 원래 Brave API 팀 공용키를 사려 했지만(카탈로그 주석), claude -p 가
# Claude Code CLI라 WebSearch가 내장돼 있어 키 없이 실제 검색이 된다(측정 41초).
BUILTIN_TOOLS: dict[str, str] = {
    "web-search": "WebSearch,WebFetch",
    "fetch": "WebFetch",
}


def _env_for(tool_key: str, spec: dict) -> dict[str, str] | None:
    """저장된 secret → MCP 서버에 넘길 env dict. 필드가 하나라도 비면 None."""
    secret = db.get_credential(tool_key)
    if not secret:
        return None

    fields: list[str] = spec["env_fields"]
    try:
        parsed = json.loads(secret)
    except (json.JSONDecodeError, ValueError):
        parsed = None

    if isinstance(parsed, dict):
        env = {f: str(parsed[f]).strip() for f in fields if str(parsed.get(f, "")).strip()}
    elif len(fields) == 1:
        env = {fields[0]: secret.strip()}  # 평문 단일 키(기존 저장분)
    else:
        return None

    return env if len(env) == len(fields) else None  # 필드 누락 → 못 씀


@contextmanager
def mcp_config_for(tool_key: str):
    """(config_path, reason) 를 내준다. 끝나면 임시 파일을 지운다.

    - 정상       : (경로, None)
    - 미지원 도구 : (None, "unsupported")
    - 키 없음/부족: (None, "no_key")
    """
    spec = MCP_SERVERS.get(tool_key)
    if not spec:
        yield None, "unsupported"
        return

    env = _env_for(tool_key, spec)
    if not env:
        yield None, "no_key"
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
