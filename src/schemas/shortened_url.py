from datetime import datetime

from pydantic import BaseModel, HttpUrl, conint


class ShortenedURLInDB(BaseModel):
    id: conint(ge=0)
    value: HttpUrl
    original: HttpUrl
    created_at: datetime
    deleted: bool

    class Config:
        orm_mode = True


class ShortenedURLRead(ShortenedURLInDB):
    pass


class ShortenedURLCreate(BaseModel):
    url: HttpUrl
