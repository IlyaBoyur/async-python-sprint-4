import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session
from schemas.blacklist import BlacklistedClientCreate, BlacklistedClientRead
from services.services import blacklist_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/blacklist")
async def blacklist(
    *, db: AsyncSession = Depends(get_session), client: BlacklistedClientCreate
) -> BlacklistedClientRead:
    """Blacklist host"""
    from models.models import BlacklistedClient

    db_object = BlacklistedClient(**client.dict())
    db.add(db_object)
    await db.commit()
    logger.info(
        "Host %s blacklisted until %s",
        db_object.host,
        db_object.until.ctime(),
    )
    return db_object


@router.get("/blacklist")
async def show_blacklist(
    *, db: AsyncSession = Depends(get_session)
) -> list[BlacklistedClientRead]:
    """Show blacklist"""
    clients = await blacklist_service.get_multi(db=db)
    return clients


@router.delete("/blacklist/{id}")
async def remove_from_blacklist(
    *, db: AsyncSession = Depends(get_session), id: int
) -> Response:
    """Remove host from blacklist"""
    db_object = await blacklist_service.get(db=db, id=id)
    if db_object is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Host is not in blacklist",
        )
    host = db_object.host
    await blacklist_service.delete(db=db, id=id)
    logger.info("Host %s removed from blacklist", host)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
