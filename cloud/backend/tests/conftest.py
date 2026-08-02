"""Pytest fixtures for async database tests."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.auth.models import RefreshToken  # noqa: F401 — register with Base.metadata
from app.auth.security import _rate_limit_store
from app.config import settings
from app.models import child, device_binding, family, parent, parent_child  # noqa: F401
from app.models.answer import AnswerRecord, WrongAnswer  # noqa: F401
from app.models.base import Base
from app.models.config import ConfigAudit, LearningGoal, LearningModuleConfig  # noqa: F401
from app.models.behavior import BehaviorEvent  # noqa: F401
from app.models.file_upload import FileUpload  # noqa: F401
from app.models.message import ParentMessage  # noqa: F401
from app.models.navigation import NavigationInstruction  # noqa: F401
from app.models.notification import Notification, NotificationSettings  # noqa: F401
from app.models.content import (  # noqa: F401
    EnglishWord,
    MathQuestion,
    MusicTrack,
    PoemContent,
    QuizQuestion,
    ScienceArticle,
)
from app.models.learning import BatchItem, LearningBatch, LearningSession  # noqa: F401
from app.models.task import DailyTask  # noqa: F401
from app.telemetry.models import LearningEvent  # noqa: F401


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
        # Use CASCADE to handle FK dependencies between new and old tables.
        # SQLAlchemy's drop_all can mis-order tables with complex FK graphs.
        from sqlalchemy import text

        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(
                text(f"DROP TABLE IF EXISTS {table.name} CASCADE")
            )


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
