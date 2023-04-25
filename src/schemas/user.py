from datetime import datetime

from pydantic import BaseModel, Field, SecretStr, conint


class UserInDB(BaseModel):
    id: conint(ge=0)
    username: str
    password: SecretStr = Field(exclude=True)
    created_at: datetime

    class Config:
        orm_mode = True


class UserRead(UserInDB):
    pass
