"""tool_catalog 시드 — 지원 도구(MCP·API) 초기 데이터.

실행: (venv에서, backend 폴더)  python -m app.seed_tools
  - key로 get-or-create (여러 번 돌려도 안전, 이미 있으면 업데이트).
  - CS 데모 도구(Gmail·스마트택배) + 흔한 도구 몇 개.
"""

from sqlalchemy import select

from app.core.db import SessionLocal
from app.models.tool_catalog import ToolCatalog

TOOLS = [
    {
        "key": "gmail",
        "name": "Gmail",
        "type": "mcp",
        "auth_owner": "user",  # 유저 본인이 앱 비밀번호 붙여넣기
        "key_required": True,
        "key_issue_url": "https://myaccount.google.com/apppasswords",
        "description": "메일 읽기·발송 (IMAP+SMTP)",
        # fields의 name = MCP 서버(@codefuturist/email-mcp)에 넘길 환경변수명.
        # IMAP/SMTP 호스트는 상수라 mcp.py의 static_env에 박아둠 — 유저는 2개만 넣는다.
        "metadata_json": {
            "fields": [
                {
                    "name": "MCP_EMAIL_ADDRESS",
                    "placeholder": "you@gmail.com",
                    "help": "메일 주소",
                },
                {
                    "name": "MCP_EMAIL_PASSWORD",
                    "placeholder": "16자리 앱 비밀번호",
                    "help": "2단계 인증 후 앱 비밀번호 생성 (계정 비밀번호 아님)",
                },
            ]
        },
    },
    {
        "key": "sweettracker",
        "name": "스마트택배 (배송조회)",
        "type": "api",
        "auth_owner": "developer",  # 우리 공용키 — 유저는 붙여넣을 게 없음
        "key_required": False,
        "key_issue_url": "https://info.sweettracker.co.kr/apidoc",
        "description": "택배 배송 상태 조회 (한국 택배사)",
        "metadata_json": None,
    },
    {
        "key": "slack",
        "name": "Slack",
        "type": "mcp",
        "auth_owner": "user",
        "key_required": True,
        "key_issue_url": "https://api.slack.com/apps",
        "description": "슬랙 메시지 전송",
        "metadata_json": {
            "field": "SLACK_BOT_TOKEN",
            "help": "봇 토큰 생성 후 붙여넣기",
            "placeholder": "xoxb-...",
        },
    },
    {
        "key": "notion",
        "name": "Notion",
        "type": "mcp",
        "auth_owner": "user",
        "key_required": True,
        "key_issue_url": "https://www.notion.so/my-integrations",
        "description": "노션 페이지 읽기·쓰기",
        "metadata_json": {
            "field": "NOTION_TOKEN",
            "help": "통합(integration) 생성 후 시크릿 붙여넣기",
            "placeholder": "secret_...",
        },
    },
    # ── 추가 수집분 (팀원 카탈로그 조사) ─────────────────
    {
        "key": "google-docs",
        "name": "Google Docs",
        "type": "mcp",
        "auth_owner": "user",
        "key_required": True,
        "key_issue_url": "https://developers.google.com/workspace/guides/configure-mcp-servers",
        "description": "문서 생성/읽기/수정",
        "metadata_json": None,
    },
    {
        "key": "google-sheets",
        "name": "Google Sheets",
        "type": "mcp",
        "auth_owner": "user",
        "key_required": True,
        "key_issue_url": "https://console.cloud.google.com/apis/credentials",
        "description": "스프레드시트 읽기/쓰기",
        "metadata_json": None,
    },
    {
        "key": "google-calendar",
        "name": "Google Calendar",
        "type": "mcp",
        "auth_owner": "user",
        "key_required": True,
        "key_issue_url": "https://developers.google.com/workspace/calendar/api/guides/configure-mcp-server",
        "description": "일정 조회/생성/수정",
        "metadata_json": None,
    },
    {
        "key": "google-drive",
        "name": "Google Drive",
        "type": "mcp",
        "auth_owner": "user",
        "key_required": True,
        "key_issue_url": "https://developers.google.com/workspace/drive/api/guides/configure-mcp-server",
        "description": "파일 검색/읽기/생성",
        "metadata_json": None,
    },
    {
        "key": "discord",
        "name": "Discord",
        "type": "mcp",
        "auth_owner": "developer",  # 봇 토큰 발급(개발자) — 키는 봇 토큰
        "key_required": True,
        "key_issue_url": "https://discord.com/developers/applications",
        "description": "채널 메시지 송수신",
        # fields의 name = MCP 서버에 넘길 환경변수명. local-runner/app/core/mcp.py 의
        # MCP_SERVERS["discord"].env_fields 와 반드시 일치해야 한다.
        "metadata_json": {
            "fields": [
                {
                    "name": "DISCORD_BOT_TOKEN",
                    "placeholder": "봇 토큰",
                    "help": "Developer Portal → Bot → Reset Token. 봇을 서버에 초대해야 전송됩니다.",
                }
            ]
        },
    },
    {
        "key": "telegram",
        "name": "Telegram",
        "type": "mcp",
        "auth_owner": "developer",  # @BotFather 발급 봇 토큰
        "key_required": True,
        "key_issue_url": "https://core.telegram.org/bots#botfather",
        "description": "봇으로 채널·대화방에 메시지 발송",
        # 값이 2개 필요한 도구 — secret 컬럼에 JSON으로 저장된다.
        "metadata_json": {
            "fields": [
                {
                    "name": "BOT_TELEGRAM_TOKEN",
                    "placeholder": "123456789:AA...",
                    "help": "@BotFather 에서 /newbot 으로 발급",
                },
                {
                    "name": "BOT_TELEGRAM_CHAT_ID",
                    "placeholder": "-100... 또는 123456789",
                    "help": "봇과 대화를 먼저 시작해야 chat_id가 생깁니다",
                },
            ]
        },
    },
    {
        "key": "github",
        "name": "GitHub",
        "type": "mcp",
        "auth_owner": "user",
        "key_required": True,
        "key_issue_url": "https://github.com/settings/tokens",
        "description": "저장소·이슈·PR 관리",
        "metadata_json": None,
    },
    {
        "key": "linear",
        "name": "Linear",
        "type": "mcp",
        "auth_owner": "user",
        "key_required": True,  # OAuth
        "key_issue_url": "https://linear.app/docs/mcp",
        "description": "이슈·프로젝트 관리",
        "metadata_json": None,
    },
    {
        "key": "web-search",
        "name": "Web Search",
        "type": "mcp",
        # 원래 Brave API 팀 공용키를 사려 했으나, 실행기가 쓰는 claude -p 는 Claude Code CLI라
        # WebSearch가 내장돼 있다. --allowed-tools 로 열어주면 키 없이 실제 검색이 된다.
        # → 팀 공용키 불필요. (local-runner/app/core/mcp.py 의 BUILTIN_TOOLS)
        "auth_owner": "developer",
        "key_required": False,
        "key_issue_url": None,
        "description": "웹 검색 (키 불필요 — Claude 내장)",
        "metadata_json": None,
    },
    {
        "key": "fetch",
        "name": "Fetch",
        "type": "mcp",
        "auth_owner": "developer",  # 키 불필요(공개)
        "key_required": False,
        "key_issue_url": None,
        "description": "URL 콘텐츠 가져오기·변환",
        "metadata_json": None,
    },
    {
        "key": "atlassian",
        "name": "Atlassian (Jira & Confluence)",
        "type": "mcp",
        "auth_owner": "user",
        "key_required": True,
        "key_issue_url": "https://support.atlassian.com/atlassian-rovo-mcp-server/docs/getting-started-with-the-atlassian-remote-mcp-server/",
        "description": "이슈 트래킹 및 위키 문서 관리",
        "metadata_json": None,
    },
    {
        "key": "kakaowork",
        "name": "카카오워크",
        "type": "api",
        "auth_owner": "developer",  # Bot App Key = 워크스페이스 관리자 발급
        "key_required": True,
        "key_issue_url": "https://docs.kakaoi.ai/kakao_work/botdevguide/",
        "description": "사내 메신저 채팅/알림 봇 연동",
        "metadata_json": None,
    },
    {
        "key": "jandi",
        "name": "잔디 (JANDI)",
        "type": "api",
        "auth_owner": "developer",  # 웹훅 URL = 워크스페이스 관리자 발급
        "key_required": True,
        "key_issue_url": "https://blog.jandi.com/ko/2016/03/02/jandi-connect-webhook/",
        "description": "사내 메신저 웹훅 알림 연동",
        "metadata_json": None,
    },
    {
        "key": "figma",
        "name": "Figma",
        "type": "mcp",
        "auth_owner": "user",
        "key_required": True,
        "key_issue_url": "https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/",
        "description": "디자인 파일 조회/편집",
        "metadata_json": None,
    },
    {
        "key": "zoom",
        "name": "Zoom",
        "type": "mcp",
        "auth_owner": "user",
        "key_required": True,
        "key_issue_url": "https://developers.zoom.us/docs/mcp/",
        "description": "회의 생성 및 녹화 요약 조회",
        "metadata_json": None,
    },
    {
        "key": "microsoft-365",
        "name": "Microsoft 365 (Outlook)",
        "type": "mcp",
        "auth_owner": "user",
        "key_required": True,
        "key_issue_url": "https://learn.microsoft.com/en-us/graph/mcp-server/overview",
        "description": "메일·캘린더·연락처 관리 (Graph API)",
        "metadata_json": None,
    },
]


def seed() -> None:
    db = SessionLocal()
    try:
        for data in TOOLS:
            tool = db.scalar(select(ToolCatalog).where(ToolCatalog.key == data["key"]))
            if tool is None:
                db.add(ToolCatalog(**data))
                print(f"  + 추가: {data['key']}")
            else:
                for k, v in data.items():
                    setattr(tool, k, v)
                print(f"  ~ 갱신: {data['key']}")
        db.commit()
        print(f"✅ tool_catalog 시드 완료 ({len(TOOLS)}개)")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
