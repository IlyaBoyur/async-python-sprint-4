import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from db.db import get_session
from services.services import blacklist_service

logger = logging.getLogger(__name__)


class BlacklistMiddleware(BaseHTTPMiddleware):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def dispatch(self, request: Request, call_next):
        async for db in get_session():
            blacklist_entry = await blacklist_service.get_multi(
                db=db, filter=dict(host=request.client.host)
            )
        if blacklist_entry:
            logger.info(
                "Blacklisted client %s connection attempt", request.client.host
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "You`ve been temporary blacklisted"},
            )
        return await call_next(request)
