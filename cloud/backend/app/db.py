"""Async SQLAlchemy database engine and session utilities."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

async_engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "dev",
    future=True,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize the async engine (no schema creation; alembic owns schema)."""
    # Engine is created at import time; this hook is reserved for app startup.
    pass


async def close_db() -> None:
    """Dispose the async engine on app shutdown."""
    await async_engine.dispose()
