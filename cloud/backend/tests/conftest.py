"""Pytest fixtures for async database tests."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.auth.security import _rate_limit_store
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


@pytest.fixture
async def async_client(engine, tables):
    """Create an httpx AsyncClient backed by the FastAPI test app.

    Overrides the app's get_db dependency so all requests use the test
    engine (with NullPool) rather than the production database engine.
    """
    import app.db as db_module
    from app.main import create_app

    test_app = create_app()

    # Override get_db dependency to use the test engine's session factory
    async def override_get_db():
        session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        async with session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    test_app.dependency_overrides[db_module.get_db] = override_get_db

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(autouse=True)
def _clear_rate_limit():
    """Clear the in-memory rate limit store between tests.

    The phone login rate limiter is an in-process dict shared across
    all tests. Without clearing it, tests that fire multiple login
    requests can hit the 5-per-minute ceiling and spuriously fail.
    """
    _rate_limit_store.clear()
    yield
