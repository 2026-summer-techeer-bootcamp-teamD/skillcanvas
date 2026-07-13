# SkillCanvas 프로젝트 가이드

이 문서는 Claude가 이 레포지토리에서 작업할 때 지켜야 할 컨텍스트와 규칙을 정의합니다.

## 1. 프로젝트 개요
- **설명**: 말로 만드는 AI 업무 비서 빌더 (SkillCanvas)
- **구조**: 모노레포 (`backend/`, `frontend/`, `docs/`, `local-runner/`)
- **기술 스택**: FastAPI, SQLAlchemy, PostgreSQL, Python 3.12, React, TypeScript, React Flow

## 2. API 개발 시 필수 참고 파일 (컨텍스트 로드용)
API를 설계, 구현, 수정할 때는 반드시 아래 문서들의 규칙과 스키마를 최우선으로 확인해야 합니다.

- **컨벤션 및 규칙**: `docs/SkillCanvas_컨벤션.md`
  - *중요*: FastAPI 라우터 작성 시 **엔드포인트 한글 summary 및 tag 규칙**을 반드시 준수할 것.
- **레포 구조 가이드**: `docs/레포구조.md` (백엔드 API 개발 위치 및 폴더 구조 규칙)
- **기능 및 API 명세**: 
  - `docs/SkillCanvas_API명세서.md` (엔드포인트 상세)
  - `docs/SkillCanvas_기능명세서.md` (데이터/API 관점 명세)
  - `docs/SkillCanvas_기능명세서_상세.md` (화면 관점 명세)
- **데이터베이스 모델**: `docs/SkillCanvas_ERD.md` 및 `backend/app/models/` 내의 SQLAlchemy 엔티티 파일들

## 3. 개발 명령어 및 가이드
- **DB (Postgres) 실행**: `docker compose up`
- **백엔드 서버 실행**: `cd backend && uvicorn app.main:app --reload` (기본 주소: localhost:8000/docs)
- **프론트엔드 실행**: `cd frontend && npm install && npm run dev`
- **모니터링 실행**: `docker compose --profile monitoring up` → Prometheus(localhost:9090) + Grafana(localhost:3000, admin/admin). 백엔드는 `/metrics`에서 지표 노출 (venv로 띄운 백엔드 기준으로 스크랩 설정됨).
- **코드 스타일 및 린트**: GitHub Actions CI 통과를 위해 `ruff` 및 `black` 규칙을 준수하여 작성할 것.

## 4. Claude 행동 지침
- 새로운 API 엔드포인트나 비즈니스 로직 구현 요청을 받으면, 먼저 관련 `docs/` 내 명세서들을 읽고 요구사항을 파악하세요.
- 코드를 제안하거나 수정할 때는 `docs/SkillCanvas_컨벤션.md`에 정의된 린트 가이드와 Swagger 한글화 규칙에 어긋나지 않는지 스스로 검증한 뒤 결과를 출력하세요.


## 5. api 개발 전에는 깃허브 이슈 만들기 (보통 1~3번만 작성)
- 1. 기능 요약(제안하는 기능을 한 문장으로 설명해 주세요.)

- 2. 배경 / 동기(이 기능이 필요한 이유나 해결하려는 문제를 설명해 주세요.)

- 3. 제안 내용(기능의 동작 방식이나 구현 방향을 구체적으로 설명해 주세요.)

- 4. 대안(고려해 본 다른 방법이 있다면 설명해 주세요.)

- 5. 추가 정보(참고 자료, 스크린샷, 관련 이슈 등을 자유롭게 첨부해 주세요.)


## 6. 깃허브 pull request 내용

1. 작업 내용
예: 내 프로필 조회 기능 추가했습니다. (+users.py, main.py 코드 추가)

2. 변경 사항
- [O ] 기능 추가
- [ ] 버그 수정
- [ ] 리팩토링
- [ ] 테스트 추가 / 수정
- [ ] 문서 수정
- [ ] 기타 (설명: )

3. 구현 방법 / 주요 변경 포인트
핵심 로직이나 설계 결정 사항을 설명해 주세요.

4. 테스트 방법
변경 사항을 검증하는 방법을 작성해 주세요.
환경 설정:
실행 방법:
확인 사항:

5. 스크린샷 (선택)
UI 변경이 있는 경우 전/후 스크린샷을 첨부해 주세요.

6. 리뷰어에게 전달 사항
리뷰어가 특히 집중해서 봐줬으면 하는 부분이나 논의가 필요한 부분을 작성해 주세요.

7.  셀프 체크리스트
- [ ] 코드 컨벤션을 준수했나요?
- [ ] 불필요한 주석/로그를 제거했나요?
- [ ] 테스트를 작성/업데이트했나요?
- [ ] PR 제목이 명확한가요? (예: `[FEAT] 로그인 기능 구현`)

