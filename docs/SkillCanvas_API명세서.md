# 🔌 SkillCanvas — API 명세서 (서버 API)

> **대상**: 호스팅 백엔드(FastAPI) 서버 API. 로컬 실행기 API(localhost)는 부록.
> **컨벤션**: 직접반환(감싸지 않음) · 순수 REST(진짜 액션만 동사) · snake_case · `/api/v1`

---

## 0. 공통 규약

- **Base URL**: `https://api.skillcanvas.example/api/v1`
- **인증**: 보호 엔드포인트는 `Authorization: Bearer {accessToken}` 필요 (Clerk 토큰)
- **성공 응답**: 데이터 **직접 반환** (`{code,message,data}`로 안 감쌈)
- **에러 응답**: HTTP status + `detail`
  ```json
  { "detail": { "code": "WORKFLOW_NOT_FOUND", "message": "워크플로우를 찾을 수 없습니다" } }
  ```
- **필드**: snake_case · **날짜**: ISO 8601 UTC

**공통 Error Codes**

| HTTP 상태 | errorCode | 설명 |
| --- | --- | --- |
| 400 | `COMMON_INVALID_INPUT` | 입력값 유효성 검증 실패 |
| 401 | `AUTH_UNAUTHORIZED` | 인증 토큰 없음 또는 만료 |
| 403 | `AUTH_FORBIDDEN` | 권한 없음 |
| 404 | `COMMON_NOT_FOUND` | 리소스 없음 |
| 500 | `COMMON_INTERNAL_ERROR` | 서버 내부 오류 |

**에러코드 규칙**: 도메인별 코드(`WORKFLOW_NOT_FOUND` 등)가 있으면 그걸 우선, 없으면 위 공통 코드. **검증 실패 구분 — 필드 형식 오류(타입·필수값·글자수)=`400 _INVALID_INPUT`, 내용/구조 무결성 오류(예: 깨진 그래프)=`422`.**

**인가(Authorization) 원칙**: "누가 뭘 볼 수 있냐"는 **항상 토큰에서 뽑은 유저 id로 판단.** 요청 바디·쿼리로 받은 `owner_id`/`user_id`는 **소유권 판정에 절대 쓰지 않는다**(위조 가능). *(인증=Clerk, 인가=우리 백엔드)*

**목록(GET) 공통**: 쿼리 `limit`(기본 20)·`offset`(기본 0). 응답 `{ items, total, limit, offset }`.

---

# 1. 계정 / 프로필

> **회원가입·로그인은 Clerk가 담당 → 별도 API 없음.** 우리 백엔드는 ① Clerk 토큰 검증(미들웨어) ② 첫 로그인 시 `GET /users/me`가 프로필 자동 생성 ③ `PATCH /users/me` 수정만 담당한다.
> ※ `nickname`은 **UNIQUE**라, 자동 생성 시 충돌 없는 기본값(예: `user_a1b2c3`)을 부여하고 이후 사용자가 수정한다.

## 1-1. 내 프로필 조회
로그인한 유저의 프로필을 조회한다. (없으면 첫 로그인으로 간주해 생성 후 반환)

| 항목 | 내용 |
| --- | --- |
| **Method** | `GET` |
| **URL** | `/api/v1/users/me` |
| **인증** | Required |

**Request Headers**

| 헤더 | 값 | 필수 |
| --- | --- | --- |
| Authorization | `Bearer {accessToken}` | Y |

**Path Parameters**: 없음 / **Query Parameters**: 없음 / **Request Body**: 없음

**Response Body (200 OK)**
```json
{
  "id": 12,
  "clerk_user_id": "user_2ab...",
  "nickname": "teamd",
  "created_at": "2026-07-06T00:00:00Z",
  "updated_at": "2026-07-06T00:00:00Z"
}
```

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | Long | 우리 DB 유저 id |
| `clerk_user_id` | String | Clerk 유저 식별자 |
| `nickname` | String | 닉네임 |
| `created_at` | DateTime | 가입일 |
| `updated_at` | DateTime | 마지막 수정일 |

**Error Codes**

| HTTP 상태 | errorCode | 설명 |
| --- | --- | --- |
| 401 | `AUTH_UNAUTHORIZED` | 인증 실패 |
| 500 | `COMMON_INTERNAL_ERROR` | 서버 오류 |

---

## 1-2. 프로필 수정
닉네임을 수정한다.

| 항목 | 내용 |
| --- | --- |
| **Method** | `PATCH` |
| **URL** | `/api/v1/users/me` |
| **인증** | Required |

**Request Headers**

| 헤더 | 값 | 필수 |
| --- | --- | --- |
| Authorization | `Bearer {accessToken}` | Y |
| Content-Type | `application/json` | Y |

**Path Parameters**: 없음 / **Query Parameters**: 없음

**Request Body**
```json
{ "nickname": "teamd" }
```

| 필드 | 타입 | 필수 | 설명 | 제약조건 |
| --- | --- | --- | --- | --- |
| `nickname` | String | Y | 닉네임 | 2~20자 |

**Response Body (200 OK)**
```json
{ "id": 12, "clerk_user_id": "user_2ab...", "nickname": "teamd", "created_at": "2026-07-06T00:00:00Z", "updated_at": "2026-07-07T00:00:00Z" }
```

> **비고**: `nickname`은 **UNIQUE(중복 불가)** — ERD `nickname`에 UK 설정. 이미 쓰는 닉네임으로 수정 시 409 반환.

