from models.models import BlacklistedClient as BlacklistedClientModel
from models.models import ShortenedURL as ShortenedURLModel
from models.models import ShortenedURLUse as ShortenedURLUseModel
from schemas.blacklist import BlacklistedClientCreate
from schemas.short_url_use import ShortURLUseCreate
from schemas.shortened_url import ShortenedURLCreate, ShortenedURLUpdate

from .base import RepositoryDB


class RepositoryShortenedURL(
    RepositoryDB[ShortenedURLModel, ShortenedURLCreate, ShortenedURLUpdate]
):
    pass


short_url_service = RepositoryShortenedURL(ShortenedURLModel)


class RepositoryShortenedURLUse(
    RepositoryDB[ShortenedURLUseModel, ShortURLUseCreate, None]
):
    pass


url_use_service = RepositoryShortenedURLUse(ShortenedURLUseModel)


class RepositoryBlacklist(
    RepositoryDB[BlacklistedClientModel, BlacklistedClientCreate, None]
):
    pass


blacklist_service = RepositoryBlacklist(BlacklistedClientModel)
