"""로컬 실행기 경로 설정.

개발 중엔 sandbox/(연습용 가짜 .claude)를 본다. 나중에 실제 사용자
홈의 ~/.claude 로 바꾸려면 BASE_DIR 한 곳만 고치면 된다.
"""

from pathlib import Path

# local-runner/ 폴더 (이 파일 기준 두 단계 위: app/core/ → app/ → local-runner/)
RUNNER_ROOT = Path(__file__).resolve().parents[2]

# 개발용 작업 폴더. (실서비스에선 Path.home() 로 교체)
BASE_DIR = RUNNER_ROOT / "sandbox"

CLAUDE_DIR = BASE_DIR / ".claude"
SKILLS_DIR = CLAUDE_DIR / "skills"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"
MCP_FILE = BASE_DIR / ".mcp.json"

# 로컬 실행기 상태 저장용 SQLite (재시작에도 남아야 하는 것 — 중복체크 등). gitignore됨(*.db)
DB_FILE = BASE_DIR / "runner.db"