**Error Codes**

| HTTP 상태 | errorCode | 설명 |
| --- | --- | --- |
| 400 | `COMMON_INVALID_INPUT` | 닉네임 형식 오류 |
| 401 | `AUTH_UNAUTHORIZED` | 인증 실패 |
| 409 | `USER_DUPLICATE_NICKNAME` | 이미 존재하는 닉네임 |

---

# 2. 도구 카탈로그 (MCP + API)

> ERD `tool_catalog` 테이블. MCP·API 도구를 함께 담는다. (택배 API 등 API 도구 + Gmail 등 MCP)

## 2-1. 카탈로그 목록 조회
지원하는 도구(MCP·API) 목록과 키 메타데이터를 반환한다. (키 붙여넣기 팝업이 이걸 읽어 자동 생성)

| 항목 | 내용 |
| --- | --- |
| **Method** | `GET` |
| **URL** | `/api/v1/tool-catalog` |
| **인증** | Optional |

**Request Headers**: 없음(공개) / **Path Parameters**: 없음

**Query Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `limit` | Integer | N | 페이지 크기 (기본 20) |
| `offset` | Integer | N | 시작 위치 (기본 0) |

**Response Body (200 OK)**
```json
{
  "items": [
    { "id": 1, "key": "gmail", "name": "Gmail", "type": "mcp", "auth_owner": "user",
      "key_required": true, "key_issue_url": "https://myaccount.google.com/apppasswords",
      "description": "메일 읽기·발송",
      "metadata_json": { "field": "GMAIL_APP_PASSWORD", "help": "2단계 인증 후 앱 비밀번호 생성", "placeholder": "16자리 앱 비밀번호" } }
  ],
  "total": 8, "limit": 20, "offset": 0
}
```

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `items[].key` | String | 도구 식별키 (코드에서 참조, UNIQUE) |
| `items[].name` | String | 표시명 |
| `items[].type` | String | mcp / api |
| `items[].auth_owner` | String | user(유저 본인 붙여넣기) / developer(개발자=우리 공용키, 붙여넣기 불필요) |
| `items[].key_required` | Boolean | 키 붙여넣기 필요 여부 |
| `items[].key_issue_url` | String / null | "여기서 발급" 링크 (팝업에 표시) |
| `items[].description` | String | 자연어 추천용 설명 |
| `items[].metadata_json` | Object / null | 팝업 세부 (붙여넣을 필드명·안내문구·placeholder 등) |

> **비고**: 이 응답은 **키 붙여넣기 팝업(기능 3.4)을 자동 생성**하는 데 쓰인다.
> - `auth_owner="developer"`(개발자=우리) → 공용키(택배 API 등). **팝업 안 뜸**, 사용자는 붙여넣을 게 없다.
> - `auth_owner="user"`(유저 본인) & `key_required=true` → 팝업 뜸. `key_issue_url`(여기서 발급) + `metadata_json`(붙여넣을 필드명·안내문구)을 그대로 표시.
> **Clerk와 무관** — 우리가 지원하는 도구(MCP·API) 목록이다.
> ※ ERD 코멘트 `"유저"|"개발자"` = 코드 값 `user`|`developer`.

**Error Codes**

| HTTP 상태 | errorCode | 설명 |
| --- | --- | --- |
| 500 | `COMMON_INTERNAL_ERROR` | 서버 오류 |

---

## 2-2. 카탈로그 등록 원칙 (기본 = DB 시드)

> 지원 도구는 **기본적으로 우리(운영)가 DB에 시드(마이그레이션/초기 데이터)로 미리 넣는다.** `metadata_json`·`key_issue_url` 등 안내 문구도 우리가 작성.
> `tool_catalog` 테이블과 조회 API(`GET /tool-catalog`, 2-1)가 핵심이며, **시드만으로도 완전히 동작한다.**
> 런타임에 도구를 추가하는 **등록 API(2-3)는 후순위(개발 여유되면)** — 없어도 무방.

---

## 2-3. 도구 등록 *(후순위 — 개발 여유되면 / 운영자용)*
카탈로그에 새 도구를 추가한다. **원칙은 DB 시드**이고, 런타임에 추가하고 싶을 때 쓰는 선택 엔드포인트.

> **후순위 처리 방침**: 이 엔드포인트와 **운영자 판정(admin)은 지금 만들지 않고 나중에 함께 추가**한다. (현재 스키마엔 role/is_admin 컬럼 없음 → 이 기능 개발 시 컬럼 add 마이그레이션 + 게이팅을 같이 붙임. 컬럼 추가는 Alembic으로 손쉬움.)

| 항목 | 내용 |
| --- | --- |
| **Method** | `POST` |
| **URL** | `/api/v1/tool-catalog` |
| **인증** | Required (운영자 전용 — 게이팅은 개발 시 추가) |

**Request Headers**

| 헤더 | 값 | 필수 |
| --- | --- | --- |
| Authorization | `Bearer {accessToken}` | Y |
| Content-Type | `application/json` | Y |

**Path Parameters**: 없음 / **Query Parameters**: 없음

**Request Body**
```json
{ "key": "slack", "name": "Slack", "type": "mcp", "auth_owner": "user",
  "key_required": true, "key_issue_url": "https://api.slack.com/apps",
  "description": "슬랙 메시지 전송",
  "metadata_json": { "field": "SLACK_BOT_TOKEN", "help": "봇 토큰 생성 후 붙여넣기", "placeholder": "xoxb-..." } }
```

