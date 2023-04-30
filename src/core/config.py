from logging import config as logging_config

from pydantic import BaseSettings, HttpUrl, PostgresDsn

from core.logger import LOGGING

logging_config.dictConfig(LOGGING)


class AppSettings(BaseSettings):
    project_name: str = "URL Shortener App"
    project_host: str | HttpUrl = "127.0.0.1"
    project_port: int = 8080
    project_db: PostgresDsn | str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    )
    project_shortener: str = "clckru"

    class Config:
        env_file = ".env"


app_settings = AppSettings()
