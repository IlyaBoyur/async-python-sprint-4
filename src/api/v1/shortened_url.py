import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session
from schemas import shortened_url as short_url_schema
from schemas.short_url_use import ShortURLUseRead, ShortURLUseReadCut
from services.services import short_url_service, url_use_service
from services.shortener import generate_short_url

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{id}")
async def read_short_url(
    *,
    db: AsyncSession = Depends(get_session),
    id: int,
) -> Response:
    """Get URL by ID"""
    url_object = await short_url_service.get(db=db, id=id)
    if url_object is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="URL is not found"
        )
    logger.info(f"Redirecting to: {url_object.original}")
    headers = {"Location": url_object.original}
    return Response(
        content="",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers=headers,
    )


@router.get("/{id}/status")
async def read_short_url_statistics(
    *,
    db: AsyncSession = Depends(get_session),
    id: int,
    full_info: bool | None = None,
    offset: int = 0,
    max_result: int = 10,
) -> list[ShortURLUseRead] | ShortURLUseReadCut:
    """Get URL statistics by ID"""
    if not full_info:
        url_uses_count = await url_use_service.count(
            db, filter=dict(url_id=id)
        )
        return ShortURLUseReadCut(count=url_uses_count)
    url_uses = await url_use_service.get_multi(
        db=db, filter=dict(url_id=id), skip=offset, limit=max_result
    )
    return url_uses


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_short_url(
    *,
    db: AsyncSession = Depends(get_session),
    url_in: short_url_schema.ShortenedURLCreate,
) -> short_url_schema.ShortenedURLRead:
    """Create new short URL"""
    urls_count = await short_url_service.count(
        db, filter={"value": url_in.url}
    )
    if urls_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL already exists",
        )
    data = {
        "value": url_in.url,
        "original": generate_short_url(url_in.url),
    }
    url_object = await short_url_service.create(db=db, object_in=data)
    return short_url_schema.ShortenedURLRead.from_orm(url_object)