| 필드 | 타입 | 필수 | 설명 | 제약조건 |
| --- | --- | --- | --- | --- |
| `key` | String | Y | 식별키 (UNIQUE, 코드 참조용) | 영문 snake, 1~100자 |
| `name` | String | Y | 표시명 | 1~100자 |
| `type` | String | Y | 도구 종류 | mcp / api |
| `auth_owner` | String | Y | 키 주인 | user / developer |
| `key_required` | Boolean | Y | 키 붙여넣기 필요 여부 | |
| `key_issue_url` | String | N | 키 발급 링크 | 최대 255자 |
| `description` | String | N | 자연어 추천용 설명 | |
| `metadata_json` | Object | N | 팝업 세부(붙여넣을 필드명·안내문구·placeholder) | |

**Response Body (201 Created)**: 생성된 도구 (2-1 items 구조 + `id`)

**Error Codes**

| HTTP 상태 | errorCode | 설명 |
| --- | --- | --- |
| 400 | `COMMON_INVALID_INPUT` | 입력값 검증 실패 |
| 401 | `AUTH_UNAUTHORIZED` | 인증 실패 |
| 403 | `AUTH_FORBIDDEN` | 운영자 아님 |
| 409 | `TOOL_DUPLICATE_KEY` | 이미 존재하는 key |

---

# 3. 자연어 조립 / 추천 (백엔드가 Claude API 호출)

## 3-1. 워크플로우 자동생성
자연어 요청을 워크플로우 그래프로 변환한다. (카탈로그 내 도구로만 구성·검증)

| 항목 | 내용 |
| --- | --- |
| **Method** | `POST` |
| **URL** | `/api/v1/assemble` |
| **인증** | Required |

**Request Headers**

| 헤더 | 값 | 필수 |
| --- | --- | --- |
| Authorization | `Bearer {accessToken}` | Y |
| Content-Type | `application/json` | Y |

**Request Body**
```json
{ "text": "CS 컴플레인 오면 긴급도 보고 배송조회해서 사과+쿠폰, 보내기 전 확인받고",
  "context": [], "target": "workflow" }
```

| 필드 | 타입 | 필수 | 설명 | 제약조건 |
| --- | --- | --- | --- | --- |
| `text` | String | Y | 자연어 업무 설명 | 1~1000자 |
| `context` | String[] | N | 대화 누적 | |
| `target` | String | N | 생성 대상 | workflow(기본) / skill |

**Response Body (200 OK)**
```json
{
  "name": "cs-complaint-handler",
  "nodes": [
    { "id": "n1", "type": "trigger", "label": "매일 9시", "detail": "스케줄" },
    { "id": "n2", "type": "tool", "label": "Gmail 읽기", "detail": "gmail" },
    { "id": "n3", "type": "agent", "label": "긴급도 판단", "detail": "Claude" },
    { "id": "n4", "type": "approve", "label": "승인 게이트", "detail": "발송할까요?" }
  ],
  "edges": [ { "from": "n1", "to": "n2" }, { "from": "n2", "to": "n3" }, { "from": "n3", "to": "n4" } ],
  "used_mcps": ["gmail"]
}
```

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `name` | String | 워크플로우 이름(kebab) |
| `nodes[]` | Object[] | 노드 (id·type·label·detail) |
| `edges[]` | Object[] | 연결 (from·to) |
| `used_mcps` | String[] | 사용된 카탈로그 MCP key |

**Error Codes**

| HTTP 상태 | errorCode | 설명 |
| --- | --- | --- |
| 401 | `AUTH_UNAUTHORIZED` | 인증 실패 |
| 422 | `ASSEMBLE_FAILED` | 그래프 생성/파싱 실패 |
| 502 | `CLAUDE_UNAVAILABLE` | Claude 호출 실패 |

---

## 3-2. MCP 추천
자연어 요청에 붙일 MCP를 추천한다. (카탈로그 안에서만)

| 항목 | 내용 |
| --- | --- |
| **Method** | `POST` |
| **URL** | `/api/v1/recommend` |
| **인증** | Required |

**Request Headers**

| 헤더 | 값 | 필수 |
| --- | --- | --- |
| Authorization | `Bearer {accessToken}` | Y |
| Content-Type | `application/json` | Y |

**Request Body**
```json
{ "text": "회의록 정리해서 노션에 저장하고 싶어" }
```

| 필드 | 타입 | 필수 | 설명 | 제약조건 |
| --- | --- | --- | --- | --- |
| `text` | String | Y | 자연어 요청 | 1~500자 |

**Response Body (200 OK)**
```json
{ "skill": "meeting-notes", "description": "회의록 요약해 노션 저장", "mcps": ["notion"] }
```

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `skill` | String | 추천 스킬명 |
| `description` | String | 한 줄 설명 |
| `mcps[]` | String | 추천 MCP key (카탈로그 내) |

**비고**: 카탈로그에 맞는 게 없으면 `mcps: []` 반환 (없는 도구를 지어내지 않음).

**Error Codes**

| HTTP 상태 | errorCode | 설명 |
| --- | --- | --- |
| 401 | `AUTH_UNAUTHORIZED` | 인증 실패 |
| 422 | `RECOMMEND_FAILED` | 추천 파싱 실패 |
| 502 | `CLAUDE_UNAVAILABLE` | Claude 호출 실패 |

---

