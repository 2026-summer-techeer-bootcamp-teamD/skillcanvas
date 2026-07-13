"""도구 카탈로그 API 테스트. (API 명세서 2-1)

카탈로그는 시드 스크립트(app/seed_tools)로 채워지는 lookup 테이블이라
API로 만들 방법이 없음 → db_session에 직접 넣고 조회만 검증한다.

검증 포인트:
  ① 인증 불필요(공개 목록)  ② 페이지네이션(limit/offset)  ③ id 오름차순 정렬
"""

from app.models.tool_catalog import ToolCatalog

BASE = "/api/v1/tool-catalog"


def _make(key: str) -> ToolCatalog:
    return ToolCatalog(
        key=key,
        name=key,
        description=None,
        key_required=False,
        key_issue_url=None,
        metadata_json=None,
        type="mcp",
        auth_owner="developer",
    )


def test_list_no_auth_required(client, db_session):
    db_session.add(_make("slack"))
    db_session.commit()

    r = client.get(BASE)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    assert any(item["key"] == "slack" for item in body["items"])


def test_pagination(client, db_session):
    for key in ("t1", "t2", "t3"):
        db_session.add(_make(key))
    db_session.commit()

    r = client.get(BASE, params={"limit": 1, "offset": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["limit"] == 1
    assert body["offset"] == 1
    assert len(body["items"]) == 1
    assert body["total"] >= 3


def test_items_ordered_by_id_asc(client, db_session):
    db_session.add(_make("first"))
    db_session.commit()
    db_session.add(_make("second"))
    db_session.commit()

    items = client.get(BASE, params={"limit": 100}).json()["items"]
    ids = [item["id"] for item in items]
    assert ids == sorted(ids)
