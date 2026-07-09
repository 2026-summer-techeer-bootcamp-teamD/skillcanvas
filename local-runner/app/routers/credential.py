"""A-6: POST /credential — 도구 API 키를 로컬 SQLite에 저장(서버로 전송 X)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core import db

router = APIRouter(tags=["키 저장"])


class CredentialIn(BaseModel):
    tool_key: str = ""
    secret: str = ""


@router.post("/credential", summary="도구 키 저장 (로컬 전용)")
def save_credential(payload: CredentialIn) -> dict:
    tool_key = payload.tool_key.strip()
    if not tool_key or not payload.secret:
        raise HTTPException(
            400,
            {"code": "CREDENTIAL_INVALID_INPUT", "message": "tool_key와 secret이 필요합니다"},
        )
    db.set_credential(tool_key, payload.secret)
    return {"ok": True, "tool_key": tool_key}  # secret은 응답에 노출하지 않음
