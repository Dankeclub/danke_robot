# Cloud Backend Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal runnable backend skeleton — FastAPI app, car login (phone), parent login (WeChat), event reporting (telemetry), car screen login page — so the car can complete "phone login → JWT → report events" end-to-end and parents can complete "WeChat login → JWT".

**Architecture:** Modular monolith with 8 planned modules. This plan delivers the app shell (main.py + middleware + unified response), auth module (RefreshToken model + JWT security + car/parent routers), telemetry module (LearningEvent model + idempotent batch insert), and car screen login page + network layer. All new code follows the existing patterns: async SQLAlchemy, Alembic migrations, pydantic-settings, Vue 3 Composition API with hand-drawn doodle style.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2.0 async, asyncpg, Alembic, PyJWT, httpx, pydantic-settings, Vue 3 (Composition API), PostgreSQL 16

## Global Constraints

- Python >= 3.12
- All API responses use `{code: int, msg: str, data: object|null}` envelope
- HTTP status: 200 success, 401 unauthenticated, 404 not found, 409 conflict, 422 validation error, 500 internal error
- Car API prefix: `/v1/api/car`, Parent API prefix: `/v1/api/parent`
- All DB models use `AuditMixin` (UUID PK + created_at/updated_at) unless specified otherwise
- Alembic manages all schema changes; never use `Base.metadata.create_all` in production
- `.env` contains secrets; `.env.example` is the template; never commit real secrets
- Ruff format: line-length 100, select E/F/I/N/W/UP, target py312, google pydocstyle
- Car screen: 1024x600, hand-drawn doodle style, `--font-heading: 'ZCOOL KuaiLe'`, touch-friendly (min 48px)

---

### Task 1: Create feature branch and install new dependencies

**Files:**
- Modify: `cloud/backend/pyproject.toml`

**Interfaces:**
- Produces: branch `feature/cloud-backend-skeleton`, `httpx` available as production dependency, `PyJWT` available

- [ ] **Step 1: Create feature branch**

```bash
cd d:/danke_robot
git checkout -b feature/cloud-backend-skeleton
```

- [ ] **Step 2: Add httpx and PyJWT to production dependencies**

In `cloud/backend/pyproject.toml`, add to `dependencies` list:

```toml
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy[asyncio]>=2.0.30",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "pydantic-settings>=2.3.0",
    "python-dotenv>=1.0.0",
    "psycopg[binary]>=3.1.0",
    "httpx>=0.27.0",
    "PyJWT>=2.9.0",
]
```

Note: `httpx` moves from dev-dependency to production dependency. Remove it from `[project.optional-dependencies] dev`.

- [ ] **Step 3: Install updated dependencies**

```powershell
cd d:/danke_robot/cloud/backend
pip install -e .
```

- [ ] **Step 4: Verify imports work**

```powershell
cd d:/danke_robot/cloud/backend
python -c "import httpx; import jwt; print('httpx', httpx.__version__); print('PyJWT', jwt.__version__)"
```

- [ ] **Step 5: Commit**

```bash
git add cloud/backend/pyproject.toml
git commit -m "build: add httpx and PyJWT as production dependencies"
```

---

### Task 2: Fix .env to use dev mode

**Files:**
- Modify: `cloud/backend/.env`

- [ ] **Step 1: Change APP_ENV from test to dev**

Replace the content of `cloud/backend/.env`:

```env
APP_ENV=dev
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://parent:parent@localhost:5432/parent_db
```

- [ ] **Step 2: Commit**

```bash
git add cloud/backend/.env
git commit -m "fix: set APP_ENV=dev in default .env file"
```

---

### Task 3: Fix ParentChild model to use composite primary key

**Files:**
- Modify: `cloud/backend/app/models/parent_child.py`
- Modify: `cloud/backend/tests/test_parent_child.py`
- Create: `cloud/backend/alembic/versions/20260726_a1b2c3d4e5f6_fix_parent_child_pk.py`

**Interfaces:**
- Produces: `ParentChild` model with `(parent_id, child_id)` composite PK, no UUID `id`. Tests updated.
- Consumes: `AuditMixin` columns recreated manually (id, created_at, updated_at dropped; created_at/updated_at added manually).

- [ ] **Step 1: Rewrite ParentChild model**

Replace `cloud/backend/app/models/parent_child.py`:

```python
"""Parent-child binding model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ParentChild(Base):
    """Binding between a parent account and a child.

    Uses (parent_id, child_id) as composite primary key.
    A parent can manage multiple children.
    """

    __tablename__ = "parent_child"

    parent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parent_account.id"),
        primary_key=True,
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("child.id"),
        primary_key=True,
    )
    family_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("family.id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="active"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("idx_parent_child_parent", "parent_id"),
        Index("idx_parent_child_child", "child_id"),
    )
```

- [ ] **Step 2: Create the fix migration**

Create `cloud/backend/alembic/versions/20260726_a1b2c3d4e5f6_fix_parent_child_pk.py`:

```python
"""fix parent_child composite primary key

Revision ID: a1b2c3d4e5f6
Revises: d4e5f6a7b8c9
Create Date: 2026-07-26 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Replace UUID PK with composite (parent_id, child_id) PK."""
    # Drop old table
    op.drop_table('parent_child')

    # Recreate with composite PK
    op.create_table(
        'parent_child',
        sa.Column(
            'parent_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('parent_account.id'),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            'child_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('child.id'),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            'family_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('family.id'),
            nullable=False,
        ),
        sa.Column('status', sa.Text(), nullable=False, server_default=sa.text("'active'")),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('parent_id', 'child_id'),
    )
    op.create_index('idx_parent_child_parent', 'parent_child', ['parent_id'])
    op.create_index('idx_parent_child_child', 'parent_child', ['child_id'])


def downgrade() -> None:
    """Restore UUID PK."""
    op.drop_table('parent_child')
    op.create_table(
        'parent_child',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
        ),
        sa.Column(
            'parent_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('parent_account.id'),
            nullable=False,
        ),
        sa.Column(
            'child_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('child.id'),
            nullable=False,
        ),
        sa.Column(
            'family_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('family.id'),
            nullable=False,
        ),
        sa.Column('status', sa.Text(), nullable=False, server_default=sa.text("'active'")),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('parent_id', 'child_id'),
    )
    op.create_index('idx_parent_child_parent', 'parent_child', ['parent_id'])
    op.create_index('idx_parent_child_child', 'parent_child', ['child_id'])
```

- [ ] **Step 3: Update test to match new model (no UUID id)**

Replace `cloud/backend/tests/test_parent_child.py`:

```python
"""Tests for the parent_child table."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.child import Child
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild


async def test_create_parent_child(db_session):
    """A parent-child binding can be inserted with composite PK."""
    family = Family(name="小宇的家")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="小宇")
    db_session.add(child)
    await db_session.flush()

    parent = ParentAccount(
        phone_e164="+8613800138000",
        phone_hash="sha256:test001",
        phone_masked="138****8000",
    )
    db_session.add(parent)
    await db_session.flush()

    pc = ParentChild(
        parent_id=parent.id,
        family_id=family.id,
        child_id=child.id,
    )
    db_session.add(pc)
    await db_session.commit()
    await db_session.refresh(pc)

    # Composite PK: no UUID id field
    assert pc.parent_id == parent.id
    assert pc.child_id == child.id
    assert pc.status == "active"
    assert pc.is_default is False
    assert pc.created_at is not None
    assert pc.updated_at is not None


async def test_parent_child_unique_constraint(db_session):
    """Duplicate (parent_id, child_id) violates composite PK."""
    family = Family(name="测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="测试孩子")
    db_session.add(child)
    await db_session.flush()

    parent = ParentAccount(
        phone_e164="+8613800138000",
        phone_hash="sha256:test002",
        phone_masked="138****8000",
    )
    db_session.add(parent)
    await db_session.flush()

    pc1 = ParentChild(
        parent_id=parent.id,
        family_id=family.id,
        child_id=child.id,
    )
    pc2 = ParentChild(
        parent_id=parent.id,
        family_id=family.id,
        child_id=child.id,
    )
    db_session.add(pc1)
    db_session.add(pc2)

    with pytest.raises(IntegrityError):
        await db_session.commit()
```

- [ ] **Step 4: Drop and recreate test DB, run migration and tests**

```powershell
cd d:/danke_robot/cloud/backend

# Drop and recreate test database (all migrations are from scratch)
$env:PGPASSWORD="parent"
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U parent -h localhost -c "DROP DATABASE IF EXISTS parent_db;"
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U parent -h localhost -c "CREATE DATABASE parent_db;"

# Run all migrations from scratch
alembic upgrade head

# Run existing tests
pytest tests/ -v
```

Expected: 16 tests pass. `test_parent_child` no longer checks `pc.id` (UUID), instead checks composite PK `(parent_id, child_id)`.

- [ ] **Step 5: Commit**

```bash
git add cloud/backend/app/models/parent_child.py \
        cloud/backend/tests/test_parent_child.py \
        cloud/backend/alembic/versions/20260726_a1b2c3d4e5f6_fix_parent_child_pk.py
git commit -m "refactor: change ParentChild PK from UUID to composite (parent_id, child_id)"
```

---

### Task 4: Make ParentAccount phone fields nullable for WeChat-first login

**Files:**
- Modify: `cloud/backend/app/models/parent.py`
- Create: `cloud/backend/alembic/versions/20260726_b2c3d4e5f6a7_alter_parent_account_phone_nullable.py`

**Interfaces:**
- Produces: `ParentAccount.phone_e164`, `phone_hash`, `phone_masked` all `nullable=True`. `phone_hash` unique constraint replaced with conditional unique index `WHERE phone_hash IS NOT NULL`.
- Consumes: DDL event pattern from `app/models/device_binding.py:73-80`.

- [ ] **Step 1: Update ParentAccount model**

Replace `cloud/backend/app/models/parent.py`:

```python
"""Parent account model."""

from sqlalchemy import DDL, Text, event
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base


class ParentAccount(Base, AuditMixin):
    """A parent user account.

    Phone fields are nullable to support WeChat-first registration:
    wx.login() creates an account with status='pending_bind', then
    phone is bound later via /auth/phone/bind.

    Attributes:
        phone_e164: E.164 formatted phone number (nullable).
        phone_hash: Deterministic hash of the phone number (nullable).
        phone_masked: Displayable masked phone number (nullable).
        nickname: Optional display name.
        avatar_url: Optional avatar image URL.
        wx_openid: WeChat OpenID for this mini-program (nullable).
        wx_unionid: WeChat UnionID across apps (nullable).
        status: 'active' | 'pending_bind' | 'disabled'.
    """

    __tablename__ = "parent_account"

    phone_e164: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone_masked: Mapped[str | None] = mapped_column(Text, nullable=True)
    nickname: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    wx_openid: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    wx_unionid: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="active",
    )


# DDL event: create conditional unique index on phone_hash.
# SQLAlchemy ORM does not support WHERE clauses on UniqueConstraint,
# so we register it as a raw DDL after_create event.
event.listen(
    ParentAccount.__table__,
    "after_create",
    DDL(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_parent_account_phone_hash "
        "ON parent_account(phone_hash) WHERE phone_hash IS NOT NULL"
    ),
)
```

- [ ] **Step 2: Create the migration**

