from datetime import datetime

from pydantic import BaseModel, conint
from pydantic.networks import IPv4Address


class BlacklistedClientCreate(BaseModel):
    host: IPv4Address
    until: datetime | None


class BlacklistedClientInDB(BaseModel):
    id: conint(ge=0)
    host: IPv4Address
    until: datetime | None

    class Config:
        orm_mode = True


class BlacklistedClientRead(BlacklistedClientInDB):
    pass