## 3-3. 노드 자연어 편집/매핑
워크플로우 노드를 자연어로 수정해 재분류·재매핑한다.

| 항목 | 내용 |
| --- | --- |
| **Method** | `POST` |
| **URL** | `/api/v1/map-node` |
| **인증** | Required |

**Request Headers**: Authorization(Y), Content-Type(Y)

**Request Body**
```json
{ "node": { "type": "tool", "label": "노션 저장", "detail": "notion" }, "instruction": "노션 대신 슬랙으로 보내게" }
```

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `node` | Object | Y | 현재 노드 (type·label·detail) |
| `instruction` | String | Y | 수정 지시 |

**Response Body (200 OK)**
```json
{ "node": { "type": "tool", "label": "슬랙 전송", "detail": "slack" }, "mcp_added": "slack" }
```

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `node` | Object | 갱신된 노드 |
| `mcp_added` | String / null | 새로 필요해진 MCP key |

**Error Codes**

| HTTP 상태 | errorCode | 설명 |
| --- | --- | --- |
| 401 | `AUTH_UNAUTHORIZED` | 인증 실패 |
| 422 | `MAP_NODE_FAILED` | 매핑 실패 |
| 502 | `CLAUDE_UNAVAILABLE` | Claude 호출 실패 |

---

## 3-4. 유형 판단 (스킬 vs 오토플로우)
자연어 요청이 **스킬에 가까운지 워크플로우(오토플로우)에 가까운지** 판단한다. (통합 입력 화면에서 생성 전에 사용자를 유도하는 용도)

| 항목 | 내용 |
| --- | --- |
| **Method** | `POST` |
| **URL** | `/api/v1/classify` |
| **인증** | Required |

**Request Headers**

| 헤더 | 값 | 필수 |
| --- | --- | --- |
| Authorization | `Bearer {accessToken}` | Y |
| Content-Type | `application/json` | Y |

**Request Body**
```json
{ "text": "매일 아침 CS 컴플레인 오면 긴급도 보고 배송조회해서 사과+쿠폰, 보내기 전 확인받고" }
```

| 필드 | 타입 | 필수 | 설명 | 제약조건 |
| --- | --- | --- | --- | --- |
| `text` | String | Y | 자연어 요청 | 1~1000자 |

**판단 기준** *(프롬프트에 주입)*
- **워크플로우에 가까움**: 여러 단계 순서 흐름 · 자동/스케줄 트리거("매일", "~오면") · 사람 승인 지점 · 외부 도구 여러 개 · 조건 분기/반복
- **스킬에 가까움**: 단일 작업/능력 · 단발성 · 도구 없거나 하나 · 흐름 없음

**판정 규칙** *(백엔드에서 계산)*
- Claude가 `skill`·`workflow` 점수(각 0~100, **독립** — 합이 100 아님)를 매긴다.
- 백엔드가 최종 `closer_to` 판정: 이긴 쪽 점수 `< MIN_CONFIDENCE(60)` **또는** 두 점수 차 `< MIN_MARGIN(20)`이면 → **`neutral`**, 아니면 이긴 쪽.
- 원칙: **틀린 추천보다 중립.** 두 상수는 튜닝 손잡이(오추천 잦으면 올림).

**Response Body (200 OK)**
```json
{
  "closer_to": "workflow",
  "confidence": 82,
  "scores": { "skill": 18, "workflow": 82 },
  "reason": "매일 트리거 + 승인 + 다단계"
}
```

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `closer_to` | String | `skill` / `workflow` / `neutral` — 추천 방향(애매하면 `neutral`) |
| `confidence` | Integer | 이긴 쪽 점수 (0~100) |
| `scores` | Object | `{ skill, workflow }` 각 0~100(독립). 튜닝·디버깅용 |
| `reason` | String / null | 한 줄 근거(관측용). **프론트는 미표시** |

**비고**: 프론트는 `closer_to`만 읽어 해당 버튼을 강조(넛지), `neutral`이면 두 버튼 동등. **실패(422/502)든 `neutral`이든 프론트는 "두 버튼 동등"으로 폴백** — 오추천보다 안전.

**Error Codes**

| HTTP 상태 | errorCode | 설명 |
| --- | --- | --- |
| 401 | `AUTH_UNAUTHORIZED` | 인증 실패 |
| 422 | `CLASSIFY_FAILED` | 판단 파싱 실패 |
| 502 | `CLAUDE_UNAVAILABLE` | Claude 호출 실패 |

---

# 4. 갤러리 — 워크플로우

## 4-1. 워크플로우 목록 조회
발행된 워크플로우 목록을 조회한다. (태그 필터·인기순)

| 항목 | 내용 |
| --- | --- |
| **Method** | `GET` |
| **URL** | `/api/v1/workflows` |
| **인증** | Optional |

**Path Parameters**: 없음

**Query Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `tag` | String | N | 태그명 필터 |
| `sort` | String | N | recent(기본) / popular(가져가기순) |
| `mine` | Boolean | N | **내 것만** (인증 필요, **비공개 포함**) |
| `owner_id` | Long | N | 특정 유저의 **공개 것만** (프로필 구경용) |
| `limit` | Integer | N | 기본 20 |
| `offset` | Integer | N | 기본 0 |

