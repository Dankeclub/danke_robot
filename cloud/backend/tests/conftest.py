"""Pytest fixtures for async database tests."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.models.base import Base


@pytest.fixture
async def engine():
    """Create a test async engine with no connection pooling."""
    test_engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        future=True,
    )
    yield test_engine
    await test_engine.dispose()


@pytest.fixture
async def tables(engine):
    """Create all tables before a test and drop them afterwards."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(engine, tables):
    """Yield an async session bound to the test engine."""
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    async with session_factory() as session:
        yield session
