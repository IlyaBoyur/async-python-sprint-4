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


class ShortenedURLUpdate(BaseModel):
    deleted: bool


class ShortenedURLCreate(BaseModel):
    original_url: HttpUrl


class ShortenedURLBatchRead(BaseModel):
    short_id: conint(ge=0)
    short_url: HttpUrl
