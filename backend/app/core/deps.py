"""공통 의존성 (Depends로 주입).

인증 = Clerk. 여기서 토큰을 검증해 "현재 유저"를 만들어준다.
※ 지금은 **개발용 STUB** — 실제로는 Clerk JWT를 검증해야 한다(아래 TODO).
"""

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.user import User


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return authorization.split(" ", 1)[1].strip()


def get_optional_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    """토큰이 있으면 유저 반환(없으면 첫 로그인으로 간주해 생성), 없으면 None.

    공개 목록처럼 인증이 선택인 곳에서 사용.
    """
    token = _extract_bearer(authorization)
    if not token:
        return None

    # TODO(인증): 실제로는 Clerk JWT를 검증해 clerk_user_id를 얻어야 한다.
    #   from clerk_backend_api import ...  또는 JWKS로 토큰 서명 검증.
    #   지금은 개발 STUB — 토큰 문자열을 그대로 clerk_user_id로 간주(로컬 테스트용).
    clerk_user_id = token

    user = db.scalar(select(User).where(User.clerk_user_id == clerk_user_id))
    if user is None:
        # 첫 로그인 자동 생성. nickname은 UNIQUE라 충돌 없는 기본값 부여(이후 사용자가 수정).
        user = User(clerk_user_id=clerk_user_id, nickname=f"user_{clerk_user_id[:12]}")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    """인증 필수 엔드포인트용. 토큰 없으면 401."""
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={"code": "AUTH_UNAUTHORIZED", "message": "인증이 필요합니다"},
        )
    return user
