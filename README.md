# SkillCanvas (가제: oh my skill)

> 말로 만드는 AI 업무 비서 빌더 — 내가 커스텀한 Claude 스킬을 부품처럼 쌓아 워크플로우로 조립하고, 갤러리로 공유.

**팀원은 [`온보딩.md`](./온보딩.md) 먼저 읽으세요.**

## 구조 (모노레포)

```
skillcanvas/
├── frontend/       React + TypeScript + React Flow (→ Vercel)
├── backend/        FastAPI 갤러리 API (→ EC2 Docker)
├── local-runner/   로컬 실행기 (팀장 · 나중에)
├── docs/           기획·설계 문서 (PRD·ERD·API명세서·컨벤션 등)
└── docker-compose.yml   로컬 Postgres
```

## 기술 스택

- **프론트**: React + TS + React Flow → Vercel
- **인증**: Clerk
- **백엔드**: FastAPI + Uvicorn (Python 3.12) → EC2 + Docker + Nginx
- **DB**: PostgreSQL (로컬=Docker, 배포=AWS RDS) + SQLAlchemy + Alembic
- **CI**: GitHub Actions (ruff·black 린트)

## 빠른 실행 (개발)

```bash
docker compose up                 # Postgres 켜기
cd backend && uvicorn app.main:app --reload   # (venv에서) 백엔드 → localhost:8000/docs
cd frontend && npm install && npm run dev     # 프론트 → localhost:5173
```

## 문서

| 문서 | 내용 |
|------|------|
| `docs/SkillCanvas_팀브리핑.md` | 프로젝트 전체 온보딩 |
| `docs/SkillCanvas_API명세서.md` | API 엔드포인트 상세 |
| `docs/SkillCanvas_ERD.md` | DB 설계 (✅ 확정 — 모델·마이그레이션 반영됨) |
| `docs/SkillCanvas_기능명세서_상세.md` | 화면·기능 명세 |
| `docs/SkillCanvas_컨벤션.md` | 코드·API 규칙 (**필독**) |
| `docs/SkillCanvas_빌드플랜.md` | 일정·태스크 |

## 진행 상태

- ✅ 인프라 스캐폴드 (구조·docker·health check·CI)
- ✅ **DB 모델 7개 + 마이그레이션 + tool_catalog 시드** (`backend/app/models/`, `app/seed_tools.py`)
- ✅ **예시 엔드포인트** — `app/routers/workflows.py` (6개, 팀원 복제용 템플릿)
- ⬜ 나머지 API (users·skills·tags·tool_catalog·assemble) — workflows 복제해서
- ⬜ Clerk 인증 실연동 (`app/core/deps.py`의 STUB → 실제 JWT 검증)
- ⬜ 프론트 캔버스·갤러리 UI
- ⬜ 로컬 실행기 (팀장)