**Response Body (200 OK)**
```json
{
  "items": [
    { "id": 8, "name": "CS 컴플레인 봇", "description": "매일 컴플레인 대응",
      "owner": { "id": 12, "nickname": "teamd" }, "tags": ["cs", "자동화"],
      "import_count": 34, "is_public": true, "created_at": "2026-07-06T00:00:00Z" }
  ],
  "total": 137, "limit": 20, "offset": 0
}
```

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `items[].id` | Long | 워크플로우 id |
| `items[].name` | String | 제목(이름) |
| `items[].description` | String | 설명 |
| `items[].owner` | Object | `{ id, nickname }` |
| `items[].tags` | String[] | 태그 |
| `items[].import_count` | Integer | 가져가기 수 |
| `items[].is_public` | Boolean | 공개 여부 (내 목록의 공개/나만보기 배지용) |
| `items[].created_at` | DateTime | 발행일 |

**비고**: 목록엔 `graph_json`(큰 데이터) 미포함 — 상세에서만. 기본은 **공개(`is_public=true`)만 노출**. **비공개(나만보기)는 오직 `mine=true`(+인증)로 본인 것만** 반환하며, 이때 소유자 판정은 **토큰 유저 id**로 한다(쿼리 `owner_id` 아님). `owner_id`는 남의 **공개** 목록 구경에만 쓴다.

**Error Codes**

| HTTP 상태 | errorCode | 설명 |
| --- | --- | --- |
| 500 | `COMMON_INTERNAL_ERROR` | 서버 오류 |

---

## 4-2. 워크플로우 상세 조회
워크플로우 상세를 조회한다. (그래프 JSON 포함 — 미리보기·가져오기용)

| 항목 | 내용 |
| --- | --- |
| **Method** | `GET` |
| **URL** | `/api/v1/workflows/{workflow_id}` |
| **인증** | Optional (공개=누구나 / 비공개=소유자 본인만) |

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `workflow_id` | Long | Y | 워크플로우 id |

**Response Body (200 OK)**
```json
{
  "id": 8, "name": "CS 컴플레인 봇", "description": "매일 컴플레인 대응",
  "owner": { "id": 12, "nickname": "teamd" }, "tags": ["cs", "자동화"],
  "graph_json": { "nodes": [], "edges": [] },
  "import_count": 34, "is_public": true,
  "created_at": "2026-07-06T00:00:00Z", "updated_at": "2026-07-06T00:00:00Z"
}
```

**Error Codes**

| HTTP 상태 | errorCode | 설명 |
| --- | --- | --- |
| 404 | `WORKFLOW_NOT_FOUND` | 없거나, **비공개인데 소유자가 아님**(존재 자체를 숨김) |

> **비고**: 비공개를 남이 요청하면 403이 아니라 **404**로 준다 — 403은 "그 id가 존재함"을 알려주므로, 존재 자체를 숨기려 404 사용.

---

## 4-3. 워크플로우 발행
내 워크플로우를 갤러리에 발행한다.

| 항목 | 내용 |
| --- | --- |
| **Method** | `POST` |
| **URL** | `/api/v1/workflows` |
| **인증** | Required |

**Request Headers**

| 헤더 | 값 | 필수 |
| --- | --- | --- |
| Authorization | `Bearer {accessToken}` | Y |
| Content-Type | `application/json` | Y |

**Path Parameters**: 없음 / **Query Parameters**: 없음

**Request Body**
```json
{ "name": "CS 컴플레인 봇", "description": "매일 컴플레인 대응",
  "graph_json": { "nodes": [], "edges": [] }, "tags": ["cs", "자동화"], "is_public": true }
```

| 필드 | 타입 | 필수 | 설명 | 제약조건 |
| --- | --- | --- | --- | --- |
| `name` | String | Y | 제목(이름) | 1~200자 |
| `description` | String | N | 설명 | 최대 500자 |
| `graph_json` | Object | Y | 노드·엣지 그래프 | 유효한 그래프 |
| `tags` | String[] | N | 태그명 | 최대 5개 |
| `is_public` | Boolean | N | 공개 여부 | 기본 true |

**Response Body (201 Created)**
```json
{
  "id": 8, "name": "CS 컴플레인 봇",
  "owner": { "id": 12, "nickname": "teamd" }, "tags": ["cs", "자동화"],
  "import_count": 0, "is_public": true,
  "created_at": "2026-07-06T00:00:00Z", "updated_at": "2026-07-06T00:00:00Z"
}
```
**비고**: `owner_id`는 토큰에서 추출(요청에 안 받음). `import_count` 0 초기화. `is_public` 생략 시 기본 `true`(발행=공개).

**Error Codes**

| HTTP 상태 | errorCode | 설명 |
| --- | --- | --- |
| 400 | `COMMON_INVALID_INPUT` | 입력값 검증 실패 |
| 401 | `AUTH_UNAUTHORIZED` | 인증 실패 |
| 422 | `WORKFLOW_INVALID_GRAPH` | graph_json 형식 오류 |

---

## 4-4. 워크플로우 수정
발행된 워크플로우의 제목·설명·태그·공개여부를 수정한다. (그래프 수정은 재발행 권장)

| 항목 | 내용 |
| --- | --- |
| **Method** | `PATCH` |
| **URL** | `/api/v1/workflows/{workflow_id}` |
| **인증** | Required (소유자) |

**Request Headers**: Authorization(Y), Content-Type(Y)

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `workflow_id` | Long | Y | 워크플로우 id |

**Request Body** (변경할 필드만)
```json
{ "name": "CS 자동 대응 봇", "is_public": false }
```