Create `cloud/backend/alembic/versions/20260726_b2c3d4e5f6a7_alter_parent_account_phone_nullable.py`:

```python
"""alter parent_account phone fields to nullable

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-26 09:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make phone fields nullable; replace unique constraint with conditional index."""
    # Drop old unique constraint
    op.drop_constraint('parent_account_phone_hash_key', 'parent_account', type_='unique')

    # Make phone columns nullable
    op.alter_column('parent_account', 'phone_e164', nullable=True)
    op.alter_column('parent_account', 'phone_hash', nullable=True)
    op.alter_column('parent_account', 'phone_masked', nullable=True)

    # Create conditional unique index
    op.create_index(
        'idx_parent_account_phone_hash',
        'parent_account',
        ['phone_hash'],
        unique=True,
        postgresql_where=sa.text('phone_hash IS NOT NULL'),
    )


def downgrade() -> None:
    """Restore phone fields to non-nullable with plain unique constraint."""
    op.drop_index('idx_parent_account_phone_hash', 'parent_account')
    op.alter_column('parent_account', 'phone_masked', nullable=False)
    op.alter_column('parent_account', 'phone_hash', nullable=False)
    op.alter_column('parent_account', 'phone_e164', nullable=False)
    op.create_unique_constraint('parent_account_phone_hash_key', 'parent_account', ['phone_hash'])
```

- [ ] **Step 3: Run migration and verify tests pass**

```powershell
cd d:/danke_robot/cloud/backend
# Rebuild DB from scratch
$env:PGPASSWORD="parent"
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U parent -h localhost -c "DROP DATABASE IF EXISTS parent_db;"
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U parent -h localhost -c "CREATE DATABASE parent_db;"
alembic upgrade head
pytest tests/ -v
```

