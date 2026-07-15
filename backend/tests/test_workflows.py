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
