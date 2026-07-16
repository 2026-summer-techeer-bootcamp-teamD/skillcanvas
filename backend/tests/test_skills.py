"""스킬 API 테스트 — tests/test_workflows.py를 미러링. (API 명세서 5번)

핵심 = 보안 4종:
  ① 소유권은 토큰 유저로 판단  ② 비공개를 남이 조회/가져오기 → 404(숨김)
  ③ 남의 것 수정/삭제 → 403     ④ mine=true인데 토큰 없음 → 401

워크플로우와 차이: graph_json(dict) → content_md(str)
"""

from app.models.tool_catalog import ToolCatalog

BASE = "/api/v1/skills"


def _payload(name="sk", is_public=True):
    return {
        "name": name,
        "description": "설명",
        "content_md": "# SKILL.md 본문",  # ★ 워크플로우는 graph_json
        "tags": ["auto"],
        "is_public": is_public,
    }


def _create(client, auth, user="alice", **kw):
    r = client.post(BASE, json=_payload(**kw), headers=auth(user))
    assert r.status_code == 201, r.text
    return r.json()


# ── 발행·조회 ────────────────────────────────────────
def test_publish_and_get(client, auth):
    sk = _create(client, auth, name="cs-handler")
    assert sk["name"] == "cs-handler"
    assert sk["import_count"] == 0

    r = client.get(f"{BASE}/{sk['id']}", headers=auth("alice"))
    assert r.status_code == 200
    assert r.json()["content_md"] == "# SKILL.md 본문"


def test_owner_is_token_user(client, auth):
    # 소유자는 토큰에서 뽑은 유저 (요청 body로 안 받음)
    sk = _create(client, auth, user="alice")
    assert sk["owner"]["nickname"].startswith("user_") or sk["owner"]["id"]


# ── ② 비공개 숨김(404) ───────────────────────────────
def test_private_hidden_from_others_404(client, auth):
    sk = _create(client, auth, user="alice", is_public=False)
    # 남(bob)이 비공개 조회 → 404 (403 아님, 존재 자체를 숨김)
    r = client.get(f"{BASE}/{sk['id']}", headers=auth("bob"))
    assert r.status_code == 404
    # 소유자는 자기 비공개 조회 OK
    assert client.get(f"{BASE}/{sk['id']}", headers=auth("alice")).status_code == 200


# ── ③ 남의 것 수정/삭제(403) ─────────────────────────
def test_update_by_non_owner_403(client, auth):
    sk = _create(client, auth, user="alice")
    r = client.patch(f"{BASE}/{sk['id']}", json={"name": "해킹"}, headers=auth("bob"))
    assert r.status_code == 403


def test_update_by_owner_ok(client, auth):
    sk = _create(client, auth, user="alice")
    r = client.patch(f"{BASE}/{sk['id']}", json={"is_public": False}, headers=auth("alice"))
    assert r.status_code == 200
    assert r.json()["is_public"] is False


def test_delete_by_non_owner_403_owner_204(client, auth):
    sk = _create(client, auth, user="alice")
    assert client.delete(f"{BASE}/{sk['id']}", headers=auth("bob")).status_code == 403
    assert client.delete(f"{BASE}/{sk['id']}", headers=auth("alice")).status_code == 204


# ── ④ mine=true 인증 필요(401) ───────────────────────
def test_mine_requires_auth_401(client):
    r = client.get(f"{BASE}?mine=true")  # 토큰 없음
    assert r.status_code == 401


# ── 목록 필터 ────────────────────────────────────────
def test_list_shows_public_only_by_default(client, auth):
    _create(client, auth, user="alice", name="pub", is_public=True)
    _create(client, auth, user="alice", name="priv", is_public=False)
    names = [s["name"] for s in client.get(BASE).json()["items"]]
    assert "pub" in names and "priv" not in names


# ── limit 상한 (이슈 #115: used_mcps regex 스캔 비용 무제한 증폭 방지) ──
def test_list_limit_is_capped(client):
    assert client.get(BASE, params={"limit": 100}).status_code == 200
    assert client.get(BASE, params={"limit": 101}).status_code == 422


# ── 가져오기(import) ─────────────────────────────────
def test_import_increments_count(client, auth):
    sk = _create(client, auth, user="alice", is_public=True)
    r = client.post(f"{BASE}/{sk['id']}/import", headers=auth("bob"))
    assert r.status_code == 200
    assert r.json()["import_count"] == 1


def test_import_private_blocked_404(client, auth):
    sk = _create(client, auth, user="alice", is_public=False)
    r = client.post(f"{BASE}/{sk['id']}/import", headers=auth("bob"))
    assert r.status_code == 404


# ── used_mcps 추출 (이슈 #115) ───────────────────────
def test_list_includes_used_mcps_from_content(client, auth, db_session):
    # content_md에 카탈로그 key가 리터럴로 등장하면 목록에서 used_mcps로 추출된다
    db_session.add(
        ToolCatalog(
            key="__test_notion__",
            name="notion",
            description=None,
            key_required=False,
            key_issue_url=None,
            metadata_json=None,
            type="mcp",
            auth_owner="developer",
        )
    )
    db_session.commit()

    r = client.post(
        BASE,
        json={
            **_payload(name="mcp-skill"),
            "content_md": "1. **노션에 저장** (도구 · __test_notion__)",
        },
        headers=auth("alice"),
    )
    assert r.status_code == 201, r.text
    sk_id = r.json()["id"]

    items = client.get(f"{BASE}?mine=true", headers=auth("alice")).json()["items"]
    item = next(i for i in items if i["id"] == sk_id)
    assert item["used_mcps"] == ["__test_notion__"]


def test_publish_stores_validated_used_mcps(client, auth, db_session):
    # POST /skills의 used_mcps는 카탈로그에 실제 존재하는 key만 필터링되어 저장되고,
    # 목록에서는 content_md 재추출(레거시 폴백) 대신 저장된 값을 그대로 돌려준다.
    db_session.add(
        ToolCatalog(
            key="__test_slack__",
            name="slack",
            description=None,
            key_required=False,
            key_issue_url=None,
            metadata_json=None,
            type="mcp",
            auth_owner="developer",
        )
    )
    db_session.commit()

    r = client.post(
        BASE,
        json={
            **_payload(name="stored-mcp-skill"),
            "content_md": "1. **아무 도구도 언급 안 함**",  # 본문엔 key가 전혀 등장하지 않음
            "used_mcps": ["__test_slack__", "__fake_not_in_catalog__"],
        },
        headers=auth("alice"),
    )
    assert r.status_code == 201, r.text
    sk_id = r.json()["id"]

    items = client.get(f"{BASE}?mine=true", headers=auth("alice")).json()["items"]
    item = next(i for i in items if i["id"] == sk_id)
    # 카탈로그에 없는 키는 걸러지고, 저장된 값이 content_md 내용과 무관하게 그대로 반환된다
    assert item["used_mcps"] == ["__test_slack__"]
