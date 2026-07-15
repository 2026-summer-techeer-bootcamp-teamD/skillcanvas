"""자연어 조립/매핑 API 테스트. (API 명세서 3장: 3-1 assemble / 3-3 map-node)

Claude는 mock_claude 픽스처로 목킹 → 실제 호출 안 함(빠르고 무료).
conftest.py의 mock_claude가 app.routers.assemble.ask_claude_json을 이미 패치해준다.

검증 포인트 (assemble/map-node 공통):
  ① 인증 필요 → 토큰 없으면 401
  ② 정상 응답 → 200
  ③ 카탈로그에 없는 mcp는 필터링 (없는 도구 지어내기 방지)
  ④ AI 응답 구조가 스키마와 안 맞으면 422 {도메인}_FAILED (500 아님)
  ⑤ Claude 호출 실패 → 502 (llm.py가 처리)
"""

from fastapi import HTTPException

ASSEMBLE = "/api/v1/assemble"
MAP_NODE = "/api/v1/map-node"

VALID_ASSEMBLE_RESULT = {
    "name": "meeting-notes-workflow",
    "nodes": [
        {"id": "n1", "type": "trigger", "label": "시작"},
        {"id": "n2", "type": "tool", "label": "회의록 정리"},
    ],
    "edges": [{"from": "n1", "to": "n2"}],
    "used_mcps": [],
}


# ── 3-1. 워크플로우 자동생성 (/assemble) ─────────────────


def test_assemble_requires_auth_401(client):
    r = client.post(ASSEMBLE, json={"text": "회의록 정리 워크플로우 만들어줘"})  # 토큰 없음
    assert r.status_code == 401


def test_assemble_ok(client, auth, mock_claude):
    mock_claude(return_value=VALID_ASSEMBLE_RESULT)
    r = client.post(
        ASSEMBLE, json={"text": "회의록 정리 워크플로우 만들어줘"}, headers=auth("alice")
    )
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "meeting-notes-workflow"
    assert len(body["nodes"]) == 2
    assert body["edges"][0] == {"from": "n1", "to": "n2"}


def test_assemble_unknown_mcp_filtered_out(client, auth, mock_claude):
    # Claude가 카탈로그에 없는 도구를 지어내도 used_mcps에서 걸러져야 함
    mock_claude(return_value={**VALID_ASSEMBLE_RESULT, "used_mcps": ["존재하지_않는_도구"]})
    r = client.post(ASSEMBLE, json={"text": "아무거나"}, headers=auth("alice"))
    assert r.status_code == 200
    assert r.json()["used_mcps"] == []


def test_assemble_missing_field_422(client, auth, mock_claude):
    # name 키가 아예 없음 → pydantic ValidationError → 422 ASSEMBLE_FAILED
    mock_claude(return_value={"nodes": [], "edges": [], "used_mcps": []})
    r = client.post(ASSEMBLE, json={"text": "아무거나"}, headers=auth("alice"))
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "ASSEMBLE_FAILED"


def test_assemble_wrong_type_field_422(client, auth, mock_claude):
    # nodes가 리스트가 아니라 문자열 → 422
    mock_claude(return_value={**VALID_ASSEMBLE_RESULT, "nodes": "이상함"})
    r = client.post(ASSEMBLE, json={"text": "아무거나"}, headers=auth("alice"))
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "ASSEMBLE_FAILED"


def test_assemble_claude_unavailable_502(client, auth, mock_claude):
    mock_claude(
        raise_exc=HTTPException(
            502, {"code": "CLAUDE_UNAVAILABLE", "message": "Claude 호출에 실패했습니다"}
        )
    )
    r = client.post(ASSEMBLE, json={"text": "아무거나"}, headers=auth("alice"))
    assert r.status_code == 502


# ── 3-3. 노드 자연어 편집/매핑 (/map-node) ────────────────


def _map_node_payload(instruction: str = "이 노드를 슬랙 알림으로 바꿔줘") -> dict:
    return {
        "node": {"type": "tool", "label": "이메일 보내기", "detail": None},
        "instruction": instruction,
    }


def test_map_node_requires_auth_401(client):
    r = client.post(MAP_NODE, json=_map_node_payload())  # 토큰 없음
    assert r.status_code == 401


def test_map_node_ok(client, auth, mock_claude):
    mock_claude(
        return_value={
            "node": {"type": "tool", "label": "슬랙 알림 보내기", "detail": None},
            "mcp_added": None,
        }
    )
    r = client.post(MAP_NODE, json=_map_node_payload(), headers=auth("alice"))
    assert r.status_code == 200
    assert r.json()["node"]["label"] == "슬랙 알림 보내기"


def test_map_node_unknown_mcp_added_dropped(client, auth, mock_claude):
    # 카탈로그에 없는 key를 mcp_added로 내면 null로 무시돼야 함
    mock_claude(
        return_value={
            "node": {"type": "tool", "label": "슬랙 알림 보내기", "detail": None},
            "mcp_added": "존재하지_않는_도구",
        }
    )
    r = client.post(MAP_NODE, json=_map_node_payload(), headers=auth("alice"))
    assert r.status_code == 200
    assert r.json()["mcp_added"] is None


def test_map_node_missing_field_422(client, auth, mock_claude):
    # node 키가 아예 없음 → 422 MAP_NODE_FAILED
    mock_claude(return_value={"mcp_added": None})
    r = client.post(MAP_NODE, json=_map_node_payload(), headers=auth("alice"))
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "MAP_NODE_FAILED"


def test_map_node_claude_unavailable_502(client, auth, mock_claude):
    mock_claude(
        raise_exc=HTTPException(
            502, {"code": "CLAUDE_UNAVAILABLE", "message": "Claude 호출에 실패했습니다"}
        )
    )
    r = client.post(MAP_NODE, json=_map_node_payload(), headers=auth("alice"))
    assert r.status_code == 502
