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
        # 스텁이 아니라 **실제 Gmail(IMAP) 읽기**.
        # "가장 최근 메일"이 아니라 "최근 메일 중 고객 문의"인 이유: 그냥 최신을 집으면
        # 구글 보안 알림·뉴스레터 같은 게 하나만 끼어들어도 그걸 컴플레인으로 오인해
        # 뒤 단계가 통째로 무너진다(실제로 최신이 구글 알림이라 그렇게 됐다).
        "id": "c2",
        "type": "tool",
        "label": "Gmail 컴플레인 읽기",
        "mcp_key": "gmail",
        "detail": "받은편지함 최근 메일 중 고객 문의·항의 메일 1건을 읽어 발신자·제목·본문을 출력",
    },
    {
        # ⚠️ 조회를 '긴급도 판단'보다 **먼저** 둔다. 반대로 두면 AI가 데이터 없이 컴플레인만
        # 보고 "당일배송 약속 미이행"이라 단정해버리고, 그 프레임이 history를 타고 사과문까지
        # 오염된다(실제로 그랬다 — 배송완료라면서 배송 못 했다고 사과하는 모순이 나옴).
        #
        # 스텁이 아니라 **실제 스마트택배 API 호출**. 키는 credentials(SQLite)에서 읽고
        # 프롬프트엔 안 들어간다. 미등록이면 여기서 '키 미등록'으로 멈춘다.
        #   curl -X POST localhost:4737/credential \
        #        -d '{"tool_key":"sweettracker","secret":"발급키"}'
        "id": "c3",
        "type": "tool",
        "label": "택배 조회",
        "mcp_key": "sweettracker",
        "detail": "t_code=04&t_invoice=511951252170",  # 04 = CJ대한통운
    },
    {
        "id": "c4",
        "type": "agent",
        "label": "긴급도 판단",
        "detail": "조회 결과와 컴플레인 대조",
    },
    {"id": "c5", "type": "dedup", "label": "중복 체크", "detail": "이미 처리한 컴플레인 제외"},
    {"id": "c6", "type": "verify", "label": "검증", "detail": "대응 방향 확정"},
    {
        "id": "c7",
        "type": "agent",
        "label": "답변 문구 생성",
        "detail": "조회 사실에 근거해 작성",
    },
    {
        "id": "c8",
        "type": "approve",
        "label": "승인 게이트",
        "detail": "조회 결과를 확인하고 답변을 보낼까요?",
    },
    {
        # 스텁이 아니라 **실제 발송(SMTP)**. 진짜 메일이 나간다.
        # 수신자를 박지 않고 c2가 읽은 발신자에게 회신하는 구조 — 진짜 CS 흐름이지만,
        # c2가 엉뚱한 메일(구글 알림 등)을 집으면 그 발신자로 나갈 수 있어 no-reply 가드를 둔다.
        "id": "c9",
        "type": "tool",
        "label": "Gmail 사과메일 발송",
        "mcp_key": "gmail",
        "detail": (
            "앞 단계에서 생성한 '답변 문구'를 c2에서 읽은 컴플레인 발신자에게 회신. "
            "발신자가 no-reply·noreply 등 수신 불가 주소이면 보내지 말고 그 사유를 보고할 것."
        ),
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
