import os
from logging import config as logging_config

from dotenv import load_dotenv
from pydantic import BaseSettings, PostgresDsn

from core.logger import LOGGING

logging_config.dictConfig(LOGGING)
load_dotenv(".env")


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROJECT_NAME = os.getenv("PROJECT_NAME", "URL Shortener App")
PROJECT_HOST = os.getenv("PROJECT_HOST", "127.0.0.1")
PROJECT_PORT = int(os.getenv("PROJECT_PORT", "8080"))
PROJECT_DB = os.getenv(
    "PROJECT_DB",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
)
PROJECT_SHORTENER = os.getenv("PROJECT_SHORTENER", "clckru")


class AppSettings(BaseSettings):
    app_title: str = PROJECT_NAME
    database_dsn: PostgresDsn = PROJECT_DB


app_settings = AppSettings()
