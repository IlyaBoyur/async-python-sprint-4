import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session
from schemas.status import Status
from services.services import url_use_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/ping")
async def ping_db(*, db: AsyncSession = Depends(get_session)) -> Status:
    """Get database status"""
    time = await url_use_service.get_current_time(db=db)
    if time:
        message = f"Connection established. Database time: {time}"
    else:
        message = "Database is not available"
    return Status(message=message)
