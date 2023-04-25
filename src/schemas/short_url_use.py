from datetime import datetime

from pydantic import BaseModel, conint

from .user import UserRead


class ShortURLUseReadCut(BaseModel):
    count: conint(ge=0)


class ShortURLUseInDB(BaseModel):
    id: conint(ge=0)
    created_at: datetime
    host: str
    port: conint(ge=0)
    user_agent: str
    url_id: conint(ge=0)
    user_id: conint(ge=0) | None

    class Config:
        orm_mode = True


class ShortURLUseCreate(ShortURLUseInDB):
    id: None = None
    created_at: None = None


class ShortURLUseRead(ShortURLUseInDB):
    pass
