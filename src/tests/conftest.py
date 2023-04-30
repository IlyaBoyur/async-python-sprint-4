import os

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from db.db import Base, get_session
from main import app

engine = create_async_engine(
    os.getenv("SQLALCHEMY_TEST_DB_URL"),
    echo=True,
    connect_args={"check_same_thread": False},
)
testing_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def anyio_backend():
    """Overrides default `trio` backend to drop dependency"""
    return "asyncio"


@pytest.fixture(scope="session")
async def api_client(test_db):
    """Create and reuse async client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="session")
async def test_db():
    """Create full db schema before tests and drop after"""

    async def override_get_session():
        async with testing_session() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        yield
        await conn.run_sync(Base.metadata.drop_all)
