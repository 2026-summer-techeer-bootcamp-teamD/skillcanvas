# 로컬 실행기 (Local Runner)

> **팀장 담당.** 사용자 PC에서 도는 작은 FastAPI 프로그램.

## 하는 일
- `.claude` 파싱/직렬화 (양방향 동기화)
- 워크플로우 실행 엔진 (중단/재개)
- 하네스 (중복체크·검증·🚨승인게이트)
- Claude CLI 호출, MCP 실행, 스케줄(APScheduler), 로컬 SQLite

## 참고
- 개념 증명(PoC): `../../skillcanvas-poc/server.mjs` (JavaScript로 만든 프로토타입)
- → Python으로 이식 예정
- 상세: `../docs/SkillCanvas_시스템정리.md`, `../docs/SkillCanvas_기능명세서.md`(부록)

*(이 폴더는 나중에 채웁니다. 지금은 자리만.)*
