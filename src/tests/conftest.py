import os
from typing import AsyncGenerator

import pytest
from _pytest.monkeypatch import MonkeyPatch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from db.db import Base
from main import app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Overrides default anyio backend to drop `trio` dependency"""
    return "asyncio"


@pytest.fixture(scope="session")
async def engine() -> AsyncEngine:
    """Create async engine for tests"""
    engine = create_async_engine(
        os.getenv("PROJECT_DB"),
        echo=True,
        connect_args={"check_same_thread": False},
    )
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
async def test_db(engine: AsyncEngine) -> None:
    """Create full db schema before tests and drop after"""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        yield
        await connection.run_sync(Base.metadata.drop_all)


@pytest.fixture()
async def db_connection(
    engine: AsyncEngine,
) -> AsyncGenerator[AsyncConnection, None]:
    """
    Fixture for creating a db connection in tests
    """
    async with engine.connect() as connection:
        yield connection


@pytest.fixture(autouse=True)
async def session(
    db_connection: AsyncConnection, monkeypatch: MonkeyPatch
) -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture for creating a session in tests
    It replaces app`s Session with custom sessionmaker.
    This way tests will create a test database instead of real
    """
    session_maker = sessionmaker(
        bind=db_connection, class_=AsyncSession, expire_on_commit=False
    )
    monkeypatch.setattr("db.db.async_session", session_maker)

    async with session_maker() as session:
        yield session


@pytest.fixture
async def api_client(session) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture for creating httpx.AsyncClient in tests
    Helps to call FastAPI application in tests
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
