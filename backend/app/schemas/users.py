from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    id: int
    clerk_user_id: str
    nickname: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
