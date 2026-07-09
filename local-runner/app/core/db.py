"""로컬 실행기 SQLite — 재시작에도 살아남아야 하는 상태 저장.

지금은 중복체크(processed)만. stdlib sqlite3(경량, 외부 의존성 X).
FastAPI가 요청을 스레드풀에서 처리하므로 매 작업마다 커넥션을 새로 연다.
"""

import sqlite3
from datetime import UTC, datetime

from app.core import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS processed (
    item_key     TEXT PRIMARY KEY,
    processed_at TEXT
);
"""


def _connect() -> sqlite3.Connection:
    config.DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_FILE)
    conn.executescript(_SCHEMA)  # IF NOT EXISTS라 매번 호출해도 안전(최초 1회만 생성)
    return conn


def is_processed(item_key: str) -> bool:
    """이미 처리 완료(중복)한 건인지."""
    conn = _connect()
    try:
        row = conn.execute("SELECT 1 FROM processed WHERE item_key = ?", (item_key,)).fetchone()
        return row is not None
    finally:
        conn.close()


def mark_processed(item_key: str) -> None:
    """처리 완료로 기록(중복이면 무시). output 노드가 호출."""
    conn = _connect()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO processed(item_key, processed_at) VALUES (?, ?)",
            (item_key, datetime.now(UTC).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def clear_processed() -> int:
    """중복체크 기록 전체 삭제(데모 리허설용). 삭제된 행 수 반환."""
    conn = _connect()
    try:
        n = conn.execute("DELETE FROM processed").rowcount
        conn.commit()
        return n
    finally:
        conn.close()
