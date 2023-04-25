from pydantic import BaseModel

from .user import UserRead


class ClientRead(BaseModel):
    id: int
    host: str
    user_agent: str
    user: UserRead | None


class ClientCreate(BaseModel):
    host: str
    user_agent: str
    user_id: int

    class Config:
        orm_mode = True
