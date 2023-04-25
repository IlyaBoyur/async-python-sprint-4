from models.models import ShortenedURL as ShortenedURLModel
from schemas.shortened_url import ShortenedURLCreate

from .base import RepositoryDB


class RepositoryShortenedURL(
    RepositoryDB[ShortenedURLModel, ShortenedURLCreate, None]
):
    pass


shortened_url_service = RepositoryShortenedURL(ShortenedURLModel)