| 필드 | 타입 | 필수 | 설명 | 제약조건 |
| --- | --- | --- | --- | --- |
| `name` | String | N | 제목(이름) | 1~200자 |
| `description` | String | N | 설명 | 최대 500자 |
| `tags` | String[] | N | 태그명 | 최대 5개 |
| `is_public` | Boolean | N | 공개 여부 (나만보기 토글) | |

**Response Body (200 OK)**: 수정된 워크플로우 (4-3 응답 구조)

**Error Codes**

| HTTP 상태 | errorCode | 설명 |
| --- | --- | --- |
| 401 | `AUTH_UNAUTHORIZED` | 인증 실패 |
| 403 | `WORKFLOW_FORBIDDEN` | 소유자 아님 |
| 404 | `WORKFLOW_NOT_FOUND` | 없음 |

---

## 4-5. 워크플로우 삭제
내 워크플로우를 삭제한다.

| 항목 | 내용 |
| --- | --- |
| **Method** | `DELETE` |
| **URL** | `/api/v1/workflows/{workflow_id}` |
| **인증** | Required (소유자) |

**Request Headers**: Authorization(Y)

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `workflow_id` | Long | Y | 워크플로우 id |

**Response Body (204 No Content)**: 없음

**Error Codes**

| HTTP 상태 | errorCode | 설명 |
| --- | --- | --- |
| 401 | `AUTH_UNAUTHORIZED` | 인증 실패 |
| 403 | `WORKFLOW_FORBIDDEN` | 소유자 아님 |
| 404 | `WORKFLOW_NOT_FOUND` | 없음 |

---

## 4-6. 워크플로우 가져오기
남의 **공개** 워크플로우(또는 내 것)를 가져온다. 그래프 JSON을 반환하고 가져가기 수를 증가시킨다.

| 항목 | 내용 |
| --- | --- |
| **Method** | `POST` |
| **URL** | `/api/v1/workflows/{workflow_id}/import` |
| **인증** | Required |

**Request Headers**: Authorization(Y)

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `workflow_id` | Long | Y | 워크플로우 id |

**Request Body**: 없음

**Response Body (200 OK)**
```json
{ "id": 8, "name": "CS 컴플레인 봇",
  "graph_json": { "nodes": [], "edges": [] }, "import_count": 35 }
```

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `graph_json` | Object | 캔버스에 로드할 그래프 |
| `import_count` | Integer | 증가 후 값 |

**비고**: 실제 로컬 `.claude` 반영은 **로컬 실행기**(부록)가 담당. 이 API는 그래프만 반환. **비공개(is_public=false)이면서 내 것이 아니면 가져올 수 없다**(아래 404).

**Error Codes**

| HTTP 상태 | errorCode | 설명 |
| --- | --- | --- |
| 401 | `AUTH_UNAUTHORIZED` | 인증 실패 |
| 404 | `WORKFLOW_NOT_FOUND` | 없거나, **비공개인데 소유자가 아님**(존재 숨김) |

---

# 5. 갤러리 — 스킬

> 워크플로우(4번)와 **동일 구조**(필드명 `name`·`is_public`·`import_count` 동일, **`mine` 필터·비공개 404 숨김·import 비공개 차단 등 인가 규칙도 동일**). 차이: `graph_json` 대신 `content_md`(String, SKILL.md 원문).

| 번호 | 기능 | Method · URL |
| --- | --- | --- |
| 5-1 | 스킬 목록 조회 | `GET /api/v1/skills` (4-1과 동일) |
| 5-2 | 스킬 상세 조회 | `GET /api/v1/skills/{skill_id}` (`content_md` 포함) |
| 5-3 | 스킬 발행 | `POST /api/v1/skills` |
| 5-4 | 스킬 수정 | `PATCH /api/v1/skills/{skill_id}` |
| 5-5 | 스킬 삭제 | `DELETE /api/v1/skills/{skill_id}` |
| 5-6 | 스킬 가져오기 | `POST /api/v1/skills/{skill_id}/import` |

**5-3 발행 Request Body 예시**
```json
{ "name": "meeting-notes", "description": "회의록 요약",
  "content_md": "---\nname: meeting-notes\nallowed-tools: [notion]\n---\n# 회의록 정리...",
  "tags": ["pm"], "is_public": true }
```

| 필드 | 타입 | 필수 | 설명 | 제약조건 |
| --- | --- | --- | --- | --- |
| `name` | String | Y | 스킬명 | kebab, 1~200자 |
| `description` | String | N | 설명 | 최대 500자 |
| `content_md` | String | Y | SKILL.md 원문 (frontmatter 포함) | |
| `tags` | String[] | N | 태그 | 최대 5개 |
| `is_public` | Boolean | N | 공개 여부 | 기본 true |

**비고**: frontmatter는 `content_md`(SKILL.md 원문) **안에 들어있다.** 서버는 원문만 저장하고, 파싱이 필요하면 **로컬 실행기**가 처리 — 별도 frontmatter 컬럼 없음.

**Error Codes**: 워크플로우와 동일 (`SKILL_NOT_FOUND` 등 도메인만 교체). 상세·가져오기의 비공개 처리도 워크플로우처럼 **404로 숨김**.

---

# 6. 태그

## 6-1. 태그 목록 조회
사용 중인 태그 목록을 조회한다. (필터 UI용)

| 항목 | 내용 |
| --- | --- |
| **Method** | `GET` |
| **URL** | `/api/v1/tags` |
| **인증** | Optional |

