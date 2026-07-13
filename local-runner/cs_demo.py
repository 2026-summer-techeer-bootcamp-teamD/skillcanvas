#!/usr/bin/env python3
"""로컬 실행기 CS 시나리오 검증/데모 드라이버. (의존성 없음 — stdlib만)

실행:
  터미널1)  uvicorn app.main:app --port 4737
  터미널2)  python cs_demo.py

CS 컴플레인 대응 워크플로우를 로컬 실행기에 태워
  run → 승인게이트서 멈춤 → status → 승인 재개 → done → 중복체크
가 우리 로직대로 도는지 확인한다.
agent 노드(긴급도 판단·사과문)는 실제 로컬 claude(-p)로 생성된다(claude 설치·로그인 필요).
"""

import json
import urllib.request

BASE = "http://localhost:4737"
KEY = "cs-2026-001"

CS_NODES = [
    {"id": "c1", "type": "trigger", "label": "매일 9시 실행", "detail": "스케줄 트리거"},
    {
        "id": "c2",
        "type": "tool",
        "label": "Gmail 컴플레인 읽기",
        "detail": "받은 메일: '주문 상품이 3일째 배송 안 됨. 너무 화나요. 당장 조치해주세요.'",
    },
    {"id": "c3", "type": "agent", "label": "긴급도 판단", "detail": "감정·긴급도 분석"},
    {"id": "c4", "type": "dedup", "label": "중복 체크", "detail": "이미 처리한 컴플레인 제외"},
    {
        "id": "c5",
        "type": "tool",
        "label": "택배 조회",
        "detail": "조회 결과: 대전HUB에서 3일째 체류 중(배송 지연 확인)",
    },
    {"id": "c6", "type": "verify", "label": "검증", "detail": "배송지연 사실 확인됨"},
    {"id": "c7", "type": "agent", "label": "사과+쿠폰 문구 생성", "detail": "사과문 작성"},
    {
        "id": "c8",
        "type": "approve",
        "label": "승인 게이트",
        "detail": "분노 95%·대전HUB 체류. 사과+쿠폰 발송할까요?",
    },
    {
        "id": "c9",
        "type": "tool",
        "label": "Gmail 사과메일 발송",
        "detail": "Gmail MCP · 아웃바운드",
    },
    {"id": "c10", "type": "output", "label": "처리 기록", "detail": "처리완료 저장"},
]
CS_EDGES = [{"from": f"c{i}", "to": f"c{i + 1}"} for i in range(1, 10)]


def call(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def show(results: list[dict]) -> None:
    for x in results:
        print(f"    {x['id']:>3} [{x['type']:<7}] {x['result']}")


def main() -> None:
    line = "=" * 62
    print(line + "\n SkillCanvas 로컬 실행기 — CS 컴플레인 시나리오 검증\n" + line)

    print("\n[0] 처리이력 초기화(중복체크 리셋):", call("POST", "/processed/reset"))

    print("\n[1] 워크플로우 실행 (POST /run)")
    r = call("POST", "/run", {"nodes": CS_NODES, "edges": CS_EDGES, "item_key": KEY})
    show(r["results"])
    print(f"   → status: {r['status']}")
    if r.get("pending"):
        print(f"   → 🚨 승인 대기: {r['pending']['id']} — \"{r['pending']['message']}\"")
    run_id = r["run_id"]

    print(f"\n[2] 상태 조회 (GET /run/{run_id}/status)")
    s = call("GET", f"/run/{run_id}/status")
    print(f"   → status: {s['status']} / 지금까지 {len(s['results'])}개 노드 실행")

    print(f"\n[3] 승인 → 재개 (POST /run/{run_id}/approve)")
    a = call("POST", f"/run/{run_id}/approve")
    show(a["results"])
    print(f"   → status: {a['status']}")

    print("\n[4] 같은 건 재실행 → 중복체크(dedup)")
    r2 = call("POST", "/run", {"nodes": CS_NODES, "edges": CS_EDGES, "item_key": KEY})
    print(f"   → {r2['results'][-1]['result']}  (status: {r2['status']})")

    print("\n" + line + "\n ✅ 검증 완료 — run·승인게이트·재개·중복체크 정상\n" + line)


if __name__ == "__main__":
    main()
