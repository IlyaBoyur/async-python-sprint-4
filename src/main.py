import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from api.v1 import base
from core.config import app_settings
from middlewares.base import middlewares

app = FastAPI(
    title=app_settings.project_name,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
)

app.include_router(base.api_router, prefix="/api/v1")
for middleware in middlewares:
    app.add_middleware(middleware)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=app_settings.project_host,
        port=app_settings.project_port,
        reload=True,
    )