**Response Body (200 OK)**
```json
{ "items": [ { "id": 1, "name": "cs" }, { "id": 2, "name": "자동화" } ], "total": 2 }
```

> **비고**: 태그는 개수가 적어 **페이지네이션 없이 전체 반환**(의도된 예외 — `limit`·`offset` 없음).

---

# 부록. 로컬 실행기 API (localhost · 팀장 담당)

> 호스팅 서버 API 아님. 사용자 PC의 로컬 실행기(FastAPI)가 `http://localhost:{port}`(기본 4737)로 제공. 프론트가 파일·실행을 위해 호출.
> **인증 없음**(로컬 전용). 성공은 **직접 반환**, 에러는 `detail: { code, message }` — 서버 API와 동일 규약.

| 번호 | 기능 | Method · URL | 설명 |
| --- | --- | --- | --- |
| A-1 | 부품 시각화 | `GET /graph` | `.claude` 파싱 → 노드 그래프 |
| A-2 | 저장(동기화) | `POST /save` | 스킬 구조 → `SKILL.md` (본문 보존) |
| A-3 | 실행 시작 | `POST /run` | 그래프 실행, 승인게이트서 `awaiting_approval` |
| A-4 | 실행 상태 | `GET /run/{run_id}/status` | run 현재 상태·결과 |
| A-5 | 승인 재개 | `POST /run/{run_id}/approve` | 저장 지점부터 이어서 실행 |
| A-6 | 키 저장 | `POST /credential` | 도구 키 로컬 저장 |
| A-7 | 중복체크 초기화 | `POST /processed/reset` | 데모 리허설용 |

---

## A-1. 부품 시각화
로컬 `.claude`(스킬·MCP·룰)를 파싱해 노드 그래프로 반환한다.

| 항목 | 내용 |
| --- | --- |
| **Method** | `GET` |
| **URL** | `/graph` |
| **인증** | 없음 |

**Response Body (200 OK)**
```json
{
  "nodes": [
    { "id": "mcp:notion", "type": "mcp", "label": "notion" },
    { "id": "rule:settings", "type": "rule", "label": "권한 룰", "detail": "settings.json" },
    { "id": "skill:meeting-notes", "type": "skill", "label": "meeting-notes", "detail": "회의록 요약해 저장" }
  ],
  "edges": [
    { "from": "skill:meeting-notes", "to": "mcp:notion", "kind": "uses" },
    { "from": "skill:meeting-notes", "to": "rule:settings", "kind": "rule" }
  ]
}
```

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `nodes[].id` | String | `{type}:{name}` 형식 |
| `nodes[].type` | String | `mcp` / `rule` / `skill` |
| `nodes[].label` | String | 표시명 |
| `nodes[].detail` | String | 설명(스킬=description, 룰=파일명). SKILL.md 형식 오류 시 `⚠️ SKILL.md 형식 오류` |
| `edges[].from` / `to` | String | 노드 id |
| `edges[].kind` | String | `uses`(스킬→도구) / `rule`(스킬→룰) |

---

## A-2. 저장(동기화)
스킬 구조를 `SKILL.md`로 저장한다. `body`를 주면 **그 본문으로 저장**(빌더에서 조립한 본문), 없으면 **기존 본문 보존**(신규는 플레이스홀더)하고 frontmatter만 갱신. 없는 스킬은 신규 생성.

| 항목 | 내용 |
| --- | --- |
| **Method** | `POST` |
| **URL** | `/save` |
| **인증** | 없음 |

**Request Body**
```json
{ "skill": "meeting-notes", "name": "meeting-notes",
  "description": "회의록을 요약해 Notion에 저장", "allowed_tools": ["notion", "slack"],
  "body": "# 회의록 정리\n1. Slack에서 회의록을 받는다\n2. 200자로 요약한다\n..." }
```

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `skill` | String | Y | 스킬 폴더명(식별자). 단일 폴더명만(`/`·`.`·`..` 불가) |
| `name` | String | Y | 스킬 이름(frontmatter) |
| `description` | String | N | 설명 |
| `allowed_tools` | String[] | N | 사용할 도구 key 목록 |
| `body` | String | N | `SKILL.md` 본문. 주면 그 값으로 저장, 없으면 기존 본문 보존(신규는 플레이스홀더) |

**Response Body (200 OK)**: 저장 반영된 최신 그래프(A-1과 동일 형식 `{ nodes, edges }`)

**Error Codes**

| HTTP 상태 | errorCode | 설명 |
| --- | --- | --- |
| 400 | `SAVE_INVALID_INPUT` | 잘못된 스킬 이름 / 기존 파일 형식 오류 |

---

## A-3. 실행 시작
그래프(노드+엣지)를 위상정렬해 순서대로 실행한다. 승인 게이트를 만나면 멈춘다.

| 항목 | 내용 |
| --- | --- |
| **Method** | `POST` |
| **URL** | `/run` |
| **인증** | 없음 |

**Request Body**
```json
{ "nodes": [ { "id": "n1", "type": "trigger", "label": "시작" } ],
  "edges": [ { "from": "n1", "to": "n2" } ],
  "item_key": "cs-2026-001" }
```

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `nodes` | Object[] | Y | 노드(각 `id` 필수). type: trigger/agent/tool/dedup/verify/approve/output |
| `edges` | Object[] | N | 연결(`from`·`to`) |
| `item_key` | String | N | 중복체크 식별자. 미지정 시 런마다 유니크(항상 신규). dedup 시연 시 명시 |

