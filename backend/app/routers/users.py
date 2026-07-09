from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.users import UserOut

router = APIRouter(prefix="/users", tags=["프로필"])


# ── 1-1. 내 프로필 조회 ────────────────────────────────
@router.get("/me", response_model=UserOut, summary="내 프로필 조회")
def get_my_profile(user: User = Depends(get_current_user)) -> User:
    return user
