# 📋 SkillCanvas — 기능 명세서

> **제품**: 말로 만드는 AI 업무 비서 빌더 (범용). 발표 데모 = CS 신입.
> **구조**: **[본문] 서버 API 개발** (주니어+팀장 서버파트, API 명세 나옴) / **[부록] 엔진·로컬 개발** (팀장, 로컬 실행기 내부).
> **개발구분**: 🟦서버API · 🟩엔진/로컬 · ⬜프론트

*(작성일 2026-07-06)*

---

## 개발 구분 원칙

- **생성·조립·추천·갤러리 = 서버 API** (백엔드 FastAPI, Claude API·DB) → [본문]
- **파일·실행·하네스 = 엔진/로컬** (로컬 실행기, .claude·SQLite·Claude CLI) → [부록]

---

# 【본문】 서버 API 개발

## 1. 계정 / 인증

| 기능 | 설명 | 구분 | 우선 | 관련 데이터 |
|------|------|:---:|:---:|------|
| 회원가입/로그인 | Clerk로 처리 (우린 토큰 검증만) | 🟦 | P1 | users |
| 프로필 | 닉네임 (아바타 X) | 🟦 | P2 | users |
| 로컬 실행기 다운로드 | 사이트에서 설치파일 제공 | 🟦 | P1 | — |

## 2. MCP 카탈로그 (지원 도구 레지스트리)

| 기능 | 설명 | 구분 | 우선 | 관련 데이터 |
|------|------|:---:|:---:|------|
| 카탈로그 조회 | 지원 MCP 목록 + 키 메타데이터 반환 | 🟦 | P1 | tool_catalog |
| 카탈로그 관리 | MCP 추가/수정 (운영) | 🟦 | P2 | tool_catalog |

## 3. 자연어 조립 / 추천 (백엔드가 Claude API 호출)

| 기능 | 설명 | 구분 | 우선 | 관련 데이터 |
|------|------|:---:|:---:|------|
| 자연어→워크플로우 생성 | NL → 그래프 JSON (카탈로그 안에서만·검증). **조건 분기(branch)·`when` 엣지 생성** 포함 | 🟦 | P1 | tool_catalog |
| 자연어→스킬 생성 | NL → 스킬 초안 | 🟦 | P1 | tool_catalog |
| MCP 추천 | "이거 하고싶어" → 붙일 MCP 제안 | 🟦 | P1 | tool_catalog |
| 노드 자연어 편집/매핑 | 노드를 말로 수정 → 재매핑 (AutoFlow "노드 바꾸기") | 🟦 | P1 | — |

## 4. 갤러리 (공유·재사용)

| 기능 | 설명 | 구분 | 우선 | 관련 데이터 |
|------|------|:---:|:---:|------|
| 워크플로우/스킬 발행 | 그래프JSON/스킬 + 제목·설명 올림 | 🟦 | P1 | workflows, skills |
| 목록 조회 | 카드로 보기 (인기순=가져가기수) | 🟦 | P1 | workflows, skills |
| 태그 분류 | 태그로 묶어 보기 | 🟦 | P2 | tags, *_tags(M:N) |
| 가져가기 수 | 가져올 때 +1 (카운터) | 🟦 | P2 | workflows.import_count |
| 가져오기 | 남의 그래프JSON을 내 캔버스로 | 🟦 | P1 | workflows |
| ~~검색~~ / ~~좋아요~~ | 제외 (좋아요→가져가기수로 대체) | — | — | — |

---

# 【부록】 엔진 · 로컬 개발 (팀장 · 로컬 실행기)

> 로컬 실행기(FastAPI, 사용자 PC) 내부. 서버 API 아님. 프론트와는 localhost로 통신.

## 5. 부품 창고 (로컬 — .claude 다루기)

| 기능 | 설명 | 구분 | 우선 | 관련 데이터 |
|------|------|:---:|:---:|------|
| .claude 시각화 | 파싱: 파일 → 노드 그래프 | 🟩 | P1 | 로컬 .claude |
| 양방향 동기화 | 직렬화: 그래프 → 파일 (본문 보존) | 🟩 | P1 | 로컬 .claude |
| 스킬 커스텀 | 노드 클릭 → 파일/자연어 편집 (Claude CLI) | 🟩 | P1 | 로컬 .claude |
| 키 연결(붙여넣기) | 카탈로그 팝업으로 키 받아 로컬 저장 | 🟩 | P1 | 로컬 SQLite(credentials) |
| 가져온 것 로컬 반영 | "내 것으로 저장" → .claude에 씀 | 🟩 | P1 | 로컬 .claude |

## 6. 워크플로우 실행 (로컬 — 하네스·엔진)

