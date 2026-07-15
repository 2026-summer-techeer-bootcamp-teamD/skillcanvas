# 로컬 실행기 (Local Runner)

> **팀장 담당.** 사용자 PC에서 도는 작은 FastAPI 프로그램 (`localhost:4737`, 인증 없음).
> 웹 프론트가 이 러너를 호출해 **워크플로우 실행 / 로컬 `.claude` 동기화 / 키 저장**을 한다.

## 하는 일
- `.claude` 파싱/직렬화 (양방향 동기화) — `GET /graph`, `POST /save`
- 워크플로우 실행 엔진 (중단/재개·🚨승인게이트) — `POST /run`, `/run/{id}/approve`, `/run/{id}/status`
- 도구 키 로컬 저장 — `POST /credential`
- agent 노드는 **로컬 `claude -p` CLI**로 판단/생성 (아래 의존성 참고)

## ⚠️ 의존성: Claude CLI (각자 본인 것)
- agent 노드는 `subprocess`로 **`claude -p <prompt>`**를 호출한다 (`app/core/claude.py`).
- 그래서 **각자 자기 PC에 Claude Code CLI 설치 + 로그인(Max)**돼 있어야 agent 노드가 실제로 동작한다.
- 미설치여도 러너는 안 죽고, agent 노드가 `{"error": "claude CLI를 찾을 수 없습니다"}`를 반환한다.
- **이 러너는 각자 로컬 것** — 팀장 env를 공유하는 게 아니다.

## 세팅 & 실행
```bash
cd local-runner
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --port 4737 --reload
```
- 확인: `curl http://localhost:4737/health` → `{"status":"ok"}`
- 프론트(5173)에서 실행/로컬저장/불러오기 버튼이 이 러너를 호출한다. (프론트만 개발하면 안 켜도 됨 — 실행 기능 테스트할 때만 필요)

## 환경변수 (선택)
| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `RUNNER_BASE_DIR` | (sandbox) | `~` 로 지정하면 **내 진짜 홈 `.claude`**를 다룬다. 기본은 `sandbox/`(샘플). |
| `RUNNER_CORS_ORIGINS` | `localhost:5173,3000` + `skillcanvas.store`(+www) | 기본값에 배포 도메인 포함 → 그냥 uvicorn만. 다른 배포처는 이 env로 대체. |

> 기본은 **`sandbox/.claude`(샘플 스킬: meeting-notes 등)**를 다룬다. 내 실제 스킬로 하려면 `RUNNER_BASE_DIR=~`.

## 참고
- 상세: `../docs/SkillCanvas_시스템정리.md`, `../docs/SkillCanvas_기능명세서.md`(부록)
- API 명세: `../docs/SkillCanvas_API명세서.md` (부록 A-1~A-6)
