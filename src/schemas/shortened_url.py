from datetime import datetime

from pydantic import BaseModel, HttpUrl


class ShortenedURLBase(BaseModel):
    url: HttpUrl


class ShortenedURLCreate(ShortenedURLBase):
    pass


# Properties shared by models stored in DB
class ShortenedURLInDBBase(BaseModel):
    id: int
    value: HttpUrl
    original: HttpUrl
    created_at: datetime
    deleted: bool

    class Config:
        orm_mode = True


class ShortenedURL(ShortenedURLInDBBase):
    pass
