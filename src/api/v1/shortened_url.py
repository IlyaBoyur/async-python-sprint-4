import logging

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session
from schemas import shortened_url as short_url_schema
from schemas.short_url_use import (
    ShortURLUseCreate,
    ShortURLUseRead,
    ShortURLUseReadCut,
)
from schemas.user import UserRead
from services.services import short_url_service, url_use_service
from services.shortener import generate_short_url

from .user import get_user

router = APIRouter()
logger = logging.getLogger(__name__)


def host_extractor(request: Request) -> str:
    return request.client.host


def port_extractor(request: Request) -> int:
    return request.client.port


async def get_short_url(
    *,
    db: AsyncSession = Depends(get_session),
    id: int,
) -> short_url_schema.ShortenedURLRead:
    url_object = await short_url_service.get(db=db, id=id)
    if url_object is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="URL is not found"
        )
    return url_object


async def log_url_use(
    *,
    db: AsyncSession = Depends(get_session),
    host: str = Depends(host_extractor),
    port: int = Depends(port_extractor),
    user_agent: str | None = Header(default=None),
    user: UserRead | None = Depends(get_user),
    short_url: short_url_schema.ShortenedURLRead = Depends(get_short_url),
) -> ShortURLUseRead:
    url_use_data = ShortURLUseCreate.parse_obj(
        {
            "host": host,
            "port": port,
            "user_agent": user_agent or "unknown",
            "url_id": short_url.id,
            "user_id": getattr(user, "id", None),
        }
    )
    db_object = await url_use_service.create(db=db, object_in=url_use_data)
    use = ShortURLUseRead.from_orm(db_object)
    logger.info(f"Logged URL use: {use}")
    return use


@router.get("/{id}")
async def read_short_url(
    *,
    short_url: short_url_schema.ShortenedURLRead = Depends(get_short_url),
    use: ShortURLUseRead = Depends(log_url_use),
) -> Response:
    """Get URL by ID & log use"""
    logger.info(f"Redirecting to: {short_url.original}")
    headers = {"Location": short_url.original}
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
