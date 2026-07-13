"""공통 의존성 (Depends로 주입).

인증 = Clerk. 프론트가 보낸 Clerk 세션 JWT를 검증해 "현재 유저"를 만든다.

토큰 판별(하이브리드):
- **JWT 모양(점 2개)** → 항상 Clerk 서명 검증(JWKS). 실제 로그인 경로.
- 그 외 문자열(예: 테스트의 "alice") → `AUTH_DEV_MODE=True`일 때만 그대로 유저 식별자로 인정(개발 STUB).
  → 팀원 테스트/로컬은 기존처럼 동작하고, 실제 프론트 JWT는 안전하게 검증된다.

HTTPBearer를 쓰므로 Swagger 우측 상단 "Authorize 🔓" 버튼으로 토큰을 넣어 테스트할 수 있다.
"""

from __future__ import annotations

import httpx
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.user import User

# auto_error=False → 토큰이 없어도 예외를 내지 않고 None을 넘김(선택 인증용).
bearer_scheme = HTTPBearer(auto_error=False)

_clerk_sdk = None


def _clerk():
    """Clerk SDK 지연 초기화 (STUB 경로만 쓰면 SDK 없이도 동작)."""
    global _clerk_sdk
    if _clerk_sdk is None:
        from clerk_backend_api import Clerk

        _clerk_sdk = Clerk(bearer_auth=settings.clerk_secret_key)
    return _clerk_sdk


def _looks_like_jwt(token: str) -> bool:
    return token.count(".") == 2


def _admin_emails() -> set[str]:
    return {e.strip().lower() for e in settings.admin_emails.split(",") if e.strip()}


def _verify_clerk_jwt(token: str, request: Request) -> dict | None:
    """실제 Clerk 세션 JWT 검증 → payload(dict) 또는 None."""
    from clerk_backend_api.security.types import AuthenticateRequestOptions

    parties = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    proxy_req = httpx.Request(
        request.method,
        str(request.url),
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        state = _clerk().authenticate_request(
            proxy_req, AuthenticateRequestOptions(authorized_parties=parties)
        )
    except Exception:
        return None
    return state.payload if state.is_signed_in else None


def _fetch_clerk_profile(clerk_user_id: str) -> tuple[str | None, str | None]:
    """Clerk에서 기본 이메일 + 닉네임(unsafeMetadata) 조회. 실패 시 (None, None)."""
    try:
        u = _clerk().users.get(user_id=clerk_user_id)
    except Exception:
        return None, None

    email = None
    primary_id = getattr(u, "primary_email_address_id", None)
    for e in getattr(u, "email_addresses", None) or []:
        if getattr(e, "id", None) == primary_id:
            email = getattr(e, "email_address", None)
            break

    meta = getattr(u, "unsafe_metadata", None) or {}
    nickname = meta.get("nickname") if isinstance(meta, dict) else None
    return email, nickname


def _unique_nickname(db: Session, base: str) -> str:
    base = (base or "user")[:45]
    nick = base
    i = 1
    while db.scalar(select(User.id).where(User.nickname == nick)):
        nick = f"{base}_{i}"
        i += 1
    return nick


def _provision_user(
    db: Session, clerk_user_id: str, email: str | None, nickname: str | None
) -> User:
    is_admin = email is not None and email.lower() in _admin_emails()
    nick = _unique_nickname(db, nickname or f"user_{clerk_user_id[:12]}")
    user = User(clerk_user_id=clerk_user_id, nickname=nick, is_admin=is_admin)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """토큰이 있으면 유저 반환(첫 로그인은 자동 생성), 없으면 None.

    공개 목록처럼 인증이 선택인 곳에서 사용.
    """
    if credentials is None:
        return None

    token = credentials.credentials
    real_login = _looks_like_jwt(token)

    if real_login:
        payload = _verify_clerk_jwt(token, request)
        if payload is None or not payload.get("sub"):
            return None
        clerk_user_id = payload["sub"]
    elif settings.auth_dev_mode:
        clerk_user_id = token  # 개발 STUB (토큰 = 식별자)
    else:
        return None

    user = db.scalar(select(User).where(User.clerk_user_id == clerk_user_id))
    if user is None:
        # 실제 로그인만 Clerk에서 이메일/닉네임 조회(관리자 판별·닉네임 반영).
        email, nickname = _fetch_clerk_profile(clerk_user_id) if real_login else (None, None)
        user = _provision_user(db, clerk_user_id, email, nickname)
    return user


def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    """인증 필수 엔드포인트용. 토큰 없으면 401."""
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={"code": "AUTH_UNAUTHORIZED", "message": "인증이 필요합니다"},
        )
    return user
