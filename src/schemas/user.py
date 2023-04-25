from datetime import datetime

from pydantic import BaseModel


class UserRead(BaseModel):
    id: int
    username: str
    created_at: datetime


class UserCreate(BaseModel):
    username: str
    password: str
