from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    id: int
    clerk_user_id: str
    nickname: str
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    nickname: str = Field(min_length=2, max_length=20)
