from datetime import datetime

from pydantic import BaseModel

from .client import ClientRead
from .shortened_url import ShortenedURLRead


class ShortURLUseRead(BaseModel):
    created_at: datetime
    url: ShortenedURLRead
    client: ClientRead

    class Config:
        orm_mode = True


class ShortURLUseReadCut(BaseModel):
    count: int


class ShortURLUseCreate(BaseModel):
    url_id: int
    client_id: int
