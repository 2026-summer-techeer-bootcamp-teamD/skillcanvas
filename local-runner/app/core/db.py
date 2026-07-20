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
CREATE TABLE IF NOT EXISTS credentials (
    tool_key TEXT PRIMARY KEY,
    secret   TEXT
);
-- 스케줄러가 자동 실행할 '감시 워크플로우'. 실행기가 재시작해도 남아야 하므로 여기 저장.
-- 단일 행(id=1)만 둔다 — 한 번에 하나의 워크플로우만 감시(데모 범위).
CREATE TABLE IF NOT EXISTS watched_workflow (
    id           INTEGER PRIMARY KEY CHECK (id = 1),
    graph_json   TEXT NOT NULL,   -- {"nodes": [...], "edges": [...]}
    enabled      INTEGER NOT NULL DEFAULT 1,
    interval_sec INTEGER NOT NULL DEFAULT 30,
    updated_at   TEXT
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


def _norm_key(tool_key: str) -> str:
    """tool_key 정규화 — 카탈로그 키(예: 'notion')와 대소문자·공백 무관하게 매칭."""
    return tool_key.strip().lower()


def set_credential(tool_key: str, secret: str) -> None:
    """도구 키를 로컬에 저장(upsert). 같은 tool_key면 덮어씀.

    ⚠️ secret은 현재 **평문 저장**(로컬 데모 전용). runner.db는 gitignore(*.db)라
    커밋되지 않지만, DB 파일 접근 가능한 사용자/백업동기화 폴더엔 그대로 노출됨.
    → 암호화·파일권한(0600)은 후속 티켓(#35)에서.
    """
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO credentials(tool_key, secret) VALUES (?, ?) "
            "ON CONFLICT(tool_key) DO UPDATE SET secret = excluded.secret",
            (_norm_key(tool_key), secret),
        )
        conn.commit()
    finally:
        conn.close()


def get_credential(tool_key: str) -> str | None:
    """저장된 도구 키 조회(실행 시 MCP 주입용). 없으면 None."""
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT secret FROM credentials WHERE tool_key = ?", (_norm_key(tool_key),)
        ).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def save_watch(graph_json: str, interval_sec: int = 30) -> None:
    """감시 워크플로우 저장/갱신(upsert, enabled=1로 켬). 그래프는 JSON 문자열."""
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO watched_workflow(id, graph_json, enabled, interval_sec, updated_at) "
            "VALUES (1, ?, 1, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET "
            "graph_json = excluded.graph_json, enabled = 1, "
            "interval_sec = excluded.interval_sec, updated_at = excluded.updated_at",
            (graph_json, interval_sec, datetime.now(UTC).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def get_watch() -> dict | None:
    """저장된 감시 워크플로우 조회. 없으면 None.

    반환: {"graph_json": str, "enabled": bool, "interval_sec": int, "updated_at": str}
    """
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT graph_json, enabled, interval_sec, updated_at "
            "FROM watched_workflow WHERE id = 1"
        ).fetchone()
        if row is None:
            return None
        return {
            "graph_json": row[0],
            "enabled": bool(row[1]),
            "interval_sec": row[2],
            "updated_at": row[3],
        }
    finally:
        conn.close()


def set_watch_enabled(enabled: bool) -> None:
    """감시 on/off 토글. 저장된 워크플로우가 없으면 아무 것도 안 함."""
    conn = _connect()
    try:
        conn.execute(
            "UPDATE watched_workflow SET enabled = ?, updated_at = ? WHERE id = 1",
            (1 if enabled else 0, datetime.now(UTC).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def list_credential_keys() -> list[str]:
    """등록된 도구 키 목록(현황 조회용). secret은 절대 포함하지 않는다.

    빈/공백 secret은 제외한다 — 실행 시 그런 키는 못 쓰는데(no_key) 목록에 뜨면
    "연결됨"으로 잘못 보인다.
    """
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT tool_key FROM credentials "
            "WHERE secret IS NOT NULL AND TRIM(secret) != '' ORDER BY tool_key"
        ).fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()
