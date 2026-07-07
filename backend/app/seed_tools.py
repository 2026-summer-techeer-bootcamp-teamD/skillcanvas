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
        "description": "메일 읽기·발송",
        "metadata_json": {
            "field": "GMAIL_APP_PASSWORD",
            "help": "2단계 인증 후 앱 비밀번호 생성",
            "placeholder": "16자리 앱 비밀번호",
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
