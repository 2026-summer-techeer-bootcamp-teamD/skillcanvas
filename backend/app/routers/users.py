from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.users import UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["프로필"])


# ── 1-1. 내 프로필 조회 ────────────────────────────────
@router.get("/me", response_model=UserOut, summary="내 프로필 조회")
def get_my_profile(user: User = Depends(get_current_user)) -> User:
    return user


# ── 1-2. 프로필 수정 ────────────────────────────────────
@router.patch("/me", response_model=UserOut, summary="프로필 수정")
def update_my_profile(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> User:
    duplicate = db.scalar(select(User).where(User.nickname == payload.nickname, User.id != user.id))
    if duplicate is not None:
        raise HTTPException(
            409, {"code": "USER_DUPLICATE_NICKNAME", "message": "이미 존재하는 닉네임입니다"}
        )

    user.nickname = payload.nickname
    db.commit()
    db.refresh(user)
    return user
