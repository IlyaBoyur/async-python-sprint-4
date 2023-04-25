from fastapi import APIRouter

from .shortened_url import router

api_router = APIRouter()

api_router.include_router(router, prefix="")
