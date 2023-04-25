from models.models import ShortenedURL as ShortenedURLModel
from models.models import ShortenedURLUse as ShortenedURLUseModel
from schemas.short_url_use import ShortURLUseCreate
from schemas.shortened_url import ShortenedURLCreate

from .base import RepositoryDB


class RepositoryShortenedURL(
    RepositoryDB[ShortenedURLModel, ShortenedURLCreate, None]
):
    pass


short_url_service = RepositoryShortenedURL(ShortenedURLModel)


class RepositoryShortenedURLUse(
    RepositoryDB[ShortenedURLUseModel, ShortURLUseCreate, None]
):
    pass


url_use_service = RepositoryShortenedURLUse(ShortenedURLUseModel)
