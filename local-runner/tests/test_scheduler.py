"""스케줄러 자동 실행 로직 테스트.

실제 IMAP·Claude는 안 부른다 — probe(메일 조회)와 start_run(실행)을 목킹하고,
'새 메일이면 실행 / 중복이면 스킵 / 메일 없으면 아무 것도 안 함'만 검증한다.
async 함수라 asyncio.run으로 구동(별도 플러그인 불필요).
"""

import asyncio
import json

import pytest

from app.core import config, db, scheduler

GRAPH = {"nodes": [{"id": "n1", "type": "trigger", "label": "시작"}], "edges": []}


@pytest.fixture
def clean_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_FILE", tmp_path / "test.db")
    yield


def _watch_row() -> dict:
    return {"graph_json": json.dumps(GRAPH), "enabled": True, "interval_sec": 15}


def test_new_mail_triggers_run(clean_db, monkeypatch):
    calls = []
    monkeypatch.setattr(scheduler, "probe_latest_unseen_mail_id", lambda: "<msg-1@x>")
    monkeypatch.setattr(
        scheduler,
        "start_run",
        lambda nodes, edges, item_key: calls.append((nodes, edges, item_key)),
    )

    result = asyncio.run(scheduler._run_if_new_mail(_watch_row()))

    assert result == "<msg-1@x>"
    assert len(calls) == 1
    nodes, edges, item_key = calls[0]
    assert nodes[0]["id"] == "n1"
    assert item_key == "<msg-1@x>"
    assert db.is_processed("<msg-1@x>")  # 실행하며 처리기록 남음


def test_same_mail_not_run_twice(clean_db, monkeypatch):
    calls = []
    monkeypatch.setattr(scheduler, "probe_latest_unseen_mail_id", lambda: "<msg-1@x>")
    monkeypatch.setattr(
        scheduler, "start_run", lambda nodes, edges, item_key: calls.append(item_key)
    )

    asyncio.run(scheduler._run_if_new_mail(_watch_row()))  # 1회차 실행
    result = asyncio.run(scheduler._run_if_new_mail(_watch_row()))  # 2회차 = 중복

    assert result is None
    assert len(calls) == 1  # 두 번째는 실행 안 됨


def test_no_mail_no_run(clean_db, monkeypatch):
    calls = []
    monkeypatch.setattr(scheduler, "probe_latest_unseen_mail_id", lambda: None)
    monkeypatch.setattr(
        scheduler, "start_run", lambda nodes, edges, item_key: calls.append(item_key)
    )

    result = asyncio.run(scheduler._run_if_new_mail(_watch_row()))

    assert result is None
    assert calls == []


def test_bad_graph_json_skips(clean_db, monkeypatch):
    calls = []
    monkeypatch.setattr(scheduler, "probe_latest_unseen_mail_id", lambda: "<msg-2@x>")
    monkeypatch.setattr(
        scheduler, "start_run", lambda nodes, edges, item_key: calls.append(item_key)
    )

    result = asyncio.run(scheduler._run_if_new_mail({"graph_json": "{not json", "enabled": True}))

    assert result is None
    assert calls == []
    # 파싱 실패라도 중복기록은 남아(같은 깨진 메일로 매 폴링마다 재시도하지 않게)
    assert db.is_processed("<msg-2@x>")


def test_gmail_login_parses_stored_json(clean_db):
    db.set_credential(
        "gmail", json.dumps({"MCP_EMAIL_ADDRESS": "a@b.com", "MCP_EMAIL_PASSWORD": "pw"})
    )
    assert scheduler._gmail_login() == ("a@b.com", "pw")


def test_gmail_login_none_when_missing(clean_db):
    assert scheduler._gmail_login() is None
