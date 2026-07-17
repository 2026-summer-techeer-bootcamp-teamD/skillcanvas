"""스케줄러 감시 워크플로우 저장/조회/중지 테스트.

DB는 tmp 파일로 격리한다(실제 runner.db 오염 방지). db 모듈은 매 호출마다
config.DB_FILE로 커넥션을 열므로, config.DB_FILE만 tmp로 갈아끼우면 된다.
"""

import json

import pytest
from fastapi.testclient import TestClient

from app.core import config, db
from app.main import app


@pytest.fixture
def clean_db(tmp_path, monkeypatch):
    # db._connect()는 매 호출마다 config.DB_FILE을 읽으므로 이것만 tmp로 갈아끼우면 격리된다.
    monkeypatch.setattr(config, "DB_FILE", tmp_path / "test.db")
    yield


GRAPH = {
    "nodes": [{"id": "n1", "type": "trigger", "label": "시작"}],
    "edges": [],
}


# ── db 계층 ────────────────────────────────────────────
def test_no_watch_initially(clean_db):
    assert db.get_watch() is None


def test_save_and_get_watch(clean_db):
    db.save_watch(json.dumps(GRAPH), interval_sec=20)
    w = db.get_watch()
    assert w is not None
    assert w["enabled"] is True
    assert w["interval_sec"] == 20
    assert json.loads(w["graph_json"])["nodes"][0]["id"] == "n1"


def test_save_watch_upserts_single_row(clean_db):
    db.save_watch(json.dumps(GRAPH), 20)
    db.save_watch(json.dumps({"nodes": [], "edges": []}), 40)
    w = db.get_watch()
    assert w["interval_sec"] == 40  # 덮어씀
    assert json.loads(w["graph_json"])["nodes"] == []


def test_stop_watch_keeps_graph(clean_db):
    db.save_watch(json.dumps(GRAPH), 20)
    db.set_watch_enabled(False)
    w = db.get_watch()
    assert w["enabled"] is False
    assert w["graph_json"]  # 그래프는 보존


# ── API 계층 ───────────────────────────────────────────
def test_watch_api_start_status_stop(clean_db):
    client = TestClient(app)

    # 시작 전엔 저장 없음
    r = client.get("/watch")
    assert r.status_code == 200
    assert r.json() == {"watching": False, "saved": False}

    # 시작
    r = client.post("/watch", json={**GRAPH, "interval_sec": 15})
    assert r.status_code == 200
    body = r.json()
    assert body["watching"] is True
    assert body["saved"] is True
    assert body["interval_sec"] == 15
    assert body["node_count"] == 1

    # 조회
    assert client.get("/watch").json()["watching"] is True

    # 중지
    r = client.post("/watch/stop")
    assert r.json()["watching"] is False
    assert r.json()["saved"] is True  # 그래프는 남음


def test_watch_api_rejects_too_short_interval(clean_db):
    client = TestClient(app)
    r = client.post("/watch", json={**GRAPH, "interval_sec": 3})
    assert r.status_code == 422  # ge=10
