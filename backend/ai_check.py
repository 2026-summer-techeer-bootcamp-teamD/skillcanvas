#!/usr/bin/env python3
"""백엔드 AI 엔드포인트 검증 (3-1 assemble / 3-2 recommend / 3-3 map-node). stdlib만.

실행:
  터미널1)  cd backend && source .venv/bin/activate && uvicorn app.main:app --port 8000
  터미널2)  cd backend && source .venv/bin/activate && python ai_check.py

전제:
  - .env 에 ANTHROPIC_API_KEY 설정 (없으면 502 CLAUDE_UNAVAILABLE)
  - DB에 카탈로그 시드 (python -m app.seed_tools)
  - 인증은 로컬 스텁: Bearer 문자열이 곧 유저 식별자
"""

import json
import urllib.error
import urllib.request

BASE = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json", "Authorization": "Bearer tester"}


def call(method: str, path: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def catalog_keys() -> set[str]:
    _, page = call("GET", "/tool-catalog?limit=100")
    return {it["key"] for it in page.get("items", [])}


def check_catalog(mcps: list[str], keys: set[str]) -> None:
    outside = [m for m in mcps if m not in keys]
    if outside:
        print(f"    ⚠ 카탈로그 밖 도구(지어냄 — 로직 위반): {outside}")
    else:
        print(f"    ✅ 모두 카탈로그 내: {mcps}")


def main() -> None:
    line = "=" * 62
    print(line + "\n 백엔드 AI 엔드포인트 검증 (3-1/3-2/3-3)\n" + line)
    keys = catalog_keys()
    print(f"\n카탈로그 {len(keys)}개 로드됨")

    print('\n[3-2] recommend — "회의록 정리해서 노션에 저장하고 싶어"')
    st, r = call("POST", "/recommend", {"text": "회의록 정리해서 노션에 저장하고 싶어"})
    if st != 200:
        print(f"   ❌ {st}: {r.get('detail')}")
    else:
        print(f"   skill: {r['skill']} — {r['description']}")
        print(f"   mcps: {r['mcps']}")
        check_catalog(r["mcps"], keys)

    print("\n[3-1] assemble — CS 컴플레인 워크플로우 자동생성")
    st, r = call(
        "POST",
        "/assemble",
        {
            "text": "CS 컴플레인 오면 긴급도 보고 배송조회해서 사과+쿠폰, 보내기 전 확인받고",
            "target": "workflow",
        },
    )
    if st != 200:
        print(f"   ❌ {st}: {r.get('detail')}")
    else:
        print(f"   name: {r['name']} / 노드 {len(r['nodes'])}개")
        for n in r["nodes"]:
            print(f"     {n['id']} [{n['type']:<7}] {n['label']}")
        print(f"   used_mcps: {r['used_mcps']}")
        check_catalog(r["used_mcps"], keys)

    print("\n[3-3] map-node — '노션 저장' 노드를 '슬랙으로'")
    st, r = call(
        "POST",
        "/map-node",
        {
            "node": {"type": "tool", "label": "노션 저장", "detail": "notion"},
            "instruction": "노션 대신 슬랙으로 보내게",
        },
    )
    if st != 200:
        print(f"   ❌ {st}: {r.get('detail')}")
    else:
        print(f"   변환된 노드: {r['node']}")
        print(f"   mcp_added: {r.get('mcp_added')}")

    print("\n" + line)
    print(" ※ 502 CLAUDE_UNAVAILABLE → .env의 ANTHROPIC_API_KEY 확인")
    print(line)


if __name__ == "__main__":
    main()
