import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session
from schemas import shortened_url as short_url_schema
from services.services import shortened_url_service as short_url_service
from services.shortener import generate_short_url

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{id}")
async def read_short_url(
    *,
    db: AsyncSession = Depends(get_session),
    id: int,
) -> Any:
    """Get URL by ID"""
    url_object = await short_url_service.get(db=db, id=id)
    if url_object is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="URL is not found"
        )
    headers = {"Location": url_object.original}
    logger.info(f"Redirecting to: {url_object.original}")
    return Response(
        content="",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers=headers,
    )


@router.post(
    "/",
    response_model=short_url_schema.ShortenedURL,
    status_code=status.HTTP_201_CREATED,
)
async def create_short_url(
    *,
    db: AsyncSession = Depends(get_session),
    url_in: short_url_schema.ShortenedURLCreate,
) -> Any:
    """Create new short URL"""
    print(url_in.url)
    data = {
        "value": url_in.url,
        "original": generate_short_url(url_in.url),
    }
    url = await short_url_service.create(db=db, object_in=data)
    return url
