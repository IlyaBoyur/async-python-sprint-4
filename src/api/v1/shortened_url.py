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
from schemas.short_url_use import (
    ShortURLUseCreate,
    ShortURLUseRead,
    ShortURLUseReadCut,
)
from schemas.shortened_url import (
    ShortenedURLBatchRead,
    ShortenedURLCreate,
    ShortenedURLRead,
    ShortenedURLUpdate,
)
from services.services import short_url_service, url_use_service
from services.shortener import generate_short_url

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
) -> ShortenedURLRead:
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
    short_url: ShortenedURLRead = Depends(get_short_url),
) -> ShortURLUseRead:
    url_use_data = ShortURLUseCreate.parse_obj(
        {
            "host": host,
            "port": port,
            "user_agent": user_agent or "unknown",
            "url_id": short_url.id,
            "user_id": None,
        }
    )
    db_object = await url_use_service.create(db=db, object_in=url_use_data)
    use = ShortURLUseRead.from_orm(db_object)
    logger.info(f"Logged URL use: {use}")
    return use


@router.post("/shorten")
async def bulk_create_short_url(
    *,
    db: AsyncSession = Depends(get_session),
    urls_in: list[ShortenedURLCreate],
) -> list[ShortenedURLBatchRead]:
    objects_in = [
        {
            "value": generate_short_url(url.original_url),
            "original": url.original_url,
        }
        for url in urls_in
    ]
    db_objects = await short_url_service.bulk_create(
        db=db, objects_in=objects_in
    )
    urls_out = [
        ShortenedURLBatchRead(short_id=obj.id, short_url=obj.value)
        for obj in db_objects
    ]
    return urls_out


@router.get("/{id}")
async def read_short_url(
    *,
    short_url: ShortenedURLRead = Depends(get_short_url),
    use: ShortURLUseRead = Depends(log_url_use),
) -> Response:
    """Get URL by ID & log use"""
    if short_url.deleted:
        return Response(status_code=status.HTTP_410_GONE)
    logger.info(f"Redirecting to: {short_url.original}")
    headers = {"Location": short_url.original}
    return Response(
        content="",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers=headers,
    )


@router.delete("/{id}")
async def mark_deleted_short_url(
    *,
    db: AsyncSession = Depends(get_session),
    short_url: ShortenedURLRead = Depends(get_short_url),
) -> Response:
    """Get URL by ID & mark deleted"""
    await short_url_service.update(
        db=db, db_object=short_url, object_in=ShortenedURLUpdate(deleted=True)
    )
    logger.info(f"Mark {short_url.value} ({short_url.original}) as deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id}/status")
async def read_short_url_use_history(
    *,
    db: AsyncSession = Depends(get_session),
    id: int,
    full_info: bool | None = None,
    offset: int = 0,
    max_result: int = 10,
) -> list[ShortURLUseRead] | ShortURLUseReadCut:
    """Get URL use history by ID"""
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
    url_in: ShortenedURLCreate,
) -> ShortenedURLRead:
    """Create new short URL"""
    original = url_in.original_url
    urls_count = await short_url_service.count(db, filter={"value": original})
    if urls_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL already exists",
        )
    data = {
        "value": generate_short_url(original),
        "original": original,
    }
    url_object = await short_url_service.create(db=db, object_in=data)
    return ShortenedURLRead.from_orm(url_object)
