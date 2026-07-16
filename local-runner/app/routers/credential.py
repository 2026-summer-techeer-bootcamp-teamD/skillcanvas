"""A-6: POST /credential — 도구 API 키를 로컬 SQLite에 저장(서버로 전송 X).

도구에 따라 저장 전에 부족한 값을 대신 채운다(예: 텔레그램은 봇 토큰만 받고
chat_id를 getUpdates로 조회). core/resolvers.py 참고.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core import db, resolvers

router = APIRouter(tags=["키 저장"])


class CredentialIn(BaseModel):
    tool_key: str = ""
    secret: str = ""


@router.post("/credential", summary="도구 키 저장 (로컬 전용)")
def save_credential(payload: CredentialIn) -> dict:
    # pydantic 기본 422 대신 명세 규약의 400을 내려고 수동 검증
    tool_key = payload.tool_key.strip().lower()  # db 저장 형태와 일치(정규화)
    if not tool_key or not payload.secret.strip():  # 공백-only도 거부
        raise HTTPException(
            400,
            {"code": "CREDENTIAL_INVALID_INPUT", "message": "tool_key와 secret이 필요합니다"},
        )
    # 부족한 값 자동 채우기(텔레그램 chat_id 등). 실패 사유는 사용자가 고칠 수 있게 그대로 전달.
    try:
        secret = resolvers.resolve(tool_key, payload.secret)
    except resolvers.ResolveError as e:
        raise HTTPException(400, {"code": "CREDENTIAL_RESOLVE_FAILED", "message": str(e)}) from e

    db.set_credential(tool_key, secret)
    return {"ok": True, "tool_key": tool_key}  # secret은 응답에 노출하지 않음


@router.get("/credentials", summary="등록된 도구 키 목록 (secret 미포함)")
def list_credentials() -> dict:
    """프론트가 '키가 이미 들어갔는지'를 알기 위한 조회.

    이게 없으면 저장 후에도 "키 연결 필요" 패널이 그대로 떠 있어 넣었는지 확인이 안 된다.
    MyWorld(키 현황)와 AutoFlow(노드 편집 패널)가 이 API를 공유한다.
    secret은 절대 내보내지 않는다 — key 목록만.
    """
    return {"tool_keys": db.list_credential_keys()}