Expected: 16 tests pass. `test_parent_account.py` factory uses phone fields, still works (nullable doesn't break existing non-null data).

- [ ] **Step 4: Commit**

```bash
git add cloud/backend/app/models/parent.py \
        cloud/backend/alembic/versions/20260726_b2c3d4e5f6a7_alter_parent_account_phone_nullable.py
git commit -m "refactor: make ParentAccount phone fields nullable for WeChat-first registration"
```

---

### Task 5: Extend config.py with JWT, WeChat, rate-limit, and timezone settings

**Files:**
- Modify: `cloud/backend/app/config.py`
- Modify: `cloud/backend/.env.example`

**Interfaces:**
- Produces: `settings.JWT_SECRET` (SecretStr), `settings.JWT_ALGORITHM`, `settings.ACCESS_TOKEN_TTL_SECONDS`, `settings.REFRESH_TOKEN_TTL_SECONDS`, `settings.WX_APPID`, `settings.WX_SECRET` (SecretStr), `settings.PHONE_LOGIN_RATE_LIMIT`, `settings.BUSINESS_TIMEZONE`
- Consumes: nothing new

- [ ] **Step 1: Extend Settings class**

Replace `cloud/backend/app/config.py`:

```python
"""Application settings loaded from environment / .env file."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings.

    Attributes:
        app_env: Runtime environment name (dev, test, prod).
        log_level: Logging level.
        database_url: Async PostgreSQL connection URL using asyncpg.
        jwt_secret: Secret key for signing JWT tokens.
        jwt_algorithm: JWT signing algorithm.
        access_token_ttl_seconds: Access token time-to-live in seconds.
        refresh_token_ttl_seconds: Refresh token time-to-live in seconds.
        wx_appid: WeChat Mini Program AppID.
        wx_secret: WeChat Mini Program AppSecret.
        phone_login_rate_limit: Max phone login attempts per IP per minute.
        business_timezone: IANA timezone for business date calculations.
    """

    app_env: str = "dev"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://parent:parent@localhost:5432/parent_db"

    # JWT
    jwt_secret: SecretStr = SecretStr("change-me-in-production")
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 7200
    refresh_token_ttl_seconds: int = 2592000

    # WeChat Mini Program
    wx_appid: str = ""
    wx_secret: SecretStr = SecretStr("")

    # Rate limiting
    phone_login_rate_limit: int = 5

    # Business
    business_timezone: str = "Asia/Shanghai"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
```

Note: `pydantic.SecretStr` is used for `jwt_secret` and `wx_secret` to prevent accidental logging. Access the actual value with `.get_secret_value()`.

- [ ] **Step 2: Update .env.example**

Replace `cloud/backend/.env.example`:

```env
# Copy this file to .env and fill in real secrets for non-local environments.
APP_ENV=dev
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://parent:parent@localhost:5432/parent_db

# JWT — generate a strong random secret: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET=change-me-in-production

# WeChat Mini Program — fill in from 微信公众平台 → 开发 → 开发设置
WX_APPID=
WX_SECRET=
```

- [ ] **Step 3: Verify config loads**

```powershell
cd d:/danke_robot/cloud/backend
python -c "from app.config import settings; print('JWT_ALGORITHM:', settings.jwt_algorithm); print('ACCESS_TOKEN_TTL:', settings.access_token_ttl_seconds); print('TZ:', settings.business_timezone)"
```

- [ ] **Step 4: Commit**

```bash
git add cloud/backend/app/config.py cloud/backend/.env.example
git commit -m "feat: add JWT, WeChat, rate-limit, and timezone config settings"
```

---

### Task 6: Create unified response schema and middleware

**Files:**
- Create: `cloud/backend/app/schemas/__init__.py`
- Create: `cloud/backend/app/schemas/common.py`
- Create: `cloud/backend/app/middleware/__init__.py`
- Create: `cloud/backend/app/middleware/cors.py`
- Create: `cloud/backend/app/middleware/request_id.py`
- Create: `cloud/backend/app/middleware/error_handler.py`

**Interfaces:**
- Produces:
  - `APIResponse[T]` — pydantic model `{code: int, msg: str, data: T|None}`
  - `ok(data)` — helper returning `APIResponse(code=0, msg="ok", data=data)`
  - `error(code, msg)` — helper returning `APIResponse(code=N, msg=str, data=None)`
  - `add_cors(app)` — function to configure CORS
  - `RequestIDMiddleware` — ASGI middleware injecting `X-Request-ID`
  - `register_error_handlers(app)` — function registering global exception handlers
- Consumes: nothing

- [ ] **Step 1: Write common schemas**

Create `cloud/backend/app/schemas/__init__.py`:
```python
"""Shared pydantic schemas."""
```

Create `cloud/backend/app/schemas/common.py`:

```python
"""Unified API response envelope and helper functions."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper.

    All endpoints return this envelope:
        {"code": 0, "msg": "ok", "data": {...}}
    """

    code: int = 0
    msg: str = "ok"
    data: T | None = None


def ok(data: Any = None) -> dict[str, Any]:
    """Build a success response dict.

    Usage:
        return ok({"profile": child_profile})
        return ok()  # data is null
    """
    return {"code": 0, "msg": "ok", "data": data}


def error(code: int, msg: str, data: Any = None) -> dict[str, Any]:
    """Build an error response dict.

    Usage:
        return error(404, "phone_not_bound")
    """
    return {"code": code, "msg": msg, "data": data}
```

- [ ] **Step 2: Write middleware files**

Create `cloud/backend/app/middleware/__init__.py`:
```python
"""FastAPI middleware package."""
```

Create `cloud/backend/app/middleware/cors.py`:

```python
"""CORS middleware configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def add_cors(app: FastAPI) -> None:
    """Add CORS middleware allowing all origins in dev.

    Production must restrict origins to the actual mini-program and car domains.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

Create `cloud/backend/app/middleware/request_id.py`:

```python
"""X-Request-ID middleware for traceability."""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject X-Request-ID header into every response.

    If the client sends X-Request-ID, it is reused; otherwise a new
    UUID v4 is generated.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

Create `cloud/backend/app/middleware/error_handler.py`:

```python
"""Global exception handlers — convert unhandled errors to APIResponse envelope."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.schemas.common import error


def register_error_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        return JSONResponse(
            status_code=409,
            content=error(409, "resource_conflict"),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=error(500, "internal_error"),
        )
```

- [ ] **Step 3: Commit**

```bash
git add cloud/backend/app/schemas/ cloud/backend/app/middleware/
git commit -m "feat: add unified response schema and middleware (CORS, request ID, error handler)"
```

---

### Task 7: Create FastAPI app factory (main.py) and top-level router

**Files:**
- Create: `cloud/backend/app/main.py`
- Create: `cloud/backend/app/router.py`

**Interfaces:**
- Produces:
  - `app: FastAPI` — the ASGI application instance (importable as `app.main:app` for uvicorn)
  - `router.py` aggregates all sub-routers under `/v1/api/car` and `/v1/api/parent`
- Consumes: middleware functions from Task 6, placeholder routers (will be populated by later tasks)

- [ ] **Step 1: Write top-level router**

Create `cloud/backend/app/router.py`:

```python
"""Top-level router aggregation.

All module routers are assembled here under their API prefixes.
"""

from fastapi import APIRouter

# Routers will be imported and included as they are implemented.
# For now, the health check is the only endpoint.

top_router = APIRouter()


@top_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"code": 0, "msg": "ok", "data": {"status": "healthy"}}
```

- [ ] **Step 2: Write main.py**

Create `cloud/backend/app/main.py`:

```python
"""FastAPI application factory.

Entry point for uvicorn: `uvicorn app.main:app --reload`
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import close_db, init_db
from app.middleware.cors import add_cors
from app.middleware.error_handler import register_error_handlers
from app.middleware.request_id import RequestIDMiddleware
from app.router import top_router


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup and shutdown lifecycle."""
    await init_db()
    yield
    await close_db()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    application = FastAPI(
        title="Danke Parent Backend",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Middleware (order matters: CORS outermost, request ID, then error handlers)
    add_cors(application)
    application.add_middleware(RequestIDMiddleware)
    register_error_handlers(application)

    application.include_router(top_router)

    return application


app = create_app()
```

- [ ] **Step 3: Verify app starts and /health responds**

```powershell
cd d:/danke_robot/cloud/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
# In another terminal:
# curl http://localhost:8000/health
```

Expected response: `{"code": 0, "msg": "ok", "data": {"status": "healthy"}}`

- [ ] **Step 4: Commit**

```bash
git add cloud/backend/app/main.py cloud/backend/app/router.py
git commit -m "feat: add FastAPI app factory with health check endpoint"
```

---

### Task 8: Create RefreshToken model and migration

**Files:**
- Create: `cloud/backend/app/auth/__init__.py`
- Create: `cloud/backend/app/auth/models.py`
- Create: `cloud/backend/alembic/versions/20260726_c3d4e5f6a7b8_create_refresh_token.py`

**Interfaces:**
- Produces: `RefreshToken` model — `id, token_hash, parent_id(FK,nullable), device_id(FK,nullable), child_id(FK,nullable), family_id(FK,nullable), expires_at, revoked_at, rotated_from_id(FK self-ref), created_at, updated_at`
- Consumes: `AuditMixin` from `app.models.base`, existing models for FK references

- [ ] **Step 1: Write RefreshToken model**

Create `cloud/backend/app/auth/__init__.py`:
```python
"""Auth module — authentication, JWT, token management."""
```

Create `cloud/backend/app/auth/models.py`:

```python
"""Refresh token model for JWT token rotation."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RefreshToken(Base):
    """Stores hashed refresh tokens for JWT rotation.

    parent_id and device_id are mutually exclusive — car login stores
    device_id; parent login stores parent_id. This is enforced at the
    application layer, not via DB constraint.
    """

    __tablename__ = "refresh_token"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    token_hash: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parent_account.id"),
        nullable=True,
    )
    device_id: Mapped[str | None] = mapped_column(
        Text,
        ForeignKey("device_binding.device_id"),
        nullable=True,
    )
    child_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("child.id"),
        nullable=True,
    )
    family_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("family.id"),
        nullable=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rotated_from_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("refresh_token.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
```

Note: `RefreshToken` does NOT inherit `AuditMixin` because it uses its own PK definition (needs `default=uuid.uuid4` not `server_default=gen_random_uuid()`) and manually defines `created_at`/`updated_at`.

- [ ] **Step 2: Create migration**

Create `cloud/backend/alembic/versions/20260726_c3d4e5f6a7b8_create_refresh_token.py`:

```python
"""create refresh_token

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-26 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create refresh_token table."""
    op.create_table(
        'refresh_token',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column('token_hash', sa.Text(), nullable=False),
        sa.Column(
            'parent_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('parent_account.id'),
            nullable=True,
        ),
        sa.Column(
            'device_id',
            sa.Text(),
            sa.ForeignKey('device_binding.device_id'),
            nullable=True,
        ),
        sa.Column(
            'child_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('child.id'),
            nullable=True,
        ),
        sa.Column(
            'family_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('family.id'),
            nullable=True,
        ),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'rotated_from_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('refresh_token.id'),
            nullable=True,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
    )


def downgrade() -> None:
    """Drop refresh_token table."""
    op.drop_table('refresh_token')
```

- [ ] **Step 3: Run migration and verify**

```powershell
cd d:/danke_robot/cloud/backend
alembic upgrade head
python -c "from app.auth.models import RefreshToken; print('RefreshToken model loaded OK')"
```

- [ ] **Step 4: Commit**

```bash
git add cloud/backend/app/auth/ \
        cloud/backend/alembic/versions/20260726_c3d4e5f6a7b8_create_refresh_token.py
git commit -m "feat: add RefreshToken model and migration"
```

---

### Task 9: Write auth schemas (pydantic request/response models)

**Files:**
- Create: `cloud/backend/app/auth/schemas.py`

**Interfaces:**
- Produces:
  - `CarLoginRequest` — `phone: str, device_id: str, device_name: str, device_type: Literal["car","robot"], app_version: str | None`
  - `CarLoginResponse` — `access_token: str, refresh_token: str, expires_in: int, child_profile: ChildProfile`
  - `WechatLoginRequest` — `code: str`
  - `WechatLoginResponse` — `access_token: str, refresh_token: str, expires_in: int, is_new_user: bool, need_bind_phone: bool, profile: ParentProfile | None`
  - `PhoneBindRequest` — `phone: str`
  - `RefreshRequest` — `refresh_token: str`
  - `TokenPairResponse` — `access_token: str, refresh_token: str, expires_in: int`
- Consumes: nothing

- [ ] **Step 1: Write schemas**

Create `cloud/backend/app/auth/schemas.py`:

```python
"""Auth module request/response pydantic schemas."""

from typing import Literal

from pydantic import BaseModel, Field


# ── Shared ──────────────────────────────────────────────

class ChildProfile(BaseModel):
    """Minimal child profile returned after car login."""
    child_id: str
    nickname: str
    avatar_url: str | None = None
    family_id: str


class ParentProfile(BaseModel):
    """Parent profile returned after WeChat login."""
    parent_id: str
    nickname: str | None = None
    avatar_url: str | None = None
    phone_masked: str | None = None


class TokenPairResponse(BaseModel):
    """Access + refresh token pair."""
    access_token: str
    refresh_token: str
    expires_in: int = 7200


# ── Car login ───────────────────────────────────────────

class CarLoginRequest(BaseModel):
    """Request body for car phone-number login."""
    phone: str = Field(..., description="E.164 phone number, e.g. +8613800138000")
    device_id: str = Field(..., description="Device serial number / unique ID")
    device_name: str = Field(default="蛋仔机器人", description="Human-readable device name")
    device_type: Literal["car", "robot"] = "car"
    app_version: str | None = None


class CarLoginResponse(TokenPairResponse):
    """Car login success response."""
    child_profile: ChildProfile


# ── Parent WeChat login ─────────────────────────────────

class WechatLoginRequest(BaseModel):
    """Request body for parent WeChat mini-program login."""
    code: str = Field(..., description="wx.login() temporary code")


class WechatLoginResponse(TokenPairResponse):
    """WeChat login response."""
    is_new_user: bool = False
    need_bind_phone: bool = False
    profile: ParentProfile | None = None


# ── Phone binding ───────────────────────────────────────

class PhoneBindRequest(BaseModel):
    """Request body for binding phone number after WeChat login.

    Phase 1 simplified: plaintext phone. Later upgrade to
    wx.getPhoneNumber() encrypted data.
    """
    phone: str = Field(..., description="E.164 phone number")


class PhoneBindResponse(BaseModel):
    """Phone binding success response."""
    profile: ParentProfile


# ── Token refresh ───────────────────────────────────────

class RefreshRequest(BaseModel):
    """Request body for token refresh."""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Request body for logout (revoke refresh token)."""
    refresh_token: str
```

- [ ] **Step 2: Commit**

```bash
git add cloud/backend/app/auth/schemas.py
git commit -m "feat: add auth pydantic schemas (car login, wechat login, phone bind, refresh)"
```

---

### Task 10: Write auth security module (JWT sign/verify, token rotation, rate limiter)

**Files:**
- Create: `cloud/backend/app/auth/security.py`

**Interfaces:**
- Produces:
  - `hash_token(token: str) -> str` — SHA-256 hash of a token string
  - `create_access_token(device_id, child_id, family_id, scope) -> str` — sign a JWT access token
  - `create_parent_access_token(parent_id, scope) -> str` — sign a parent JWT access token
  - `decode_token(token: str) -> dict` — verify and decode a JWT, raises on invalid
  - `create_refresh_token_record(db, ...) -> str` — create RefreshToken row, return raw token
  - `rotate_refresh_token(db, old_raw_token) -> (str, RefreshToken)` — rotate (revoke old, create new), detect replay
  - `revoke_refresh_token(db, raw_token) -> None` — revoke a token by its raw value
  - `check_phone_login_rate_limit(ip: str) -> None` — raise if rate limit exceeded
- Consumes: `RefreshToken` model, config settings

- [ ] **Step 1: Write security module**

Create `cloud/backend/app/auth/security.py`:

```python
"""JWT token creation, verification, rotation, and rate limiting."""

import hashlib
import hmac
import time
import uuid
from datetime import datetime, timezone

import jwt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshToken
from app.config import settings


# ── Hashing ─────────────────────────────────────────────

def hash_token(token: str) -> str:
    """SHA-256 hash a token string for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def hash_phone(phone: str) -> str:
    """Deterministic SHA-256 hash of a phone number for lookup."""
    return hashlib.sha256(phone.encode()).hexdigest()


# ── JWT ─────────────────────────────────────────────────

def _base_payload(scope: str) -> dict:
    """Common JWT claims."""
    now = int(time.time())
    return {
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + settings.access_token_ttl_seconds,
        "iss": "danke-backend",
        "scope": scope,
    }


def create_access_token(
    device_id: str,
    child_id: str,
    family_id: str,
    scope: str = "car.learning.read car.learning.write car.chat car.messages car.files car.realtime",
) -> str:
    """Sign a JWT access token for the car device."""
    payload = {
        **_base_payload(scope),
        "sub": device_id,
        "child_id": child_id,
        "family_id": family_id,
        "sub_type": "device",
    }
    return jwt.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def create_parent_access_token(
    parent_id: str,
    scope: str = "parent.read parent.write parent.manage",
) -> str:
    """Sign a JWT access token for a parent (WeChat login)."""
    payload = {
        **_base_payload(scope),
        "sub": parent_id,
        "sub_type": "parent",
    }
    return jwt.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict:
    """Verify and decode a JWT token. Raises jwt.PyJWTError on failure."""
    return jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "iat", "jti", "sub", "scope"]},
    )


# ── Phone hash ──────────────────────────────────────────

def mask_phone(phone: str) -> str:
    """Mask phone number for display: +8613800138000 → 138****8000."""
    digits = phone.replace("+", "").replace("86", "", 1) if phone.startswith("+86") else phone
    if len(digits) >= 7:
        return f"{digits[:3]}****{digits[-4:]}"
    return digits


# ── Refresh token management ────────────────────────────

def _generate_refresh_token_raw() -> str:
    """Generate a cryptographically random refresh token string."""
    return secrets.token_urlsafe(48)


async def create_refresh_token_record(
    db: AsyncSession,
    *,
    parent_id: str | None = None,
    device_id: str | None = None,
    child_id: str | None = None,
    family_id: str | None = None,
) -> str:
    """Create a RefreshToken row and return the raw token."""
    raw = _generate_refresh_token_raw()
    token_hash = hash_token(raw)
    expires_at = datetime.now(timezone.utc).timestamp() + settings.refresh_token_ttl_seconds

    record = RefreshToken(
        token_hash=token_hash,
        parent_id=uuid.UUID(parent_id) if parent_id else None,
        device_id=device_id,
        child_id=uuid.UUID(child_id) if child_id else None,
        family_id=uuid.UUID(family_id) if family_id else None,
        expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc),
    )
    db.add(record)
    await db.flush()
    return raw


async def rotate_refresh_token(
    db: AsyncSession,
    old_raw_token: str,
) -> tuple[str, RefreshToken]:
    """Rotate a refresh token: revoke old, create new, detect replay.

    Returns (new_raw_token, new_record).

    If the old token was already revoked, revokes the entire rotation
    chain (replay detection) and raises ValueError.
    """
    old_hash = hash_token(old_raw_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == old_hash)
    )
    old_record = result.scalar_one_or_none()

    if old_record is None:
        raise ValueError("refresh_token_not_found")

    if old_record.revoked_at is not None:
        # Replay detected — revoke entire chain
        await _revoke_chain(db, old_record)
        await db.commit()
        raise ValueError("refresh_token_replayed")

    # Revoke old token
    old_record.revoked_at = datetime.now(timezone.utc)

    # Create new token, rotated from old
    new_raw = _generate_refresh_token_raw()
    new_hash = hash_token(new_raw)
    expires_at = datetime.now(timezone.utc).timestamp() + settings.refresh_token_ttl_seconds

    new_record = RefreshToken(
        token_hash=new_hash,
        parent_id=old_record.parent_id,
        device_id=old_record.device_id,
        child_id=old_record.child_id,
        family_id=old_record.family_id,
        expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc),
        rotated_from_id=old_record.id,
    )
    db.add(new_record)
    await db.flush()
    return new_raw, new_record


async def _revoke_chain(db: AsyncSession, record: RefreshToken) -> None:
    """Recursively revoke all tokens in the rotation chain."""
    now = datetime.now(timezone.utc)
    record.revoked_at = now
    if record.rotated_from_id:
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.id == record.rotated_from_id)
        )
        parent = result.scalar_one_or_none()
        if parent and parent.revoked_at is None:
            await _revoke_chain(db, parent)


async def revoke_refresh_token(db: AsyncSession, raw_token: str) -> None:
    """Revoke a refresh token by its raw value."""
    token_hash = hash_token(raw_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    record = result.scalar_one_or_none()
    if record and record.revoked_at is None:
        record.revoked_at = datetime.now(timezone.utc)
        await db.flush()


# ── Rate limiting (in-memory, single-worker only) ───────
# TODO: Replace with Redis-based rate limiter (lua script / sliding window)
# when multi-worker deployment is needed.

import secrets  # noqa: E402 (import at top is fine, but we need it only for _generate_refresh_token_raw)

_rate_limit_store: dict[str, list[float]] = {}


def check_phone_login_rate_limit(ip: str) -> None:
    """Check rate limit for phone login. Raises ValueError if exceeded.

    Single-worker only — each worker has its own in-memory counter.
    Docker Compose must use --workers 1.
    """
    now = time.time()
    window_start = now - 60  # 1 minute sliding window

    # Clean old entries
    if ip in _rate_limit_store:
        _rate_limit_store[ip] = [
            ts for ts in _rate_limit_store[ip] if ts > window_start
        ]
    else:
        _rate_limit_store[ip] = []

    if len(_rate_limit_store[ip]) >= settings.phone_login_rate_limit:
        raise ValueError("rate_limit_exceeded")

    _rate_limit_store[ip].append(now)
```

Note: `import secrets` at the top must be moved — it's used in `_generate_refresh_token_raw`. Fix the import order: move `import secrets` to the top imports block.

Fix the security.py imports (top of file):

```python
"""JWT token creation, verification, rotation, and rate limiting."""

import hashlib
import secrets
import time
import uuid
from datetime import datetime, timezone

import jwt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshToken
from app.config import settings
```

And remove the duplicate `import secrets` at the bottom.

- [ ] **Step 2: Verify module imports**

```powershell
cd d:/danke_robot/cloud/backend
python -c "from app.auth.security import hash_token, create_access_token, decode_token; print('auth.security OK')"
```

- [ ] **Step 3: Commit**

```bash
git add cloud/backend/app/auth/security.py
git commit -m "feat: add auth security module (JWT sign/verify, token rotation, rate limiter)"
```

---

### Task 11: Write auth dependencies (get_current_device, get_current_parent)

**Files:**
- Create: `cloud/backend/app/auth/dependencies.py`

**Interfaces:**
- Produces:
  - `get_current_device(request: Request, db: AsyncSession) -> dict[str, str]` — FastAPI dependency extracting `{device_id, child_id, family_id}` from Bearer token. Raises 401 on invalid/missing token.
  - `get_current_parent(request: Request, db: AsyncSession) -> str` — FastAPI dependency extracting `parent_id` from Bearer token. Raises 401.
- Consumes: `decode_token` from security.py, `get_db` from db.py

- [ ] **Step 1: Write dependencies**

Create `cloud/backend/app/auth/dependencies.py`:

```python
"""FastAPI dependencies for auth — extract identity from Bearer token."""

import jwt as pyjwt

from fastapi import Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import decode_token
from app.db import get_db
from app.schemas.common import error


async def get_current_device(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Extract device identity from Bearer token in Authorization header.

    Returns: {"device_id": str, "child_id": str, "family_id": str}

    Raises 401 JSONResponse on missing/invalid/expired token or wrong sub_type.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return _unauthorized("missing_token")

    token = auth_header[7:]  # strip "Bearer "
    try:
        payload = decode_token(token)
    except pyjwt.ExpiredSignatureError:
        return _unauthorized("token_expired")
    except pyjwt.PyJWTError:
        return _unauthorized("invalid_token")

    if payload.get("sub_type") != "device":
        return _unauthorized("wrong_token_type")

    return {
        "device_id": payload["sub"],
        "child_id": payload.get("child_id", ""),
        "family_id": payload.get("family_id", ""),
    }


async def get_current_parent(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> str:
    """Extract parent identity from Bearer token.

    Returns: parent_id as string.

    Raises 401 JSONResponse on missing/invalid/expired token or wrong sub_type.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return _unauthorized("missing_token")

    token = auth_header[7:]
    try:
        payload = decode_token(token)
    except pyjwt.ExpiredSignatureError:
        return _unauthorized("token_expired")
    except pyjwt.PyJWTError:
        return _unauthorized("invalid_token")

    if payload.get("sub_type") != "parent":
        return _unauthorized("wrong_token_type")

    return payload["sub"]


def _unauthorized(msg: str):
    """Return a 401 JSONResponse. Never returns — the caller should return this."""
    return JSONResponse(
        status_code=401,
        content=error(401, msg),
    )
```

Note: `_unauthorized` returns a `JSONResponse` because FastAPI dependencies can return a Response to short-circuit. The type checker will complain about the return type mismatch (`dict[str, str]` vs `JSONResponse`), but this is the standard FastAPI dependency pattern — it works at runtime. Add `# type: ignore` if needed.

- [ ] **Step 2: Verify imports**

```powershell
cd d:/danke_robot/cloud/backend
python -c "from app.auth.dependencies import get_current_device, get_current_parent; print('auth.dependencies OK')"
```

- [ ] **Step 3: Commit**

```bash
git add cloud/backend/app/auth/dependencies.py
git commit -m "feat: add auth dependencies (get_current_device, get_current_parent)"
```

---

### Task 12: Write car auth router (phone login, refresh, logout)

**Files:**
- Create: `cloud/backend/app/auth/router_car.py`

**Interfaces:**
- Produces:
  - `car_auth_router: APIRouter` with prefix `/auth`, tag `car-auth`
  - `POST /login` — phone login
  - `POST /refresh` — rotate refresh token
  - `POST /logout` — revoke refresh token
- Consumes: `hash_phone`, `create_access_token`, `create_refresh_token_record`, `rotate_refresh_token`, `revoke_refresh_token`, `check_phone_login_rate_limit`, `mask_phone` from security.py; schemas from schemas.py; `get_db` from db.py; models from models/

- [ ] **Step 1: Write car auth router**

Create `cloud/backend/app/auth/router_car.py`:

```python
"""Car device auth routes — phone number login, token refresh, logout."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import (
    CarLoginRequest,
    CarLoginResponse,
    ChildProfile,
    LogoutRequest,
    RefreshRequest,
    TokenPairResponse,
)
from app.auth.security import (
    check_phone_login_rate_limit,
    create_access_token,
    create_refresh_token_record,
    decode_token,
    hash_phone,
    mask_phone,
    revoke_refresh_token,
    rotate_refresh_token,
)
from app.db import get_db
from app.models.child import Child
from app.models.device_binding import DeviceBinding
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild
from app.schemas.common import error, ok

car_auth_router = APIRouter(prefix="/auth", tags=["car-auth"])


@car_auth_router.post("/login")
async def car_phone_login(
    body: CarLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Login with phone number for car device.

    1. Rate-limit by client IP
    2. Hash phone → find ParentAccount
    3. Resolve child via ParentChild (is_default=True)
    4. Create/update DeviceBinding
    5. Issue JWT access + refresh tokens
    6. Return CarLoginResponse
    """
    client_ip = request.client.host if request.client else "unknown"

    # Rate limit
    try:
        check_phone_login_rate_limit(client_ip)
    except ValueError:
        return JSONResponse(
            status_code=429,
            content=error(429, "rate_limit_exceeded"),
        )

    # Find parent by phone hash
    phone_hash = hash_phone(body.phone)
    result = await db.execute(
        select(ParentAccount).where(ParentAccount.phone_hash == phone_hash)
    )
    parent = result.scalar_one_or_none()

    if parent is None:
        return JSONResponse(
            status_code=404,
            content=error(404, "phone_not_bound"),
        )

    if parent.status != "active":
        return JSONResponse(
            status_code=403,
            content=error(403, "account_disabled"),
        )

    # Find default child
    # TODO: support multi-child selection on car login
    result = await db.execute(
        select(ParentChild, Child, Family)
        .join(Child, ParentChild.child_id == Child.id)
        .join(Family, Child.family_id == Family.id)
        .where(
            ParentChild.parent_id == parent.id,
            ParentChild.is_default == True,  # noqa: E712
        )
    )
    row = result.one_or_none()
    if row is None:
        return JSONResponse(
            status_code=404,
            content=error(404, "no_child_found"),
        )

    _pc, child, family = row

    # Create or update device binding
    result = await db.execute(
        select(DeviceBinding).where(
            DeviceBinding.device_id == body.device_id,
        )
    )
    binding = result.scalar_one_or_none()

    if binding is None:
        # Deactivate any existing active binding for this child
        result = await db.execute(
            select(DeviceBinding).where(
                DeviceBinding.child_id == child.id,
                DeviceBinding.bind_status == "active",
            )
        )
        old_binding = result.scalar_one_or_none()
        if old_binding:
            old_binding.bind_status = "inactive"

        binding = DeviceBinding(
            device_id=body.device_id,
            child_id=child.id,
            device_name=body.device_name,
            device_type=body.device_type,
            app_version=body.app_version,
            bind_status="active",
            bound_at=datetime.now(timezone.utc),
        )
        db.add(binding)
    else:
        binding.device_name = body.device_name
        binding.device_type = body.device_type
        binding.app_version = body.app_version
        binding.bind_status = "active"
        binding.bound_at = datetime.now(timezone.utc)

    await db.flush()

    # Issue tokens
    access_token = create_access_token(
        device_id=binding.device_id,
        child_id=str(child.id),
        family_id=str(family.id),
    )
    refresh_token_raw = await create_refresh_token_record(
        db,
        device_id=binding.device_id,
        child_id=str(child.id),
        family_id=str(family.id),
    )

    await db.commit()

    return ok(
        CarLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token_raw,
            expires_in=7200,
            child_profile=ChildProfile(
                child_id=str(child.id),
                nickname=child.nickname,
                avatar_url=child.avatar_url,
                family_id=str(family.id),
            ),
        ).model_dump()
    )


@car_auth_router.post("/refresh")
async def car_refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Rotate refresh token — revoke old, issue new pair."""
    try:
        new_raw, new_record = await rotate_refresh_token(db, body.refresh_token)
    except ValueError as e:
        msg = str(e)
        if msg == "refresh_token_replayed":
            return JSONResponse(
                status_code=401,
                content=error(401, "token_replayed"),
            )
        return JSONResponse(
            status_code=401,
            content=error(401, "invalid_refresh_token"),
        )

    # Issue new access token
    access_token = create_access_token(
        device_id=new_record.device_id or "",
        child_id=str(new_record.child_id) if new_record.child_id else "",
        family_id=str(new_record.family_id) if new_record.family_id else "",
    )

    await db.commit()

    return ok(
        TokenPairResponse(
            access_token=access_token,
            refresh_token=new_raw,
            expires_in=7200,
        ).model_dump()
    )


@car_auth_router.post("/logout")
async def car_logout(
    body: LogoutRequest,
    db: AsyncSession = Depends(get_db),
):
    """Revoke refresh token (logout)."""
    await revoke_refresh_token(db, body.refresh_token)
    await db.commit()
    return ok()
```

- [ ] **Step 2: Verify router compiles**

```powershell
cd d:/danke_robot/cloud/backend
python -c "from app.auth.router_car import car_auth_router; print('routes:', [r.path for r in car_auth_router.routes])"
```

- [ ] **Step 3: Commit**

```bash
git add cloud/backend/app/auth/router_car.py
git commit -m "feat: add car auth router (phone login, refresh, logout)"
```

---

### Task 13: Write parent auth router (WeChat login, phone bind, refresh, logout)

**Files:**
- Create: `cloud/backend/app/auth/router_parent.py`

**Interfaces:**
- Produces:
  - `parent_auth_router: APIRouter` with prefix `/auth`, tag `parent-auth`
  - `POST /wechat/login` — WeChat code → JWT
  - `POST /phone/bind` — bind phone after WeChat login
  - `POST /refresh` — rotate refresh token
  - `POST /logout` — revoke refresh token
- Consumes: same as router_car.py + `httpx` for WeChat API call

- [ ] **Step 1: Write parent auth router**

Create `cloud/backend/app/auth/router_parent.py`:

```python
"""Parent auth routes — WeChat login, phone binding, token refresh, logout."""

import httpx

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.auth.schemas import (
    LogoutRequest,
    ParentProfile,
    PhoneBindRequest,
    PhoneBindResponse,
    RefreshRequest,
    TokenPairResponse,
    WechatLoginRequest,
    WechatLoginResponse,
)
from app.auth.security import (
    create_parent_access_token,
    create_refresh_token_record,
    hash_phone,
    hash_token,
    mask_phone,
    revoke_refresh_token,
    rotate_refresh_token,
)
from app.config import settings
from app.db import get_db
from app.models.parent import ParentAccount
from app.schemas.common import error, ok

parent_auth_router = APIRouter(prefix="/auth", tags=["parent-auth"])


@parent_auth_router.post("/wechat/login")
async def wechat_login(
    body: WechatLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """WeChat mini-program login: exchange wx.login() code for JWT.

    1. Call WeChat jscode2session API
    2. Find or create ParentAccount by openid
    3. Issue JWT access + refresh tokens
    """
    wx_appid = settings.wx_appid
    wx_secret = settings.wx_secret.get_secret_value()

    if not wx_appid or not wx_secret:
        return JSONResponse(
            status_code=503,
            content=error(503, "wechat_not_configured"),
        )

    # Call WeChat API
    wx_url = (
        f"https://api.weixin.qq.com/sns/jscode2session"
        f"?appid={wx_appid}&secret={wx_secret}"
        f"&js_code={body.code}&grant_type=authorization_code"
    )

    try:
        async with httpx.AsyncClient() as client:
            wx_resp = await client.get(wx_url, timeout=10.0)
            wx_data = wx_resp.json()
    except httpx.HTTPError:
        return JSONResponse(
            status_code=502,
            content=error(502, "wechat_service_unavailable"),
        )

    wx_openid = wx_data.get("openid")
    if not wx_openid:
        wx_err_code = wx_data.get("errcode", "unknown")
        return JSONResponse(
            status_code=401,
            content=error(401, f"wechat_code_invalid: {wx_err_code}"),
        )

    wx_unionid = wx_data.get("unionid")

    # Find or create parent account
    result = await db.execute(
        select(ParentAccount).where(ParentAccount.wx_openid == wx_openid)
    )
    parent = result.scalar_one_or_none()

    is_new_user = False
    if parent is None:
        is_new_user = True
        parent = ParentAccount(
            wx_openid=wx_openid,
            wx_unionid=wx_unionid,
            status="pending_bind",
        )
        db.add(parent)
        await db.flush()

    need_bind_phone = parent.phone_hash is None

    # Issue tokens
    access_token = create_parent_access_token(parent_id=str(parent.id))
    refresh_token_raw = await create_refresh_token_record(
        db,
        parent_id=str(parent.id),
    )

    await db.commit()

    profile = None
    if not need_bind_phone:
        profile = ParentProfile(
            parent_id=str(parent.id),
            nickname=parent.nickname,
            avatar_url=parent.avatar_url,
            phone_masked=parent.phone_masked,
        )

    return ok(
        WechatLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token_raw,
            expires_in=7200,
            is_new_user=is_new_user,
            need_bind_phone=need_bind_phone,
            profile=profile,
        ).model_dump()
    )


@parent_auth_router.post("/phone/bind")
async def bind_phone(
    body: PhoneBindRequest,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Bind phone number to parent account (after WeChat login).

    Phase 1 simplified: plaintext phone input.
    """
    # Check if phone already bound to another account
    phone_hash = hash_phone(body.phone)
    result = await db.execute(
        select(ParentAccount).where(ParentAccount.phone_hash == phone_hash)
    )
    existing = result.scalar_one_or_none()
    if existing and str(existing.id) != parent_id:
        return JSONResponse(
            status_code=409,
            content=error(409, "phone_already_bound"),
        )

    # Update parent account
    result = await db.execute(
        select(ParentAccount).where(ParentAccount.id == parent_id)
    )
    parent = result.scalar_one_or_none()
    if parent is None:
        return JSONResponse(
            status_code=404,
            content=error(404, "parent_not_found"),
        )

    parent.phone_e164 = body.phone
    parent.phone_hash = phone_hash
    parent.phone_masked = mask_phone(body.phone)
    parent.status = "active"
    await db.commit()
    await db.refresh(parent)

    profile = ParentProfile(
        parent_id=str(parent.id),
        nickname=parent.nickname,
        avatar_url=parent.avatar_url,
        phone_masked=parent.phone_masked,
    )

    return ok(PhoneBindResponse(profile=profile).model_dump())


@parent_auth_router.post("/refresh")
async def parent_refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Rotate refresh token — revoke old, issue new pair."""
    try:
        new_raw, new_record = await rotate_refresh_token(db, body.refresh_token)
    except ValueError as e:
        msg = str(e)
        if msg == "refresh_token_replayed":
            return JSONResponse(
                status_code=401,
                content=error(401, "token_replayed"),
            )
        return JSONResponse(
            status_code=401,
            content=error(401, "invalid_refresh_token"),
        )

    access_token = create_parent_access_token(
        parent_id=str(new_record.parent_id) if new_record.parent_id else "",
    )

    await db.commit()

    return ok(
        TokenPairResponse(
            access_token=access_token,
            refresh_token=new_raw,
            expires_in=7200,
        ).model_dump()
    )


@parent_auth_router.post("/logout")
async def parent_logout(
    body: LogoutRequest,
    db: AsyncSession = Depends(get_db),
):
    """Revoke refresh token (logout)."""
    await revoke_refresh_token(db, body.refresh_token)
    await db.commit()
    return ok()
```

- [ ] **Step 2: Verify router compiles**

```powershell
cd d:/danke_robot/cloud/backend
python -c "from app.auth.router_parent import parent_auth_router; print('routes:', [r.path for r in parent_auth_router.routes])"
```

- [ ] **Step 3: Commit**

```bash
git add cloud/backend/app/auth/router_parent.py
git commit -m "feat: add parent auth router (WeChat login, phone bind, refresh, logout)"
```

---

### Task 14: Wire auth routers into top-level router

**Files:**
- Modify: `cloud/backend/app/router.py`
- Modify: `cloud/backend/app/main.py` (update docs description)

**Interfaces:**
- Modifies: `top_router` now includes `car_auth_router` under `/v1/api/car` and `parent_auth_router` under `/v1/api/parent`

- [ ] **Step 1: Update router.py**

Replace `cloud/backend/app/router.py`:

```python
"""Top-level router aggregation."""

from fastapi import APIRouter

from app.auth.router_car import car_auth_router
from app.auth.router_parent import parent_auth_router

top_router = APIRouter()

# Health check
@top_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"code": 0, "msg": "ok", "data": {"status": "healthy"}}

# Car device API
car_router = APIRouter(prefix="/v1/api/car")
car_router.include_router(car_auth_router)
top_router.include_router(car_router)

# Parent mini-program API
parent_router = APIRouter(prefix="/v1/api/parent")
parent_router.include_router(parent_auth_router)
top_router.include_router(parent_router)
```

Full paths:
- `POST /v1/api/car/auth/login`
- `POST /v1/api/parent/auth/wechat/login`
- `GET /health`

- [ ] **Step 2: Verify app starts and all routes appear**

```powershell
cd d:/danke_robot/cloud/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
Start-Sleep -Seconds 3
$response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
Write-Host "Health check: $($response | ConvertTo-Json)"

# Check OpenAPI docs are accessible
$openapi = Invoke-RestMethod -Uri "http://localhost:8000/openapi.json" -Method Get
Write-Host "Routes found: $($openapi.paths.Count)"
$openapi.paths | Get-Member -MemberType NoteProperty | ForEach-Object { Write-Host $_.Name }
```

Expected: `/health`, `/v1/api/car/auth/login`, `/v1/api/car/auth/refresh`, `/v1/api/car/auth/logout`, `/v1/api/parent/auth/wechat/login`, `/v1/api/parent/auth/phone/bind`, `/v1/api/parent/auth/refresh`, `/v1/api/parent/auth/logout`

- [ ] **Step 3: Commit**

```bash
git add cloud/backend/app/router.py
git commit -m "feat: wire auth routers into top-level router"
```

---

### Task 15: Create LearningEvent model, migration, and telemetry module

**Files:**
- Create: `cloud/backend/app/telemetry/__init__.py`
- Create: `cloud/backend/app/telemetry/models.py`
- Create: `cloud/backend/app/telemetry/schemas.py`
- Create: `cloud/backend/app/telemetry/service.py`
- Create: `cloud/backend/app/telemetry/router.py`
- Create: `cloud/backend/alembic/versions/20260726_d4e5f6a7b8c9_create_learning_event.py`

**Interfaces:**
- Produces:
  - `LearningEvent` model
  - `LearningEventSchema`, `BatchEventsRequest`, `BatchEventsResponse`
  - `insert_events(db, device_id, child_id, events) -> list[LearningEvent]`
  - `telemetry_router: APIRouter` — `POST /telemetry/events:batch`
- Consumes: `get_current_device` dependency, `ok`/`error` helpers

- [ ] **Step 1: Write LearningEvent model**

Create `cloud/backend/app/telemetry/__init__.py`:
```python
"""Telemetry module — learning event ingestion and idempotent storage."""
```

Create `cloud/backend/app/telemetry/models.py`:

```python
"""Learning event model for car device telemetry."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class LearningEvent(Base):
    """An idempotent learning event reported by a car device.

    event_id is generated by the car (UUID v4) and used for
    idempotency: duplicate (device_id, event_id) pairs are silently
    accepted but not duplicated.
    """

    __tablename__ = "learning_event"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    device_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("device_binding.device_id"),
        nullable=False,
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("child.id"),
        nullable=False,
    )
    event_id: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="Client-generated idempotency key (UUID v4)"
    )
    event_type: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="e.g. learning.session.start, learning.answer.submit"
    )
    module: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="One of: science, math, english, poems, music, quiz"
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="Event occurrence time from the device"
    )
    payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict,
        comment="Arbitrary event data"
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Server receive time"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("device_id", "event_id", name="uq_learning_event_device_event"),
        Index("idx_learning_event_device", "device_id"),
        Index("idx_learning_event_child", "child_id"),
        Index("idx_learning_event_type", "event_type"),
        Index("idx_learning_event_timestamp", "timestamp"),
    )
```

- [ ] **Step 2: Create migration**

Create `cloud/backend/alembic/versions/20260726_d4e5f6a7b8c9_create_learning_event.py`:

```python
"""create learning_event

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-26 09:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create learning_event table."""
    op.create_table(
        'learning_event',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            'device_id',
            sa.Text(),
            sa.ForeignKey('device_binding.device_id'),
            nullable=False,
        ),
        sa.Column(
            'child_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('child.id'),
            nullable=False,
        ),
        sa.Column(
            'event_id',
            sa.Text(),
            nullable=False,
            comment='Client-generated idempotency key (UUID v4)',
        ),
        sa.Column(
            'event_type',
            sa.Text(),
            nullable=False,
            comment='e.g. learning.session.start, learning.answer.submit',
        ),
        sa.Column(
            'module',
            sa.Text(),
            nullable=True,
            comment='One of: science, math, english, poems, music, quiz',
        ),
        sa.Column(
            'timestamp',
            sa.DateTime(timezone=True),
            nullable=False,
            comment='Event occurrence time from the device',
        ),
        sa.Column(
            'payload',
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'"),
            comment='Arbitrary event data',
        ),
        sa.Column(
            'received_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
            comment='Server receive time',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.UniqueConstraint('device_id', 'event_id', name='uq_learning_event_device_event'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_learning_event_device', 'learning_event', ['device_id'])
    op.create_index('idx_learning_event_child', 'learning_event', ['child_id'])
    op.create_index('idx_learning_event_type', 'learning_event', ['event_type'])
    op.create_index('idx_learning_event_timestamp', 'learning_event', ['timestamp'])


def downgrade() -> None:
    """Drop learning_event table."""
    op.drop_table('learning_event')
```

- [ ] **Step 3: Write telemetry schemas**

Create `cloud/backend/app/telemetry/schemas.py`:

```python
"""Telemetry request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class EventItem(BaseModel):
    """A single telemetry event from the car device."""
    event_id: str = Field(..., description="UUID v4 idempotency key")
    event_type: str = Field(..., description="e.g. learning.session.start")
    module: str | None = Field(None, description="Learning module: science, math, etc.")
    timestamp: datetime = Field(..., description="Event occurrence time (ISO 8601 with offset)")
    payload: dict = Field(default_factory=dict, description="Arbitrary event data")


class BatchEventsRequest(BaseModel):
    """Batch event upload request."""
    events: list[EventItem] = Field(..., min_length=1, max_length=100)


class BatchEventsResponse(BaseModel):
    """Batch event upload response."""
    accepted: int = Field(..., description="Number of events accepted")
    duplicates: int = Field(default=0, description="Number of duplicate events skipped")
```

- [ ] **Step 4: Write telemetry service**

Create `cloud/backend/app/telemetry/service.py`:

```python
"""Telemetry event ingestion with idempotency."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.telemetry.models import LearningEvent


async def insert_events(
    db: AsyncSession,
    device_id: str,
    child_id: str,
    events: list[dict],
) -> tuple[int, int]:
    """Insert events with idempotency. Returns (accepted, duplicates).

    Uses PostgreSQL ON CONFLICT DO NOTHING for idempotent inserts.
    Duplicate (device_id, event_id) pairs are silently skipped.
    """
    accepted = 0
    duplicates = 0

    for event in events:
        stmt = (
            pg_insert(LearningEvent)
            .values(
                device_id=device_id,
                child_id=child_id,
                event_id=event["event_id"],
                event_type=event["event_type"],
                module=event.get("module"),
                timestamp=event["timestamp"],
                payload=event.get("payload", {}),
            )
            .on_conflict_do_nothing(
                index_elements=["device_id", "event_id"],
            )
        )
        result = await db.execute(stmt)
        if result.rowcount and result.rowcount > 0:
            accepted += 1
        else:
            duplicates += 1

    await db.flush()
    return accepted, duplicates
```

- [ ] **Step 5: Write telemetry router**

Create `cloud/backend/app/telemetry/router.py`:

```python
"""Telemetry event ingestion routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_device
from app.db import get_db
from app.schemas.common import error, ok
from app.telemetry.schemas import BatchEventsRequest
from app.telemetry.service import insert_events

telemetry_router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@telemetry_router.post("/events:batch")
async def batch_events(
    body: BatchEventsRequest,
    device: dict = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
):
    """Ingest a batch of telemetry events from a car device.

    Idempotent: duplicate event_id values are silently accepted but not
    duplicated in storage.
    """
    device_id = device["device_id"]
    child_id = device["child_id"]

    if not child_id:
        return error(400, "missing_child_id")

    events_data = [
        {
            "event_id": e.event_id,
            "event_type": e.event_type,
            "module": e.module,
            "timestamp": e.timestamp,
            "payload": e.payload,
        }
        for e in body.events
    ]

    accepted, duplicates = await insert_events(
        db, device_id, child_id, events_data
    )
    await db.commit()

    return ok({"accepted": accepted, "duplicates": duplicates})
```

- [ ] **Step 6: Wire telemetry router**

Append to `cloud/backend/app/router.py` — update the car_router section:

```python
from app.telemetry.router import telemetry_router

# ... existing car_router setup ...
car_router.include_router(telemetry_router)
# ... rest stays the same ...
```

The full updated router.py:

```python
"""Top-level router aggregation."""

from fastapi import APIRouter

from app.auth.router_car import car_auth_router
from app.auth.router_parent import parent_auth_router
from app.telemetry.router import telemetry_router

top_router = APIRouter()


@top_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"code": 0, "msg": "ok", "data": {"status": "healthy"}}


# Car device API
car_router = APIRouter(prefix="/v1/api/car")
car_router.include_router(car_auth_router)
car_router.include_router(telemetry_router)
top_router.include_router(car_router)

# Parent mini-program API
parent_router = APIRouter(prefix="/v1/api/parent")
parent_router.include_router(parent_auth_router)
top_router.include_router(parent_router)
```

- [ ] **Step 7: Run migration and verify**

```powershell
cd d:/danke_robot/cloud/backend
alembic upgrade head
python -c "from app.telemetry.models import LearningEvent; from app.telemetry.router import telemetry_router; print('telemetry OK')"
```

- [ ] **Step 8: Commit**

```bash
git add cloud/backend/app/telemetry/ \
        cloud/backend/app/router.py \
        cloud/backend/alembic/versions/20260726_d4e5f6a7b8c9_create_learning_event.py
git commit -m "feat: add telemetry module (LearningEvent model, batch event ingestion with idempotency)"
```

---

### Task 16: Update Alembic env.py to import new models

**Files:**
- Modify: `cloud/backend/alembic/env.py`

- [ ] **Step 1: Add new model imports**

In `cloud/backend/alembic/env.py`, replace the import line:

```python
# Old:
from app.models import child, device_binding, family, parent, parent_child  # noqa: F401

# New:
from app.models import child, device_binding, family, parent, parent_child  # noqa: F401
from app.auth.models import RefreshToken  # noqa: F401
from app.telemetry.models import LearningEvent  # noqa: F401
```

- [ ] **Step 2: Verify alembic sees all models**

```powershell
cd d:/danke_robot/cloud/backend
# Should produce no new migration (autogenerate detects nothing)
alembic revision --autogenerate -m "check" --rev-id check001
# If it creates a migration with no changes, delete it
Remove-Item alembic/versions/check001_*.py -ErrorAction SilentlyContinue
```

Expected: No schema changes detected (all tables already created via explicit migrations).

- [ ] **Step 3: Commit**

```bash
git add cloud/backend/alembic/env.py
git commit -m "fix: import new models (RefreshToken, LearningEvent) in alembic env.py"
```

---

### Task 17: Create car screen LoginView.vue

**Files:**
- Create: `car/screen/src/views/LoginView.vue`
- Modify: `car/screen/src/router/index.js`

**Interfaces:**
- Produces: Login page with phone number keypad, hand-drawn doodle style. On success, stores token and navigates to `/`.
- Consumes: Design tokens from `design-tokens.css`, `router.push('/')` on success

- [ ] **Step 1: Write LoginView.vue**

Create `car/screen/src/views/LoginView.vue`:

```vue
<template>
  <div class="login">
    <!-- Status bar -->
    <div class="status-bar">
      <span>蛋仔机器人</span>
      <span>🔒 家长登录</span>
    </div>

    <!-- Card -->
    <div class="login__card card-sketch">
      <!-- Tape decoration -->
      <svg class="doodle-tape" viewBox="0 0 40 18" width="40" height="18"
           style="top: -8px; left: 50%; transform: translateX(-50%) rotate(-6deg);">
        <rect x="2" y="0" width="36" height="18" rx="3" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="1.5" opacity="0.7"/>
      </svg>

      <h2 class="login__title">家长登录</h2>
      <p class="login__desc">输入绑定手机号激活设备</p>

      <!-- Phone display -->
      <div class="login__phone-display">
        <span class="login__phone-text">{{ phoneNumber || '请输入手机号' }}</span>
        <span class="login__cursor" v-if="phoneNumber.length < 11">|</span>
      </div>

      <!-- Error message -->
      <div class="login__error" v-if="errorMsg">{{ errorMsg }}</div>

      <!-- Number keypad -->
      <div class="login__keypad">
        <button class="login__key" v-for="n in 9" :key="n" @click="addDigit(n)">{{ n }}</button>
        <button class="login__key login__key--empty" disabled></button>
        <button class="login__key" @click="addDigit(0)">0</button>
        <button class="login__key login__key--del" @click="removeDigit">
          <i class="ri-delete-back-line"></i>
        </button>
      </div>

      <!-- Submit -->
      <button
        class="btn-sketch btn-sketch--primary login__submit"
        :disabled="phoneNumber.length < 11 || loading"
        @click="submitLogin"
      >
        {{ loading ? '绑定中...' : '开始使用 →' }}
      </button>
    </div>

    <!-- Doodle decorations -->
    <svg class="doodle-star login__star" viewBox="0 0 30 30" width="20" height="20">
      <path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z"
            fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/>
    </svg>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login, saveToken } from '../utils/api.js'

const router = useRouter()
const phoneNumber = ref('')
const loading = ref(false)
const errorMsg = ref('')

function addDigit(n) {
  if (phoneNumber.value.length < 11) {
    phoneNumber.value += String(n)
    errorMsg.value = ''
  }
}

function removeDigit() {
  phoneNumber.value = phoneNumber.value.slice(0, -1)
  errorMsg.value = ''
}

async function submitLogin() {
  if (phoneNumber.value.length < 11) return

  // Format to E.164: assume Chinese number, prepend +86
  const rawPhone = phoneNumber.value
  const e164Phone = rawPhone.startsWith('+86')
    ? rawPhone
    : `+86${rawPhone}`

  loading.value = true
  errorMsg.value = ''

  try {
    const result = await login(e164Phone)
    saveToken(result.access_token, result.refresh_token)
    router.push('/')
  } catch (err) {
    if (err.message === 'phone_not_bound') {
      errorMsg.value = '该手机号未绑定，请先在家长小程序中注册'
    } else if (err.message === 'rate_limit_exceeded') {
      errorMsg.value = '操作太频繁，请稍后再试'
    } else {
      errorMsg.value = '网络出小差了，请检查连接后重试'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login {
  width: var(--screen-w);
  height: var(--screen-h);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  background: var(--bg-sky);
}

.login__card {
  width: 420px;
  padding: var(--space-8) var(--space-8) var(--space-6);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  position: relative;
  z-index: var(--z-card);
}

.login__title {
  font-family: var(--font-heading);
  font-size: var(--text-2xl);
  color: var(--ink-black);
  font-weight: 400;
}

.login__desc {
  font-family: var(--font-body);
  font-size: var(--text-sm);
  color: var(--ink-muted);
}

.login__phone-display {
  width: 100%;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: var(--border-w) solid var(--ink-black);
  border-radius: 14px 18px 14px 16px;
  background: var(--bg-cream);
  box-shadow: 2px 2px 0 var(--ink-black);
}

.login__phone-text {
  font-family: var(--font-heading);
  font-size: var(--text-xl);
  color: var(--ink-black);
  letter-spacing: 3px;
}

.login__cursor {
  font-size: var(--text-xl);
  color: var(--brand-coral);
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.login__error {
  font-family: var(--font-body);
  font-size: var(--text-sm);
  color: var(--marker-red);
  text-align: center;
  min-height: 20px;
}

.login__keypad {
  display: grid;
  grid-template-columns: repeat(3, 80px);
  gap: var(--space-3);
  justify-content: center;
  padding-top: var(--space-2);
}

.login__key {
  width: 80px;
  height: var(--touch-btn);
  border: var(--border-w) solid var(--ink-black);
  border-radius: 16px 20px 14px 18px;
  background: var(--bg-card);
  font-family: var(--font-heading);
  font-size: var(--text-xl);
  color: var(--ink-black);
  cursor: pointer;
  box-shadow: 3px 3px 0 var(--ink-black);
  transition: transform var(--dur-fast) var(--ease-bounce);
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.login__key:active {
  transform: scale(0.9) translate(2px, 2px);
  box-shadow: 1px 1px 0 var(--ink-black);
}

.login__key--empty {
  visibility: hidden;
}

.login__key--del {
  font-size: var(--text-lg);
  background: var(--bg-mint);
}

.login__submit {
  width: 100%;
  margin-top: var(--space-2);
}

.login__submit:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.login__star {
  position: absolute;
  top: 30px;
  right: 60px;
  z-index: var(--z-base);
}
</style>
```

- [ ] **Step 2: Add /login route and auth guard**

Update `car/screen/src/router/index.js`:

```javascript
import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import TaskListView from '../views/TaskListView.vue'
import ChallengeView from '../views/ChallengeView.vue'
import CelebrateView from '../views/CelebrateView.vue'
import ChatView from '../views/ChatView.vue'
import LearningView from '../views/LearningView.vue'
import ScienceView from '../views/ScienceView.vue'
import MathView from '../views/MathView.vue'
import EnglishView from '../views/EnglishView.vue'
import PoemsView from '../views/PoemsView.vue'
import MusicView from '../views/MusicView.vue'
import QuizView from '../views/QuizView.vue'
import QaBoxView from '../views/QaBoxView.vue'
import MessagesView from '../views/MessagesView.vue'
import IdleView from '../views/IdleView.vue'
import { getToken } from '../utils/api.js'

const routes = [
  { path: '/login', component: LoginView, meta: { scene: 'login' } },
  { path: '/', component: HomeView, meta: { scene: 'home', requiresAuth: true } },
  { path: '/tasks', component: TaskListView, meta: { scene: 'tasks', requiresAuth: true } },
  { path: '/challenge', component: ChallengeView, meta: { scene: 'challenge', requiresAuth: true } },
  { path: '/celebrate', component: CelebrateView, meta: { scene: 'celebrate', requiresAuth: true } },
  { path: '/chat', component: ChatView, meta: { scene: 'chat', requiresAuth: true } },
  { path: '/learning', component: LearningView, meta: { scene: 'learning', requiresAuth: true } },
  { path: '/science', component: ScienceView, meta: { scene: 'science', requiresAuth: true } },
  { path: '/math', component: MathView, meta: { scene: 'math', requiresAuth: true } },
  { path: '/english', component: EnglishView, meta: { scene: 'english', requiresAuth: true } },
  { path: '/poems', component: PoemsView, meta: { scene: 'poems', requiresAuth: true } },
  { path: '/music', component: MusicView, meta: { scene: 'music', requiresAuth: true } },
  { path: '/quiz', component: QuizView, meta: { scene: 'quiz', requiresAuth: true } },
  { path: '/qabox', component: QaBoxView, meta: { scene: 'qabox', requiresAuth: true } },
  { path: '/messages', component: MessagesView, meta: { scene: 'messages', requiresAuth: true } },
  { path: '/idle', component: IdleView, meta: { scene: 'idle', requiresAuth: true } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

// Auth guard
router.beforeEach((to, from, next) => {
  const token = getToken()
  if (to.path === '/login') {
    // Already logged in → go home
    if (token) return next('/')
    return next()
  }
  if (to.meta.requiresAuth && !token) {
    return next('/login')
  }
  next()
})

export default router
```

- [ ] **Step 3: Commit**

```bash
git add car/screen/src/views/LoginView.vue car/screen/src/router/index.js
git commit -m "feat: add car screen login page with phone keypad and auth guard"
```

---

### Task 18: Create car screen API utility (network layer)

**Files:**
- Create: `car/screen/src/utils/api.js`

**Interfaces:**
- Produces:
  - `getToken()` — returns access_token from localStorage
  - `saveToken(access, refresh)` — saves token pair to localStorage
  - `clearToken()` — removes token from localStorage
  - `login(phone)` — POST /v1/api/car/auth/login, returns {access_token, refresh_token, ...}
  - `apiClient` — fetch wrapper with auto token injection and refresh on 401

- [ ] **Step 1: Write api.js**

Create `car/screen/src/utils/api.js`:

```javascript
/**
 * Network layer for car screen.
 *
 * - Wraps fetch() with automatic Bearer token injection
 * - Auto-refreshes on 401 using refresh_token
 * - Exports login() for phone authentication
 */

const API_BASE = 'http://localhost:8000'

// ── Token storage ────────────────────────────────────────

export function getToken() {
  return localStorage.getItem('access_token')
}

export function getRefreshToken() {
  return localStorage.getItem('refresh_token')
}

export function saveToken(accessToken, refreshToken) {
  localStorage.setItem('access_token', accessToken)
  localStorage.setItem('refresh_token', refreshToken)
}

export function clearToken() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

// ── API helpers ──────────────────────────────────────────

async function refreshAccessToken() {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    clearToken()
    throw new Error('no_refresh_token')
  }

  const res = await fetch(`${API_BASE}/v1/api/car/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })

  if (!res.ok) {
    clearToken()
    throw new Error('refresh_failed')
  }

  const body = await res.json()
  saveToken(body.data.access_token, body.data.refresh_token)
  return body.data.access_token
}

