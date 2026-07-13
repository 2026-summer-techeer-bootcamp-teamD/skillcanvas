"""태그 API 테스트. (API 명세서 6-1)

검증 포인트:
  ① 인증 불필요(공개 목록)
  ② 워크플로우·스킬에 실제로 연결된 태그만 반환 (연결 없는 태그는 숨김)
  ③ 이름 오름차순 정렬
"""

from app.models.master_tag import MasterTag

BASE = "/api/v1/tags"


def _create_workflow(client, auth, tags, user="alice"):
    payload = {
        "name": "wf",
        "description": "설명",
        "graph_json": {"nodes": [], "edges": []},
        "tags": tags,
        "is_public": True,
    }
    r = client.post("/api/v1/workflows", json=payload, headers=auth(user))
    assert r.status_code == 201, r.text
    return r.json()


def test_list_tags_no_auth_required(client):
    r = client.get(BASE)
    assert r.status_code == 200
    assert "items" in r.json() and "total" in r.json()


def test_unused_tag_hidden(client, auth, db_session):
    # 워크플로우에 연결된 "used"만 노출되고, 아무 데도 안 걸린 "unused"는 숨겨져야 함
    _create_workflow(client, auth, tags=["__test_used__"])
    db_session.add(MasterTag(name="__test_unused__"))
    db_session.commit()

    names = [t["name"] for t in client.get(BASE).json()["items"]]
    assert "__test_used__" in names
    assert "__test_unused__" not in names


def test_tags_sorted_by_name(client, auth):
    _create_workflow(client, auth, tags=["zzz", "aaa"])
    names = [t["name"] for t in client.get(BASE).json()["items"]]
    assert names.index("aaa") < names.index("zzz")
