from datetime import datetime

from pydantic import BaseModel, HttpUrl


class ShortenedURLInDB(BaseModel):
    id: int
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