/**
 * Authenticated fetch wrapper.
 *
 * Automatically injects Authorization header. On 401, attempts a
 * one-time token refresh and retries. If refresh fails, clears
 * token and redirects to login.
 */
export async function apiFetch(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  let res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  // Auto-refresh on 401
  if (res.status === 401 && token) {
    try {
      const newToken = await refreshAccessToken()
      headers['Authorization'] = `Bearer ${newToken}`
      res = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers,
      })
    } catch {
      clearToken()
      window.location.hash = '#/login'
      throw new Error('auth_lost')
    }
  }

  return res
}

// ── Auth API ─────────────────────────────────────────────

/**
 * Login with phone number.
 *
 * @param {string} phone - E.164 formatted phone number
 * @returns {Promise<object>} { access_token, refresh_token, expires_in, child_profile }
 */
export async function login(phone) {
  // Simple device ID: use a stored ID or generate one
  let deviceId = localStorage.getItem('device_id')
  if (!deviceId) {
    deviceId = 'car-' + crypto.randomUUID()
    localStorage.setItem('device_id', deviceId)
  }

  const res = await fetch(`${API_BASE}/v1/api/car/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      phone,
      device_id: deviceId,
      device_name: '蛋仔机器人',
      device_type: 'car',
    }),
  })

  const body = await res.json()

  if (!res.ok || body.code !== 0) {
    throw new Error(body.msg || 'login_failed')
  }

  return body.data
}
```

- [ ] **Step 2: Verify the Vue project builds**

```powershell
cd d:/danke_robot/car/screen
npm install   # if not already installed
npm run build
```

Expected: No build errors. LoginView.vue and api.js compiled successfully.

- [ ] **Step 3: Commit**

```bash
git add car/screen/src/utils/api.js
git commit -m "feat: add car screen network layer (api fetch wrapper with auto token refresh)"
```

---

### Task 19: Create Dockerfile and docker-compose.yml

**Files:**
- Create: `cloud/backend/Dockerfile`
- Create: `cloud/backend/.dockerignore`
- Create: `cloud/backend/docker-compose.yml`

- [ ] **Step 1: Write Dockerfile**

Create `cloud/backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e . && pip install --no-cache-dir httpx PyJWT

# Copy application code
COPY . .

# Run with single worker for in-memory rate limiter compatibility
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

- [ ] **Step 2: Write .dockerignore**

Create `cloud/backend/.dockerignore`:

```
__pycache__
*.pyc
.pytest_cache
.ruff_cache
.git
.env
.venv
node_modules
alembic/versions/__pycache__
tests/__pycache__
```

- [ ] **Step 3: Write docker-compose.yml**

Create `cloud/backend/docker-compose.yml`:

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: parent
      POSTGRES_PASSWORD: parent
      POSTGRES_DB: parent_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U parent -d parent_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    environment:
      - APP_ENV=dev
      - LOG_LEVEL=INFO
      - DATABASE_URL=postgresql+asyncpg://parent:parent@db:5432/parent_db
      - JWT_SECRET=dev-secret-change-in-production
      - WX_APPID=
      - WX_SECRET=

volumes:
  pgdata:
```

- [ ] **Step 4: Verify docker-compose starts**

```powershell
cd d:/danke_robot/cloud/backend
docker compose up -d db
Start-Sleep -Seconds 5
docker compose run --rm backend alembic upgrade head
docker compose up -d backend
Start-Sleep -Seconds 3
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
```

Expected: `{"code": 0, "msg": "ok", "data": {"status": "healthy"}}`

Cleanup: `docker compose down`

- [ ] **Step 5: Commit**

```bash
git add cloud/backend/Dockerfile \
        cloud/backend/.dockerignore \
        cloud/backend/docker-compose.yml
git commit -m "feat: add Dockerfile and docker-compose.yml for containerized deployment"
```

---

### Task 20: Write integration tests

**Files:**
- Create: `cloud/backend/tests/test_auth_car_api.py`
- Create: `cloud/backend/tests/test_auth_parent_api.py`
- Create: `cloud/backend/tests/test_telemetry_api.py`
- Modify: `cloud/backend/tests/conftest.py`

**Interfaces:**
- Consumes: `app` from `app.main`, `get_db` from `app.db`, all models

- [ ] **Step 1: Add async_client fixture to conftest.py**

Append to `cloud/backend/tests/conftest.py`:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
async def async_client(engine, tables):
    """Create an httpx AsyncClient backed by the FastAPI test app."""
    # Override the app's get_db to use the test engine
    from app.db import AsyncSessionLocal

    # Create a fresh app for testing
    test_app = create_app()

    # Override get_db dependency to use test session
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

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

    test_app.dependency_overrides = {}
    # We can't easily override get_db globally without restructuring.
    # Instead, tests use the engine fixture directly for setup and
    # the client for HTTP calls, relying on the app's real DB connection.
    #
    # For simplicity in skeleton phase, integration tests connect to
    # the same test DB referenced by settings.database_url.

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
```

- [ ] **Step 2: Write car auth API tests**

Create `cloud/backend/tests/test_auth_car_api.py`:

```python
"""Integration tests for car auth API endpoints."""

import pytest
from httpx import AsyncClient

from app.models.child import Child
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild


@pytest.fixture
async def car_login_setup(db_session):
    """Create test data: family, child, parent, parent-child binding."""
    family = Family(name="测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="小测试")
    db_session.add(child)
    await db_session.flush()

    parent = ParentAccount(
        phone_e164="+8613800138000",
        phone_hash="abc123def456",
        phone_masked="138****8000",
        status="active",
    )
    db_session.add(parent)
    await db_session.flush()

    pc = ParentChild(
        parent_id=parent.id,
        family_id=family.id,
        child_id=child.id,
        is_default=True,
    )
    db_session.add(pc)
    await db_session.commit()

    return {
        "phone": "+8613800138000",
        "phone_hash": "abc123def456",
        "family_id": str(family.id),
        "child_id": str(child.id),
        "parent_id": str(parent.id),
    }


@pytest.mark.asyncio
async def test_car_login_success(async_client: AsyncClient, car_login_setup, db_session):
    """POST /v1/api/car/auth/login with valid phone returns token pair and child profile."""
    res = await async_client.post("/v1/api/car/auth/login", json={
        "phone": car_login_setup["phone"],
        "device_id": "TEST-DEV-001",
        "device_name": "测试设备",
        "device_type": "car",
    })

    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["access_token"] is not None
    assert body["data"]["refresh_token"] is not None
    assert body["data"]["expires_in"] == 7200
    assert body["data"]["child_profile"]["nickname"] == "小测试"


@pytest.mark.asyncio
async def test_car_login_phone_not_bound(async_client: AsyncClient):
    """POST /v1/api/car/auth/login with unknown phone returns 404."""
    res = await async_client.post("/v1/api/car/auth/login", json={
        "phone": "+8613900000000",
        "device_id": "TEST-DEV-002",
        "device_name": "未知设备",
        "device_type": "car",
    })

    assert res.status_code == 404
    body = res.json()
    assert body["msg"] == "phone_not_bound"


@pytest.mark.asyncio
async def test_car_refresh_token(async_client: AsyncClient, car_login_setup):
    """POST /v1/api/car/auth/refresh with valid refresh token returns new pair."""
    # First login to get tokens
    login_res = await async_client.post("/v1/api/car/auth/login", json={
        "phone": car_login_setup["phone"],
        "device_id": "TEST-DEV-003",
        "device_name": "刷新测试",
        "device_type": "car",
    })
    refresh_token = login_res.json()["data"]["refresh_token"]

    # Now refresh
    res = await async_client.post("/v1/api/car/auth/refresh", json={
        "refresh_token": refresh_token,
    })

    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["access_token"] is not None
    assert body["data"]["refresh_token"] is not None


@pytest.mark.asyncio
async def test_car_refresh_replay_detected(async_client: AsyncClient, car_login_setup):
    """Using the same refresh token twice triggers replay detection."""
    login_res = await async_client.post("/v1/api/car/auth/login", json={
        "phone": car_login_setup["phone"],
        "device_id": "TEST-DEV-004",
        "device_name": "重放测试",
        "device_type": "car",
    })
    refresh_token = login_res.json()["data"]["refresh_token"]

    # First refresh — OK
    res1 = await async_client.post("/v1/api/car/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert res1.status_code == 200

    # Second refresh with same token — replay detected
    res2 = await async_client.post("/v1/api/car/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert res2.status_code == 401
    assert res2.json()["msg"] == "token_replayed"


@pytest.mark.asyncio
async def test_car_logout(async_client: AsyncClient, car_login_setup):
    """POST /v1/api/car/auth/logout revokes refresh token."""
    login_res = await async_client.post("/v1/api/car/auth/login", json={
        "phone": car_login_setup["phone"],
        "device_id": "TEST-DEV-005",
        "device_name": "登出测试",
        "device_type": "car",
    })
    refresh_token = login_res.json()["data"]["refresh_token"]

    # Logout
    res = await async_client.post("/v1/api/car/auth/logout", json={
        "refresh_token": refresh_token,
    })
    assert res.status_code == 200
    assert res.json()["code"] == 0
```

- [ ] **Step 3: Write telemetry API tests**

Create `cloud/backend/tests/test_telemetry_api.py`:

```python
"""Integration tests for telemetry event ingestion."""

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from app.models.child import Child
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild


@pytest.fixture
async def telemetry_setup(db_session):
    """Create test data with an active device binding."""
    family = Family(name="遥测家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="遥测孩子")
    db_session.add(child)
    await db_session.flush()

    parent = ParentAccount(
        phone_e164="+8613800138001",
        phone_hash="telemetry_test_hash_001",
        phone_masked="138****8001",
        status="active",
    )
    db_session.add(parent)
    await db_session.flush()

    pc = ParentChild(
        parent_id=parent.id,
        family_id=family.id,
        child_id=child.id,
        is_default=True,
    )
    db_session.add(pc)
    await db_session.commit()

    return {
        "phone": "+8613800138001",
        "family_id": str(family.id),
        "child_id": str(child.id),
    }


@pytest.mark.asyncio
async def test_batch_events(async_client: AsyncClient, telemetry_setup):
    """POST /v1/api/car/telemetry/events:batch accepts events."""
    # Login first
    login_res = await async_client.post("/v1/api/car/auth/login", json={
        "phone": telemetry_setup["phone"],
        "device_id": "TELEM-DEV-001",
        "device_name": "遥测设备",
        "device_type": "car",
    })
    token = login_res.json()["data"]["access_token"]

    event_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    res = await async_client.post(
        "/v1/api/car/telemetry/events:batch",
        json={
            "events": [
                {
                    "event_id": event_id,
                    "event_type": "learning.session.start",
                    "module": "math",
                    "timestamp": now,
                    "payload": {"session_id": "sess-001"},
                }
            ]
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["accepted"] == 1
    assert body["data"]["duplicates"] == 0


@pytest.mark.asyncio
async def test_batch_events_idempotent(async_client: AsyncClient, telemetry_setup):
    """Repeating the same event_id returns accepted=0, duplicates=1."""
    login_res = await async_client.post("/v1/api/car/auth/login", json={
        "phone": telemetry_setup["phone"],
        "device_id": "TELEM-DEV-002",
        "device_name": "幂等设备",
        "device_type": "car",
    })
    token = login_res.json()["data"]["access_token"]

    event_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    event_payload = {
        "events": [
            {
                "event_id": event_id,
                "event_type": "learning.session.start",
                "module": "math",
                "timestamp": now,
                "payload": {},
            }
        ]
    }
    headers = {"Authorization": f"Bearer {token}"}

    # First request
    res1 = await async_client.post("/v1/api/car/telemetry/events:batch", json=event_payload, headers=headers)
    assert res1.json()["data"]["accepted"] == 1

    # Second request — same event_id
    res2 = await async_client.post("/v1/api/car/telemetry/events:batch", json=event_payload, headers=headers)
    assert res2.status_code == 200
    assert res2.json()["data"]["accepted"] == 0
    assert res2.json()["data"]["duplicates"] == 1


@pytest.mark.asyncio
async def test_batch_events_unauthorized(async_client: AsyncClient):
    """POST without auth token returns 401."""
    res = await async_client.post("/v1/api/car/telemetry/events:batch", json={
        "events": [{"event_id": str(uuid.uuid4()), "event_type": "test", "timestamp": "2026-07-26T10:00:00+08:00"}]
    })
    assert res.status_code == 401
```

- [ ] **Step 4: Run all tests**

```powershell
cd d:/danke_robot/cloud/backend
$env:PYTHONPATH="."
pytest tests/ -v
```

Expected: All tests pass (16 existing + new API tests).

Wait — the conftest.py `async_client` fixture needs to work with the existing `tables` fixture. Let me make the conftest addition cleaner. The `async_client` uses the real DB engine from `settings.database_url`, and the `tables` fixture creates tables on that same engine. The test app connects to the same DB. This should work as long as the `async_client` fixture also depends on `tables`.

Actually there's a subtlety: the `async_client` fixture creates a fresh FastAPI app with `create_app()`, which uses `app.db.async_engine` (the production engine). But the tests use a different engine (from the `engine` fixture with NullPool). We need to override the app's engine.

Let me revise the conftest addition to properly handle this:

```python
@pytest.fixture
async def async_client(engine, tables):
    """Create an httpx AsyncClient backed by a test FastAPI app."""
    import app.db as db_module
    from app.main import create_app
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    test_app = create_app()

    # Override the session factory to use test engine
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
```

This is cleaner — it overrides the `get_db` dependency directly on the test app instance.

- [ ] **Step 5: Commit**

```bash
git add cloud/backend/tests/
git commit -m "test: add integration tests for car auth and telemetry APIs"
```

---

### Task 21: Final verification — full test suite

**Files:**
- (none — verification only)

- [ ] **Step 1: Rebuild test DB and run full test suite**

```powershell
cd d:/danke_robot/cloud/backend

# Rebuild DB
$env:PGPASSWORD="parent"
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U parent -h localhost -c "DROP DATABASE IF EXISTS parent_db;"
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U parent -h localhost -c "CREATE DATABASE parent_db;"
alembic upgrade head

# Run all tests
pytest tests/ -v
```

Expected: All tests pass (16 existing + 5 new API tests = 21+ tests).

- [ ] **Step 2: Run ruff lint check**

```powershell
cd d:/danke_robot/cloud/backend
ruff check .
```

Expected: No lint errors.

- [ ] **Step 3: Verify health endpoint one more time**

```powershell
cd d:/danke_robot/cloud/backend
Start-Process -NoNewWindow python -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8000"
Start-Sleep -Seconds 3
$r = Invoke-RestMethod -Uri "http://localhost:8000/health"
Write-Host $r
# Cleanup
Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq "" } | Stop-Process
```

- [ ] **Step 4: Final commit (if any changes from lint fixes)**

```bash
git status
# If any changes from lint fixes:
git add -A
git commit -m "chore: final lint fixes and cleanup"
```

---

### Task 22: Wrap-up — verify git log and branch status

- [ ] **Step 1: Check git log**

```bash
git log --oneline origin/main..HEAD
```

Expected: 20+ commits covering all tasks from branch creation to integration tests.

- [ ] **Step 2: Push branch (DO NOT merge to main)**

```bash
git push -u origin feature/cloud-backend-skeleton
```

Note: Only push. Do NOT merge to main until user explicitly approves after review.
