"""로컬 실행기 경로·CORS 설정.

기본은 sandbox/(연습용 가짜 .claude) — 안전. 실제 사용자 ~/.claude 를 다루려면
환경변수 RUNNER_BASE_DIR="~" 로 지정(명시적 opt-in). CORS 도메인도 env로 확장.
"""

import os
from pathlib import Path

# local-runner/ 폴더 (이 파일 기준 두 단계 위: app/core/ → app/ → local-runner/)
RUNNER_ROOT = Path(__file__).resolve().parents[2]

# CORS 허용 오리진 — 웹 프론트가 이 로컬 실행기(localhost)를 호출할 수 있게 열어준다.
# 기본은 로컬 개발용. 배포 시 RUNNER_CORS_ORIGINS 환경변수로 Vercel 도메인 추가.
#   예) RUNNER_CORS_ORIGINS="http://localhost:5173,https://skillcanvas.vercel.app"
_DEFAULT_CORS = ["http://localhost:5173", "http://localhost:3000"]
# 빈 값("")으로 설정하면 파싱 결과가 []가 되어 전면 차단됨 → 그 경우 기본값으로 폴백
CORS_ORIGINS = [
    o.strip() for o in os.getenv("RUNNER_CORS_ORIGINS", "").split(",") if o.strip()
] or _DEFAULT_CORS

# 로컬 실행기가 다룰 작업 폴더(그 안의 .claude/.mcp.json을 읽고 쓴다).
# 기본은 sandbox(안전한 연습용) — 안 그러면 개발 중 실수로 진짜 .claude를 수정할 수 있음.
# 실제 내 스킬을 다루려면 RUNNER_BASE_DIR에 .claude가 있는 폴더(보통 홈)를 지정:
#   실사용:  RUNNER_BASE_DIR="~"  → ~/.claude 를 다룸
_base = os.getenv("RUNNER_BASE_DIR")
BASE_DIR = Path(_base).expanduser().resolve() if _base else RUNNER_ROOT / "sandbox"

CLAUDE_DIR = BASE_DIR / ".claude"
SKILLS_DIR = CLAUDE_DIR / "skills"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"
MCP_FILE = BASE_DIR / ".mcp.json"

# 로컬 실행기 상태 저장용 SQLite (재시작에도 남아야 하는 것 — 중복체크 등). gitignore됨(*.db)
DB_FILE = BASE_DIR / "runner.db"
