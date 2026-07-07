# 📏 SkillCanvas — 팀 컨벤션 (코드 + API)

> **목적**: 팀 전원이 지킬 규칙. **AI로 개발할 때 이 문서를 규칙으로 지칭**하세요.
> (예: AI에게 *"SkillCanvas_컨벤션.md 규칙 지켜서 짜줘"*)
> **레포 세팅 시**: 이 파일을 `CONVENTIONS.md`로 루트에 넣기.

*(작성일 2026-07-06 · 스택: FastAPI(Python) + React(TypeScript))*

---

## 0. 공통 원칙

- **명확한 이름**: 기능을 알 수 있는 단어로. 축약·모호한 이름 금지.
- **실행되는 코드만 커밋**: 죽은 코드·주석 처리된 코드·`console.log`/`print` 디버그 남기지 않기.
- **린터/포매터가 강제**: 스타일은 외우지 말고 툴이 자동 정리 (아래 6번).

---

## 1. 백엔드 (Python / FastAPI)

**네이밍**
- 변수·함수·attribute: `snake_case` (소문자 + 밑줄) — `import_count`, `get_workflow`
- 모듈 상수: `ALL_CAPS` — `API_BASE_URL`, `MAX_RETRY`
- 클래스: `PascalCase` — `WorkflowService`

**스타일**
- 들여쓰기 **공백 4칸**
- **한 줄 `if`/`for`/`while`/`except` 금지** → 여러 줄로 명료하게
  ```python
  # ❌
  if not user: raise HTTPException(404)
  # ✅
  if not user:
      raise HTTPException(status_code=404, detail="...")
  ```
- **import는 절대경로** 사용 (상대경로 지양)
- **타입 힌트 필수** — FastAPI/Pydantic가 검증·문서 자동생성에 사용
  ```python
  def publish_workflow(payload: WorkflowCreate) -> WorkflowRead:
  ```

**예외 처리**
- **`except:` (뭉뚱그리기) 금지** → 명확한 예외 명시
  ```python
  # ❌ except:
  # ✅
  except FileNotFoundError:
      ...
  except json.JSONDecodeError:
      ...
  ```

**주석**
- 인라인 주석은 코드와 **같은 줄**, **공백 2칸 이상** 띄우고, `#` 뒤 **공백 1칸**
  ```python
  count += 1  # 가져가기 수 증가
  ```

---

## 2. 프론트 (React / TypeScript)

**파일 확장자**
- **`.tsx`** (TypeScript) — `.jsx`(JS) 쓰지 않음

**네이밍**
- **컴포넌트 (파일 + 함수): `PascalCase`** — `WorkflowCanvas.tsx`, `function WorkflowCanvas()`
- 변수·함수·훅: `camelCase` — `nodeList`, `handleSave`, `useWorkflow`(훅은 `use` + camel)
- 타입·인터페이스: `PascalCase` — `type NodeProps`, `interface Workflow`
- 상수: `UPPER_SNAKE_CASE` — `API_BASE_URL`

**문법**
- **`var` 금지** → `let` / `const`만
- **TS 타입 명시** — `any` 남발 금지

**스타일(CSS)**
- 단위는 **`rem` · `%`(또는 분수)** 사용, **`px` 금지**
- 예외: **React Flow 노드 좌표**(x/y)는 `px` 자연스러움 → 허용

---

## 3. API 컨벤션

**기본**
- Base path: **`/api/v1/...`**
- 리소스명: **복수형 소문자**, 여러 단어는 kebab — `/api/v1/workflows`, `/api/v1/mcp-catalog`
- **JSON 필드 = `snake_case`** (백엔드와 일관)
- 날짜: **ISO 8601 UTC** — `2026-07-06T00:00:00Z`

**메서드 / CRUD**
| 동작 | 예 |
|------|-----|
| 목록 | `GET /api/v1/workflows` |
| 상세 | `GET /api/v1/workflows/{id}` |
| 생성 | `POST /api/v1/workflows` |
| 부분수정 | `PATCH /api/v1/workflows/{id}` |
| 삭제 | `DELETE /api/v1/workflows/{id}` |
| 액션(CRUD 아님) | `POST /api/v1/assemble`, `POST /api/v1/workflows/{id}/import` |

**응답 형식**
- **성공**: 데이터 **직접 반환** (감싸지 않음)
  ```json
  { "id": 1, "title": "...", "import_count": 3 }
  ```
- **실패**: HTTP status + `detail`에 커스텀 코드/메시지
  ```python
  raise HTTPException(
      status_code=404,
      detail={"code": "WORKFLOW_NOT_FOUND", "message": "워크플로우를 찾을 수 없습니다"}
  )
  ```
- **errorCode 네이밍**: `{도메인}_{내용}` 대문자+밑줄
  - 공통: `COMMON_INVALID_INPUT`, `COMMON_NOT_FOUND`, `COMMON_INTERNAL_ERROR`
  - 인증: `AUTH_UNAUTHORIZED`(401), `AUTH_FORBIDDEN`(403)
  - 도메인: `WORKFLOW_NOT_FOUND`, `WORKFLOW_INVALID_GRAPH`, `CATALOG_DUPLICATE_KEY` 등

**URL 스타일**: 순수 REST (CRUD는 메서드만, `/edit`·`/delete` 안 붙임) + **진짜 액션만 동사** (`POST /workflows/{id}/import`, `POST /assemble`)

**상태 코드**
| 코드 | 의미 |
|------|------|
| 200 | 성공 |
| 201 | 생성됨 |
| 400 | 잘못된 요청 |
| 401 | 인증 실패 |
| 403 | 권한 없음 |
| 404 | 없음 |
| 500 | 서버 오류 |

**인증**
- 보호 엔드포인트: `Authorization: Bearer <clerk_token>` 헤더

**목록 페이지네이션**
- `GET /api/v1/workflows?limit=20&offset=0`

---

## 4. 로컬 실행기 API (참고 — 팀장 담당)

- 호스팅 API와 별개 (localhost). 같은 응답/에러 규칙 따름.
- 엔드포인트: `GET /graph` · `POST /save` · `POST /run` · `GET /run/{id}/status` · `POST /run/{id}/approve` · `POST /credential`

---

## 5. 린터 / 포매터 (필수 — 컨벤션 자동 강제)

> 설정 한 번 하면, 저장/커밋 시 자동으로 규칙 적용 → 아무도 안 외워도 통일.

**백엔드 (Python)**
- **black** (포매터) — 들여쓰기·따옴표·줄바꿈 자동
- **ruff** (린터) — 안 쓰는 변수/import, snake_case 위반, `except:` 등 경고
- 설정: `pyproject.toml`

**프론트 (TypeScript)**
- **Prettier** (포매터) — 세미콜론·따옴표·정렬 자동
- **ESLint** (린터) — `var` 금지, `any` 경고, 안 쓰는 변수 등
- 설정: `.prettierrc`, `.eslintrc`

**적용**
- 에디터에 확장 설치 → **저장 시 자동 포맷**
- (선택) GitHub Actions에서 PR 때 린트 체크 → 규칙 어기면 빨간불

---

## 6. (나중에) Git 컨벤션

> API 명세·개발 시작 전에 팀에서 별도로 정하기. 예시 방향:
- 브랜치: `feature/기능명`, `fix/버그명`
- 커밋: `feat: ...`, `fix: ...`, `docs: ...` (Conventional Commits)
- PR: 리뷰 1명 이상 승인 후 머지

---

*이 문서를 기준으로 AI 코딩 툴에게 "이 컨벤션 지켜서 작성"이라고 지칭하세요.*
