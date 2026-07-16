"""워크플로우 API 테스트 — **다른 도메인(skills 등) 작성 시 이 파일을 참고**.

핵심 = 보안 4종:
  ① 소유권은 토큰 유저로 판단  ② 비공개를 남이 조회/가져오기 → 404(숨김)
  ③ 남의 것 수정/삭제 → 403     ④ mine=true인데 토큰 없음 → 401
"""

BASE = "/api/v1/workflows"


def _payload(name="wf", is_public=True):
    return {
        "name": name,
        "description": "설명",
        "graph_json": {"nodes": [], "edges": []},
        "tags": ["auto"],
        "is_public": is_public,
    }


def _create(client, auth, user="alice", **kw):
    r = client.post(BASE, json=_payload(**kw), headers=auth(user))
    assert r.status_code == 201, r.text
    return r.json()


# ── 발행·조회 ────────────────────────────────────────
def test_publish_and_get(client, auth):
    wf = _create(client, auth, name="cs-handler")
    assert wf["name"] == "cs-handler"
    assert wf["import_count"] == 0

    r = client.get(f"{BASE}/{wf['id']}", headers=auth("alice"))
    assert r.status_code == 200
    assert r.json()["graph_json"] == {"nodes": [], "edges": []}


def test_owner_is_token_user(client, auth):
    # 소유자는 토큰에서 뽑은 유저 (요청 body로 안 받음)
    wf = _create(client, auth, user="alice")
    assert wf["owner"]["nickname"].startswith("user_") or wf["owner"]["id"]


# ── ② 비공개 숨김(404) ───────────────────────────────
def test_private_hidden_from_others_404(client, auth):
    wf = _create(client, auth, user="alice", is_public=False)
    # 남(bob)이 비공개 조회 → 404 (403 아님, 존재 자체를 숨김)
    r = client.get(f"{BASE}/{wf['id']}", headers=auth("bob"))
    assert r.status_code == 404
    # 소유자는 자기 비공개 조회 OK
    assert client.get(f"{BASE}/{wf['id']}", headers=auth("alice")).status_code == 200


# ── ③ 남의 것 수정/삭제(403) ─────────────────────────
def test_update_by_non_owner_403(client, auth):
    wf = _create(client, auth, user="alice")
    r = client.patch(f"{BASE}/{wf['id']}", json={"name": "해킹"}, headers=auth("bob"))
    assert r.status_code == 403


def test_update_by_owner_ok(client, auth):
    wf = _create(client, auth, user="alice")
    r = client.patch(f"{BASE}/{wf['id']}", json={"is_public": False}, headers=auth("alice"))
    assert r.status_code == 200
    assert r.json()["is_public"] is False


def test_delete_by_non_owner_403_owner_204(client, auth):
    wf = _create(client, auth, user="alice")
    assert client.delete(f"{BASE}/{wf['id']}", headers=auth("bob")).status_code == 403
    assert client.delete(f"{BASE}/{wf['id']}", headers=auth("alice")).status_code == 204


# ── ④ mine=true 인증 필요(401) ───────────────────────
def test_mine_requires_auth_401(client):
    r = client.get(f"{BASE}?mine=true")  # 토큰 없음
    assert r.status_code == 401


# ── 목록 필터 ────────────────────────────────────────
def test_list_shows_public_only_by_default(client, auth):
    _create(client, auth, user="alice", name="pub", is_public=True)
    _create(client, auth, user="alice", name="priv", is_public=False)
    names = [w["name"] for w in client.get(BASE).json()["items"]]
    assert "pub" in names and "priv" not in names


# ── 가져오기(import) ─────────────────────────────────
def test_import_increments_count(client, auth):
    wf = _create(client, auth, user="alice", is_public=True)
    r = client.post(f"{BASE}/{wf['id']}/import", headers=auth("bob"))
    assert r.status_code == 200
    assert r.json()["import_count"] == 1


def test_import_private_blocked_404(client, auth):
    wf = _create(client, auth, user="alice", is_public=False)
    r = client.post(f"{BASE}/{wf['id']}/import", headers=auth("bob"))
    assert r.status_code == 404


# ── used_mcps 추출 (이슈 #115) ───────────────────────
def _seed_catalog(db_session, *keys: str) -> None:
    from app.models.tool_catalog import ToolCatalog

    for key in keys:
        db_session.add(
            ToolCatalog(
                key=key,
                name=key,
                description=None,
                key_required=False,
                key_issue_url=None,
                metadata_json=None,
                type="mcp",
                auth_owner="developer",
            )
        )
    db_session.commit()


def test_list_includes_used_mcps_from_graph(client, auth, db_session):
    # graph_json 노드의 data.mcpKey가 목록에서 used_mcps로 중복 없이 추출된다
    _seed_catalog(db_session, "__test_slack__", "__test_notion__")
    graph = {
        "nodes": [
            {"id": "n1", "data": {"mcpKey": "__test_slack__"}},
            {"id": "n2", "data": {"mcpKey": "__test_notion__"}},
            {"id": "n3", "data": {"mcpKey": "__test_slack__"}},  # 중복
            {"id": "n4", "data": {}},  # mcpKey 없음
        ],
        "edges": [],
    }
    r = client.post(
        BASE,
        json={**_payload(name="mcp-wf"), "graph_json": graph},
        headers=auth("alice"),
    )
    assert r.status_code == 201, r.text
    wf_id = r.json()["id"]

    items = client.get(f"{BASE}?mine=true", headers=auth("alice")).json()["items"]
    item = next(i for i in items if i["id"] == wf_id)
    assert item["used_mcps"] == ["__test_slack__", "__test_notion__"]


def test_list_filters_out_spoofed_mcp_key(client, auth, db_session):
    # graph_json은 검증 없이 저장되므로(자유 형식 dict), 카탈로그에 없는 mcpKey를
    # 임의로 심어도 used_mcps에는 반영되지 않아야 한다 (이슈 #115 워크플로우 스푸핑 수정).
    _seed_catalog(db_session, "__test_real__")
    graph = {
        "nodes": [
            {"id": "n1", "data": {"mcpKey": "__test_real__"}},
            {"id": "n2", "data": {"mcpKey": "__totally_made_up_tool__"}},
        ],
        "edges": [],
    }
    r = client.post(
        BASE,
        json={**_payload(name="spoof-wf"), "graph_json": graph},
        headers=auth("alice"),
    )
    assert r.status_code == 201, r.text
    wf_id = r.json()["id"]

    items = client.get(f"{BASE}?mine=true", headers=auth("alice")).json()["items"]
    item = next(i for i in items if i["id"] == wf_id)
    assert item["used_mcps"] == ["__test_real__"]