| 기능 | 설명 | 구분 | 우선 | 관련 데이터 |
|------|------|:---:|:---:|------|
| 워크플로우 실행 엔진 | 그래프 순회(cursor) 실행 (중단/재개) | 🟩 | P1 | in-memory run |
| 조건 분기 (branch) | 유형 판단 → `when` 일치 갈래**만** 실행 | 🟩 | P1 | — |
| 에이전트 실행 | Claude CLI 호출 (판단·생성) | 🟩 | P1 | — |
| MCP 실행 | 실제 도구 호출 (Gmail·택배·노션·슬랙 등). REST 도구(택배)는 앞 단계 메일에서 송장번호·택배사 **자동 추출** | 🟩 | P1 | — |
| 노션 정리 | 요약을 노션 페이지로 생성(제목 [유형]+수신일, 구획 본문) | 🟩 | P1 | 로컬 SQLite(credentials) |
| 하네스: 중복체크 | 이미 처리한 것 제외 | 🟩 | P1 | 로컬 SQLite(processed) |
| 하네스: 검증 | 조건 확인, 안 맞으면 중단 | 🟩 | P1 | — |
| 하네스: 🚨승인게이트 | 멈춤 → 사용자 승인 → 재개 | 🟩 | P1 | in-memory run |
| config 내보내기 | workflow+agent+deploy config 파일 | 🟩 | P2 | 로컬 파일 |
| 스케줄러(무인 트리거) | 새 메일 폴링(IMAP)→자동 실행, 로컬 켜진 동안 | 🟩 | P1 | 로컬 SQLite(watched_workflow) |

## 7. 로컬 실행기 인프라

- **localhost API** (프론트↔로컬 실행기): `GET /graph`(시각화) · `POST /save`(동기화) · `POST /run`(실행) · `GET /run/{id}/status` · `POST /run/{id}/approve`(승인) · `POST /credential`(키 저장) · `GET /credentials`(키 현황) · `POST /processed/reset`(중복이력 초기화) · `POST /watch`·`GET /watch`·`POST /watch/stop`(스케줄러 감시)
- **백그라운드 폴링**: FastAPI lifespan + asyncio 루프. 감시 on이면 N초마다 gmail INBOX 안읽은 메일을 IMAP(stdlib, Claude 미호출)로 확인 → 새 Message-ID면 자동 `start_run` → Message-ID를 `processed`에 기록해 중복 방지.
- **로컬 SQLite 테이블** (ERD 아님, 단순 상태 저장):
  - `processed` (item_key, processed_at) — 중복체크
  - `credentials` (tool_key, secret) — 붙여넣은 키
  - `watched_workflow` (id, graph_json, enabled, interval_sec, updated_at) — 스케줄러가 자동 실행할 감시 워크플로우(단일 행)
  - *실행 중단/재개(run_state)는 현재 in-memory(RUNS dict) — 재시작 시 초기화*

> ❌ 로드맵(지금 안 함): run_log(실행이력), 서브에이전트, 관측(Grafana/Prometheus/Sentry).

---

# 📊 데이터 모델

## 서버 DB (PostgreSQL) — **ERD 대상** ⭐ (팀원 ERD 연습은 이것만)

```
users
  id (PK) · clerk_user_id (unique) · nickname (unique) · is_admin · created_at · updated_at
      │1
      ├───────────────┐N
      │N              │
workflows            skills
  id (PK)             id (PK)
  users_id → users    users_id → users
  name · description   name · description
  graph_json (jsonb)   content_md (text)
  is_public            used_mcps (jsonb)
  import_count (int)   is_public · import_count
  created·updated_at   created·updated_at
      │N                  │N
      │                   │
workflow_tags(M:N)   skill_tags(M:N)
  id PK · 2 FK · UQ쌍   id PK · 2 FK · UQ쌍
      │                   │
      └──── master_tags (id PK · name unique) ────┘

tool_catalog  (독립 — 지원 도구 레지스트리)
  id (PK) · key(unique) · name · description · key_required · key_issue_url · metadata_json(jsonb) · type · auth_owner
```

**엔티티 7개**: `users` · `workflows` · `skills` · `master_tags` · `workflow_tags` · `skill_tags` · `tool_catalog`

**관계 요약**:
- users 1—N workflows / skills (소유, FK `users_id`)
- workflows N—M master_tags (workflow_tags) / skills N—M master_tags (skill_tags) — 연결 테이블은 surrogate PK(id)+UNIQUE(쌍)
- tool_catalog 독립 (참조 레지스트리)

## 로컬 SQLite — 참고용 (ERD 아님)

`processed` · `credentials` · `watched_workflow` — 단순 상태 저장, 관계 없음. 로컬 실행기 명세에만 기재. (실행 중단/재개 상태는 in-memory)

---

*(다음: 이 명세서 기반으로 ① 서버 ERD(팀원 연습→팀장 수정) ② API 명세서(본문 🟦 부분만))*
