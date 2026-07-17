"""스케줄러 — 저장된 감시 워크플로우를 백그라운드에서 자동 실행.

실행기가 켜져 있는 동안 N초마다 gmail INBOX의 새(안읽은) 메일을 **가볍게** 확인하고
(stdlib imaplib, Claude 안 부름), 처음 보는 메일이면 저장된 워크플로우를 자동 실행한다.
중복 실행은 메일 Message-ID를 item_key로 processed 테이블에 기록해 막는다.

"친구는 실행 버튼을 안 누른다" — 켜두기만 하면 새 메일에 알아서 반응하는 자동화의 마지막 조각.
"""

import asyncio
import email
import imaplib
import json
import logging

from app.core import db, mcp
from app.engine.runner import start_run

log = logging.getLogger("skillcanvas.scheduler")

_IDLE_INTERVAL = 30  # 감시가 꺼져 있을 때 '켜졌는지' 다시 확인하는 주기(초)
_IMAP_TIMEOUT = 10


def _gmail_login() -> tuple[str, str] | None:
    """저장된 gmail 키에서 (이메일, 앱비밀번호)를 꺼낸다. 없거나 형식이 틀리면 None."""
    secret = db.get_credential("gmail")
    if not secret:
        return None
    try:
        parsed = json.loads(secret)
        addr = str(parsed["MCP_EMAIL_ADDRESS"]).strip()
        pw = str(parsed["MCP_EMAIL_PASSWORD"]).strip()
    except (json.JSONDecodeError, KeyError, TypeError):
        return None
    return (addr, pw) if addr and pw else None


def probe_latest_unseen_mail_id() -> str | None:
    """gmail INBOX에서 가장 최근 '안읽은' 메일의 Message-ID를 IMAP로 가볍게 조회.

    새 메일 없음 / 키 없음 / 오류면 None. Claude를 부르지 않아 폴링마다 싸게 돈다.
    BODY.PEEK라 메일을 '읽음'으로 바꾸지 않는다(워크플로우가 실제로 읽기 전까지 안 읽음 유지).
    """
    creds = _gmail_login()
    if not creds:
        return None
    addr, pw = creds
    host = mcp.MCP_SERVERS["gmail"]["static_env"]["MCP_EMAIL_IMAP_HOST"]
    imap = None
    try:
        imap = imaplib.IMAP4_SSL(host, timeout=_IMAP_TIMEOUT)
        imap.login(addr, pw)
        imap.select("INBOX")
        typ, data = imap.search(None, "UNSEEN")
        if typ != "OK" or not data or not data[0]:
            return None
        latest = data[0].split()[-1]
        typ, msg = imap.fetch(latest, "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])")
        if typ != "OK" or not msg or not isinstance(msg[0], tuple):
            return None
        header = msg[0][1].decode("utf-8", "replace")
        msgid = email.message_from_string(header).get("Message-ID", "").strip()
        return msgid or None
    except Exception as e:  # noqa: BLE001 — 폴링은 어떤 IMAP 오류에도 죽으면 안 된다
        log.warning("IMAP 조회 실패: %s", e)
        return None
    finally:
        if imap is not None:
            try:
                imap.logout()
            except Exception:  # noqa: BLE001
                pass


async def _run_if_new_mail(w: dict) -> str | None:
    """새 메일이면 저장된 워크플로우를 실행하고 그 Message-ID를 반환. 아니면 None.

    IMAP 조회·start_run은 블로킹이라 스레드풀에서 돌려 이벤트 루프를 막지 않는다.
    실행 '전에' 먼저 processed에 기록 — 폴링이 겹치거나 실행이 길어도 같은 메일을
    두 번 실행하지 않게 한다(데모에서 중복 발송/기록은 치명적).
    """
    loop = asyncio.get_event_loop()
    msgid = await loop.run_in_executor(None, probe_latest_unseen_mail_id)
    if not msgid or db.is_processed(msgid):
        return None
    db.mark_processed(msgid)
    try:
        graph = json.loads(w["graph_json"])
    except (json.JSONDecodeError, TypeError):
        log.warning("감시 그래프 파싱 실패 — 건너뜀")
        return None
    nodes, edges = graph.get("nodes", []), graph.get("edges", [])
    log.info("새 메일 감지(%s) → 워크플로우 자동 실행", msgid)
    result = await loop.run_in_executor(None, start_run, nodes, edges, msgid)
    r = result or {}
    # 실행이 끝났는지·어디서 멈췄는지 남긴다. status=awaiting_approval이면 승인 게이트에
    # 걸린 것 — 자동 실행은 스스로 승인 못 하므로 브라우저에서 승인해야 이어진다.
    log.info(
        "자동 실행 결과: status=%s, %d단계 완료",
        r.get("status"),
        len(r.get("results", [])),
    )
    return msgid


async def poll_loop() -> None:
    """감시 폴링 루프. FastAPI lifespan에서 백그라운드 태스크로 띄운다.

    어떤 tick 오류에도 루프는 살아있어야 하므로(데모 중 한 번 삐끗해도 계속 돌게)
    예외를 삼키고 다음 주기로 넘어간다. 취소(CancelledError)만 위로 올려 깔끔히 종료.
    """
    log.info("스케줄러 폴링 시작")
    while True:
        interval = _IDLE_INTERVAL
        try:
            w = db.get_watch()
            if w and w["enabled"]:
                interval = w["interval_sec"]
                await _run_if_new_mail(w)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            log.warning("폴링 tick 오류: %s", e)
        await asyncio.sleep(interval)
