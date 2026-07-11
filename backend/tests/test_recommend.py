"""MCP 추천 API 테스트. (API 명세서 3-2)

Claude는 mock_claude 픽스처로 목킹 → 실제 호출 안 함(빠르고 무료).

검증 포인트:
  ① 인증 필요 → 토큰 없으면 401
  ② 정상 응답 → 200
  ③ 카탈로그에 없는 mcps는 필터링 (없는 도구 지어내기 방지)
  ④ AI 응답이 이상하면 500이 아니라 422 RECOMMEND_FAILED (명세 규정)
  ⑤ Claude 호출 실패 → 502 (llm.py가 처리)
"""

from fastapi import HTTPException

BASE = "/api/v1/recommend"


# ── ① 인증 필요(401) ─────────────────────────────────
def test_requires_auth_401(client):
    r = client.post(BASE, json={"text": "회의록 정리"})  # 토큰 없음
    assert r.status_code == 401


# ── ② 정상 응답(200) ─────────────────────────────────
def test_recommend_ok(client, auth, mock_claude):
    mock_claude(
        return_value={"skill": "meeting-notes", "description": "회의록 정리", "mcps": []}
    )
    r = client.post(BASE, json={"text": "회의록 정리해줘"}, headers=auth("alice"))
    assert r.status_code == 200
    body = r.json()
    assert body["skill"] == "meeting-notes"
    assert body["mcps"] == []


# ── ③ 카탈로그 밖 도구는 필터링 ──────────────────────
def test_unknown_mcp_filtered_out(client, auth, mock_claude):
    # Claude가 카탈로그에 없는 도구를 지어내도 응답에서 걸러져야 함
    mock_claude(
        return_value={
            "skill": "x",
            "description": "d",
            "mcps": ["존재하지_않는_도구"],
        }
    )
    r = client.post(BASE, json={"text": "아무거나"}, headers=auth("alice"))
    assert r.status_code == 200
    assert r.json()["mcps"] == []


# ── ④ AI 응답 이상 → 422 RECOMMEND_FAILED ────────────
def test_missing_field_422(client, auth, mock_claude):
    # skill 키가 아예 없음
    mock_claude(return_value={"description": "d", "mcps": []})
    r = client.post(BASE, json={"text": "아무거나"}, headers=auth("alice"))
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "RECOMMEND_FAILED"


def test_null_field_422(client, auth, mock_claude):
    # 키는 있는데 값이 null → 500 아니라 422여야 함
    mock_claude(return_value={"skill": None, "description": "d", "mcps": []})
    r = client.post(BASE, json={"text": "아무거나"}, headers=auth("alice"))
    assert r.status_code == 422


def test_wrong_type_field_422(client, auth, mock_claude):
    # skill이 문자열이 아니라 숫자 → 422
    mock_claude(return_value={"skill": 123, "description": "d", "mcps": []})
    r = client.post(BASE, json={"text": "아무거나"}, headers=auth("alice"))
    assert r.status_code == 422


def test_mcps_not_list_handled(client, auth, mock_claude):
    # mcps가 리스트가 아니라 null → TypeError(500) 안 나고 빈 배열로 처리
    mock_claude(return_value={"skill": "x", "description": "d", "mcps": None})
    r = client.post(BASE, json={"text": "아무거나"}, headers=auth("alice"))
    assert r.status_code == 200
    assert r.json()["mcps"] == []


# ── ⑤ Claude 호출 실패 → 502 ─────────────────────────
def test_claude_unavailable_502(client, auth, mock_claude):
    mock_claude(
        raise_exc=HTTPException(
            502, {"code": "CLAUDE_UNAVAILABLE", "message": "Claude 호출에 실패했습니다"}
        )
    )
    r = client.post(BASE, json={"text": "아무거나"}, headers=auth("alice"))
    assert r.status_code == 502