**Response Body (200 OK)**
```json
{ "run_id": "run1", "status": "awaiting_approval",
  "pending": { "id": "n4", "message": "사과+쿠폰 발송할까요?" },
  "results": [ { "id": "n1", "label": "시작", "type": "trigger", "result": "⏱ 트리거 발동" } ] }
```

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `run_id` | String | 실행 세션 id (재개·조회용) |
| `status` | String | `done` / `awaiting_approval`(승인 대기) / `stopped`(중복 등 중단) |
| `results[]` | Object[] | 실행된 노드별 결과(`id`·`label`·`type`·`result`) |
| `pending` | Object | 승인 대기 노드(`id`·`message`). `awaiting_approval`일 때만 |

**Error Codes**

| HTTP 상태 | errorCode | 설명 |
| --- | --- | --- |
| 400 | `RUN_INVALID_INPUT` | `id` 없는 노드 등 잘못된 그래프 |

---

## A-4. 실행 상태
run의 현재 상태와 **전체 결과(누적)**를 조회한다.

| 항목 | 내용 |
| --- | --- |
| **Method** | `GET` |
| **URL** | `/run/{run_id}/status` |
| **인증** | 없음 |

**Response Body (200 OK)**: A-3와 동일 형식(`run_id`·`status`·`results`(전체)·`pending?`)

**Error Codes**

| HTTP 상태 | errorCode | 설명 |
| --- | --- | --- |
| 404 | `RUN_NOT_FOUND` | 해당 run 없음(만료·미존재) |

---

## A-5. 승인 재개
승인 대기 중인 run을 저장된 지점부터 이어서 실행한다. 다음 승인/중단/끝에서 다시 멈춘다.

| 항목 | 내용 |
| --- | --- |
| **Method** | `POST` |
| **URL** | `/run/{run_id}/approve` |
| **인증** | 없음 |

**Response Body (200 OK)**: A-3와 동일 형식. 단 `results`는 **이번에 새로 실행된 델타만**(전체 아님).
> 프론트 계약: `approve` 응답은 append, `status`(A-4) 응답은 전체로 갈아끼운다. 승인 대기 아닌 run이면 `results: []`.

**Error Codes**

| HTTP 상태 | errorCode | 설명 |
| --- | --- | --- |
| 404 | `RUN_NOT_FOUND` | 해당 run 없음 |

---

## A-6. 키 저장
도구 API 키를 **로컬 SQLite에만** 저장한다(서버 전송 X). 같은 `tool_key`면 덮어씀(upsert).

| 항목 | 내용 |
| --- | --- |
| **Method** | `POST` |
| **URL** | `/credential` |
| **인증** | 없음 |

**Request Body**
```json
{ "tool_key": "notion", "secret": "sk-ant-..." }
```

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `tool_key` | String | Y | 도구 key(카탈로그 key). 저장 시 `strip().lower()` 정규화 |
| `secret` | String | Y | 키 값(원문 저장). 공백-only 불가. 값이 여러 개인 도구(gmail·slack 등)는 JSON 객체 문자열 |

> 도구에 따라 저장 전에 부족한 값을 대신 조회해 채운다. 예: 텔레그램은 **봇 토큰만** 받고
> `chat_id`는 `getUpdates`로 자동 조회한다(유저가 JSON을 열어 찾지 않아도 됨).
> 조회에 실패하면 400 `CREDENTIAL_RESOLVE_FAILED`.

**Response Body (200 OK)**
```json
{ "ok": true, "tool_key": "notion" }
```
> ⚠️ `secret`은 응답에 노출하지 않는다. (현재 평문 저장 — 암호화는 후속)

**Error Codes**

| HTTP 상태 | errorCode | 설명 |
| --- | --- | --- |
| 400 | `CREDENTIAL_INVALID_INPUT` | `tool_key`/`secret` 누락·공백 |
| 400 | `CREDENTIAL_RESOLVE_FAILED` | 자동 조회 실패 (토큰 무효, 봇과 대화 미시작 등). `message`에 사용자가 고칠 수 있는 사유가 담긴다 |

---

## A-7. 중복체크 초기화 *(데모 리허설용)*
저장된 처리이력(processed)을 전부 지워, 같은 `item_key`로 다시 "신규" 실행을 시연할 수 있게 한다.

| 항목 | 내용 |
| --- | --- |
| **Method** | `POST` |
| **URL** | `/processed/reset` |
| **인증** | 없음 |

**Response Body (200 OK)**
```json
{ "ok": true, "deleted": 3 }
```

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `deleted` | Integer | 삭제된 처리이력 행 수 |

---

*형식: 직접반환 · 순수 REST · `{code, message}` errorCode. 로컬 SQLite(processed·credentials)는 ERD 아님(로컬 상태 저장).*

### A-8. 등록된 도구 키 목록 조회

로컬에 저장된 MCP 도구 키 현황을 조회한다. secret 값은 포함하지 않는다.

| 항목 | 내용 |
| --- | --- |
| **Method** | `GET` |
| **URL** | `/credentials` |
| **인증** | 불필요 (로컬 전용) |

**Response Body (200 OK)**
```json
{ "tool_keys": ["slack", "notion"] }
```
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `tool_keys` | String[] | 등록된 도구 key 목록. secret은 응답에 포함되지 않음 |
