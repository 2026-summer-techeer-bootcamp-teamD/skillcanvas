"""키 저장 시 부족한 값을 대신 알아내 채운다.

왜 필요한가:
  텔레그램은 봇 토큰만으론 못 보내고 chat_id(받을 사람)가 있어야 한다. 그런데 chat_id는
  발급 화면 어디에도 없고, 유저가 직접
      https://api.telegram.org/bot<토큰>/getUpdates
  를 열어 result[0].message.chat.id 를 찾아야 한다. 일반 사용자에게 JSON을 열어 필드를
  찾으라는 건 무리고, 상품화하면 여기서 이탈한다.
  → 토큰만 받고 **우리가 대신 조회해서** 채운다. 입력칸이 2개에서 1개로 준다.

왜 저장 시점인가:
  유저가 모달에서 즉시 피드백을 받을 수 있고("/start 를 먼저 눌러주세요"), 워크플로우를
  실행할 때마다 텔레그램 API를 또 부르지 않아도 된다.

의존성 없이 stdlib urllib만 쓴다.
"""

import json
import urllib.error
import urllib.request


class ResolveError(Exception):
    """자동 조회 실패 — 사용자가 고칠 수 있게 사유를 그대로 전달한다."""


def _get_json(url: str, timeout: int = 10) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            body = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")  # 401 등에도 사유 JSON이 담겨 온다
    except (urllib.error.URLError, TimeoutError) as e:
        raise ResolveError(f"텔레그램 서버에 연결하지 못했습니다: {e}") from e
    try:
        return json.loads(body)
    except (json.JSONDecodeError, ValueError) as e:
        raise ResolveError(f"응답을 해석하지 못했습니다: {body[:120]}") from e


def _resolve_telegram(secret: str) -> dict[str, str]:
    """봇 토큰 → {BOT_TELEGRAM_TOKEN, BOT_TELEGRAM_CHAT_ID}.

    이미 JSON으로 chat_id까지 넣었으면 존중한다(채널 ID를 직접 지정하려는 경우).
    """
    try:
        parsed = json.loads(secret)
    except (json.JSONDecodeError, ValueError):
        parsed = None

    if isinstance(parsed, dict):
        token = str(parsed.get("BOT_TELEGRAM_TOKEN", "")).strip()
        chat_id = str(parsed.get("BOT_TELEGRAM_CHAT_ID", "")).strip()
        if token and chat_id:  # 둘 다 직접 넣었으면 그대로
            return {"BOT_TELEGRAM_TOKEN": token, "BOT_TELEGRAM_CHAT_ID": chat_id}
    else:
        token = secret.strip()

    if not token:
        raise ResolveError("봇 토큰이 비어 있습니다")

    me = _get_json(f"https://api.telegram.org/bot{token}/getMe")
    if not me.get("ok"):
        raise ResolveError(
            "봇 토큰이 유효하지 않습니다. @BotFather 가 /newbot 끝에 알려준 값을 그대로 붙여넣어 주세요."
        )
    bot_name = (me.get("result") or {}).get("username") or "봇"

    updates = _get_json(f"https://api.telegram.org/bot{token}/getUpdates")
    if not updates.get("ok"):
        # webhook이 걸려 있으면 getUpdates가 막힌다 — 그 사유가 description에 온다
        raise ResolveError(f"chat_id 조회 실패: {updates.get('description') or updates}")

    chats: list[str] = []
    for u in updates.get("result") or []:
        msg = u.get("message") or u.get("channel_post") or {}
        cid = (msg.get("chat") or {}).get("id")
        if cid is not None and str(cid) not in chats:
            chats.append(str(cid))

    if not chats:
        raise ResolveError(
            f"@{bot_name} 와의 대화를 아직 시작하지 않았습니다. "
            "텔레그램에서 봇을 검색해 /start 를 눌러주세요. "
            "(이미 눌렀다면 아무 메시지나 한 번 더 보낸 뒤 다시 저장해 주세요)"
        )

    # 여러 대화가 잡히면 가장 최근 것 — 방금 /start 를 누른 대화가 이쪽이다.
    return {"BOT_TELEGRAM_TOKEN": token, "BOT_TELEGRAM_CHAT_ID": chats[-1]}


# tool_key → 저장 전에 값을 채워주는 함수. 없으면 입력값을 그대로 저장한다.
RESOLVERS = {"telegram": _resolve_telegram}


def resolve(tool_key: str, secret: str) -> str:
    """저장할 최종 secret 문자열. 리졸버가 있으면 부족한 값을 채워 JSON으로 돌려준다."""
    fn = RESOLVERS.get(tool_key)
    if not fn:
        return secret
    return json.dumps(fn(secret), ensure_ascii=False)
