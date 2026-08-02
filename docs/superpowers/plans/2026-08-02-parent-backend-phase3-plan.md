# Parent Backend Phase 3 — Full Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement 7 missing parent API modules (behavior, usage, online, messages, navigation, notifications, files), fix 9 known issues, write seed data scripts, and create deployment documentation.

**Architecture:** Each new module follows the established pattern: `app/parent/<module>/{router,service,schemas,__init__}.py` with FastAPI router → service → SQLAlchemy async queries. New models go in `app/models/` with corresponding alembic migrations. All endpoints require parent JWT auth via `get_current_parent` dependency and `verify_parent_access()` for child-scoped access.

**Tech Stack:** FastAPI + SQLAlchemy async + asyncpg + Pydantic v2 + Alembic (existing stack, no new dependencies)

## Global Constraints

- All endpoints return `{code: int, msg: str, data: object|null}` via `ok()` / `error()` helpers
- All child-scoped endpoints MUST call `verify_parent_access(db, parent_id, child_id)` first
- All POST/PUT/DELETE endpoints MUST try/except ValueError → rollback + 400, except Exception → rollback + 500
- All GET endpoints MUST try/except Exception → 500
- Router prefix: `prefix="/children"` for child-scoped, `prefix=""` for parent-scoped (notifications only)
- Test pattern: httpx AsyncClient + ASGITransport, real test DB with NullPool, create_all/drop_all per test
- Each module needs 3+ integration tests covering: happy path, empty state, auth required
- Alembic migrations: name format `YYYYMMDD_<hex>_<description>.py`, auto-generate then review
- Seed scripts: idempotent (check existence before insert), use existing async engine from `app.db`

---

## Phase 0: Quick Fixes (Tasks 1-9)

### Task 1: Fix F1 — goal module sum validation + F2 — separate input schema

**Files:**
- Modify: `cloud/backend/app/parent/goal/schemas.py`
- Modify: `cloud/backend/app/parent/goal/service.py`

**Interfaces:**
- Produces: `GoalModuleIn(model, goal_minutes)` — input-only schema
- Produces: `LearningGoalModule(module, module_label, goal_minutes)` — output schema (unchanged)
- Consumes: `MODULE_LABELS, VALID_MODULES` from existing schemas.py

- [ ] **Step 1: Add GoalModuleIn to schemas.py**

In `cloud/backend/app/parent/goal/schemas.py`, add after the `LearningGoalModule` class:

```python
class GoalModuleIn(BaseModel):
    """Per-module goal input (no label)."""
    module: str
    goal_minutes: int = Field(default=0, ge=0)
```

- [ ] **Step 2: Update UpdateLearningGoalRequest to use GoalModuleIn**

Replace `modules: list[LearningGoalModule]` with:

```python
class UpdateLearningGoalRequest(BaseModel):
    """PUT request body for updating learning goal."""
    daily_goal_minutes: int = Field(..., ge=0)
    modules: list[GoalModuleIn] = Field(default_factory=list)
```

- [ ] **Step 3: Add sum validation in service.py**

In `upsert_learning_goal()` in `cloud/backend/app/parent/goal/service.py`, add after the `# Validate modules` block (line 49):

```python
    # Validate per-module sum ≤ daily total
    module_sum = sum(m.get("goal_minutes", 0) for m in modules)
    if module_sum > daily_goal_minutes:
        raise ValueError(
            f"goal_module_sum_exceeds_total: {module_sum} > {daily_goal_minutes}"
        )
```

- [ ] **Step 4: Run existing goal tests**

```bash
cd cloud/backend && python -m pytest tests/test_parent_goal.py -v
```

- [ ] **Step 5: Commit**

```bash
git add app/parent/goal/schemas.py app/parent/goal/service.py
git commit -m "fix: validate goal module sum <= daily total, separate input schema
- Add GoalModuleIn (module + goal_minutes only) for PUT requests
- UpdateLearningGoalRequest.modules now uses GoalModuleIn
- upsert_learning_goal raises ValueError when module_sum > daily_goal_minutes"
```

---

### Task 2: Fix F3 — dispatch: block learning category in POST

**Files:**
- Modify: `cloud/backend/app/parent/dispatch/router.py:96-99`

- [ ] **Step 1: Add validation in create_dispatched_tasks_endpoint**

In `cloud/backend/app/parent/dispatch/router.py`, add after line 96 (`tasks_data = [...]`):

```python
    # Dispatched tasks are non-learning only; learning tasks go through today-tasks
    for t in body.tasks:
        if t.task_category == "learning":
            return JSONResponse(
                status_code=400,
                content=error(400, "learning_tasks_not_allowed_here"),
            )
```

- [ ] **Step 2: Remove dead code in service.py**

In `cloud/backend/app/parent/dispatch/service.py`, line 118, replace:
```python
module = t.get("module") if t.get("task_category") == "learning" else None
```
with:
```python
module = None  # only non-learning tasks here; learning handled by today-tasks
```

- [ ] **Step 3: Run existing dispatch tests**

```bash
cd cloud/backend && python -m pytest tests/test_parent_dispatch.py -v
```

- [ ] **Step 4: Commit**

```bash
git add app/parent/dispatch/router.py app/parent/dispatch/service.py
git commit -m "fix: block learning category in dispatched-tasks POST, remove dead code"
```

---

### Task 3: Fix F4 — reports: add TODO comments for hardcoded behavior data

**Files:**
- Modify: `cloud/backend/app/parent/reports/service.py`

- [ ] **Step 1: Add TODO comments at hardcoded behavior fields**

In `_get_session_summary()` at line 250, replace:
```python
"total_active_duration_ms": 0,
```
with:
```python
"total_active_duration_ms": 0,  # TODO Phase 3: compute from behavior_event duration data
```

In `_build_weekly_report()` at lines 432-442, replace the behavior_summary and related fields with commented versions:

```python
        # TODO Phase 3: populate from behavior_event table (focus_score, posture_score, etc.)
        "behavior_summary": {
            "focus_score": 0, "focus_change_percent": 0,
            "posture_score": 0, "posture_change_percent": 0,
            "anomaly_count": 0, "discovery_count": 0,
        },
        # TODO Phase 3: populate from behavior_event daily aggregation
        "focus_daily_series": [],
        "posture_weekly_series": [],
        "anomalies": [],
        "discoveries": [],
        # TODO Phase 3: generate via AI/LLM summary of week's behavior
        "ai_summary": "",
```

- [ ] **Step 2: Commit**

```bash
git add app/parent/reports/service.py
git commit -m "docs: add TODO comments for behavior data integration in reports"
```

---

### Task 4: Fix F5 — reports: comment on time field discrepancy

**Files:**
- Modify: `cloud/backend/app/parent/reports/service.py`

- [ ] **Step 1: Add comment in get_learning_progress**

In `get_learning_progress()`, after the `task_result` query block (around line 54), add a comment:

```python
    # NOTE: tasks are filtered by business_date (the date the task is assigned to),
    # while answers are filtered by answered_at (the actual wall-clock time).
    # These two time axes can differ when a child works past midnight
    # or when tasks span multiple days. This is intentional for Phase 1-2;
    # Phase 3 may unify on business_date for both.
```

- [ ] **Step 2: Commit**

```bash
git add app/parent/reports/service.py
git commit -m "docs: explain task/answer time field discrepancy in progress aggregation"
```

---

### Task 5: Fix F6 — CORS: add production warning comment

**Files:**
- Modify: `cloud/backend/app/middleware/cors.py`

- [ ] **Step 1: Strengthen the existing comment**

Replace the comment in `add_cors()`:

```python
def add_cors(app: FastAPI) -> None:
    """Add CORS middleware allowing all origins in dev.

    WARNING: Production MUST restrict origins to the actual mini-program domain
    and car device origins. Example for production:
        allow_origins=["https://your-domain.com", "https://api.weixin.qq.com"]
    """
```

- [ ] **Step 2: Commit**

```bash
git add app/middleware/cors.py
git commit -m "docs: strengthen CORS production warning comment"
```

---

### Task 6: Fix F7 — move pepper constants to config

**Files:**
- Modify: `cloud/backend/app/config.py`
- Modify: `cloud/backend/app/auth/security.py`

- [ ] **Step 1: Add pepper fields to Settings in config.py**

Add after the `business_timezone` field in `Settings`:

```python
    # Security — pepper values for hashing
    phone_pepper: str = "danke-phone-pepper-v1"
    token_pepper: str = "danke-token-pepper-v1"
```

- [ ] **Step 2: Update security.py to use settings**

Replace lines 19-20:
```python
_PHONE_PEPPER = "danke-phone-pepper-v1"  # TODO: move to config
_TOKEN_PEPPER = "danke-token-pepper-v1"  # TODO: move to config
```
with:
```python
# Pepper values are loaded from config; defaults are for dev only.
# Set PHONE_PEPPER / TOKEN_PEPPER in .env for production.
```

Then update `hash_token()`:
```python
def hash_token(token: str) -> str:
    """HMAC-SHA256 hash of a token string with server-side pepper."""
    return hmac.new(
        settings.token_pepper.encode(),
        token.encode(),
        hashlib.sha256,
    ).hexdigest()
```

And `hash_phone()`:
```python
def hash_phone(phone: str) -> str:
    """HMAC-SHA256 hash of phone number with server-side pepper."""
    return hmac.new(
        settings.phone_pepper.encode(),
        phone.encode(),
        hashlib.sha256,
    ).hexdigest()
```

- [ ] **Step 3: Run existing auth tests**

```bash
cd cloud/backend && python -m pytest tests/test_parent_account.py -v
```

- [ ] **Step 4: Commit**

```bash
git add app/config.py app/auth/security.py
git commit -m "refactor: move pepper constants from security.py to config Settings"
```

---

### Task 7: Fix F8 — delete empty seed_fake_data.py

**Files:**
- Delete: `cloud/backend/scripts/seed_fake_data.py`

- [ ] **Step 1: Delete the file**

```bash
rm cloud/backend/scripts/seed_fake_data.py
```

- [ ] **Step 2: Commit**

```bash
git rm scripts/seed_fake_data.py
git commit -m "chore: remove empty seed_fake_data.py placeholder"
```

---

### Task 8: Fix F9 — add docstrings to empty __init__.py files

**Files:**
- Modify: `cloud/backend/app/models/__init__.py`
- Modify: `cloud/backend/app/parent/__init__.py`
- Modify: `cloud/backend/app/parent/reports/__init__.py`

- [ ] **Step 1: Add docstrings**

`app/models/__init__.py`:
```python
"""SQLAlchemy ORM models — all models must be imported here for Base.metadata registration."""
```

`app/parent/__init__.py`:
```python
"""Parent mini-program API — children, device, config, dashboard, reports, and more."""
```

`app/parent/reports/__init__.py`:
```python
"""Parent reports — learning progress, sessions, wrong answers, weekly reports."""
```

- [ ] **Step 2: Do the same for all other empty __init__.py in app/parent/**

Check and add docstrings to: `dispatch/__init__.py`, `goal/__init__.py`, `children/__init__.py`, `config/__init__.py`, `dashboard/__init__.py`, `device/__init__.py`

- [ ] **Step 3: Commit**

```bash
git add app/models/__init__.py app/parent/__init__.py app/parent/*/__init__.py
git commit -m "docs: add module docstrings to all empty __init__.py files"
```

---

## Phase 1: New Models & Migrations (Tasks 9-14)

### Task 9: Create BehaviorEvent model

**Files:**
- Create: `cloud/backend/app/models/behavior.py`

**Interfaces:**
- Produces: `BehaviorEvent` ORM class with `__tablename__ = "behavior_event"`

- [ ] **Step 1: Write the model**

```python
"""Behavior event model — focus, posture, location, zone events from car device."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class BehaviorEvent(Base):
    """A behavior observation event from the car device.

    Events are produced by the behavioral module on SC171 (MediaPipe + YOLOv8)
    and ingested via telemetry batch endpoint. Each event records a score
    (0-100) and optional payload with detailed metrics.

    event_type determines which analysis page consumes it:
      - focus: attention/focus score
      - posture: sitting posture score
      - location: child's location in room
      - zone: room zone change
    """

    __tablename__ = "behavior_event"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "event_type IN ('focus','posture','location','zone')",
            name="ck_behavior_event_type",
        ),
        nullable=False,
    )
    score: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Score 0-100, higher is better for focus/posture"
    )
    payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict,
        comment="Detailed metrics: {duration_seconds, zone_name, ...}"
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="When the behavior was observed (device time)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_behavior_child", "child_id"),
        Index("idx_behavior_child_type_time", "child_id", "event_type", "recorded_at"),
    )
```

- [ ] **Step 2: Commit**

```bash
git add app/models/behavior.py
git commit -m "feat: add BehaviorEvent model for focus/posture/location/zone events"
```

---

### Task 10: Create ParentMessage model

**Files:**
- Create: `cloud/backend/app/models/message.py`

- [ ] **Step 1: Write the model**

```python
"""Parent-child message model."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ParentMessage(Base):
    """A message between parent and child.

    direction: parent_to_child | child_to_parent
    msg_type: text | image | audio | task_card
    content is a JSONB blob whose schema depends on msg_type.
    """

    __tablename__ = "parent_message"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child.id"), nullable=False
    )
    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("parent_account.id"), nullable=False
    )
    direction: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "direction IN ('parent_to_child','child_to_parent')",
            name="ck_msg_direction",
        ),
        nullable=False,
    )
    msg_type: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "msg_type IN ('text','image','audio','task_card')",
            name="ck_msg_type",
        ),
        nullable=False,
    )
    content: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict,
        comment="Schema varies by msg_type: {text}, {file_id, playback_url}, {task_id, ...}"
    )
    replied_to_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("parent_message.id"), nullable=True
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_msg_child", "child_id"),
        Index("idx_msg_child_parent", "child_id", "parent_id"),
        Index("idx_msg_created", "created_at"),
    )
```

- [ ] **Step 2: Commit**

```bash
git add app/models/message.py
git commit -m "feat: add ParentMessage model for parent-child messaging"
```

---

### Task 11: Create NavigationInstruction model

**Files:**
- Create: `cloud/backend/app/models/navigation.py`

- [ ] **Step 1: Write the model**

```python
"""Navigation instruction model — parent remote control."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class NavigationInstruction(Base):
    """A remote navigation instruction from parent to child's car device.

    destination: learning | chat | parent_messages
    status: pending (not yet delivered) | delivered (car acked) | expired (ttl exceeded)
    """

    __tablename__ = "navigation_instruction"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child.id"), nullable=False
    )
    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("parent_account.id"), nullable=False
    )
    destination: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "destination IN ('learning','chat','parent_messages')",
            name="ck_nav_destination",
        ),
        nullable=False,
    )
    route_key: Mapped[str] = mapped_column(Text, nullable=False)
    module: Mapped[str | None] = mapped_column(Text, nullable=True)
    custom_batch_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "status IN ('pending','delivered','expired')",
            name="ck_nav_status",
        ),
        nullable=False,
        default="pending",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_nav_child", "child_id"),
        Index("idx_nav_child_status", "child_id", "status"),
    )
```

- [ ] **Step 2: Commit**

```bash
git add app/models/navigation.py
git commit -m "feat: add NavigationInstruction model for parent remote control"
```

---

### Task 12: Create NotificationSettings and Notification models

**Files:**
- Create: `cloud/backend/app/models/notification.py`

- [ ] **Step 1: Write both models**

```python
"""Notification settings and notification models."""

import uuid
from datetime import datetime, time

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class NotificationSettings(Base):
    """Per-child notification preferences set by parent.

    One row per child. settings is a JSONB dict of boolean toggles.
    dnd (do-not-disturb) silences all notifications during the window.
    """

    __tablename__ = "notification_settings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child.id"), nullable=False
    )
    settings: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict,
        comment="e.g. {task_completed: true, behavior_alert: true, ...}"
    )
    dnd_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    dnd_start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    dnd_end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("child_id", name="uq_notif_settings_child"),
        Index("idx_notif_settings_child", "child_id"),
    )


class Notification(Base):
    """A single notification delivered to a parent.

    Notifications are generated by the backend in response to car events
    (task completed, behavior alert, device offline, etc.).
    """

    __tablename__ = "notification"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("parent_account.id"), nullable=False
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child.id"), nullable=False
    )
    notif_type: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="task_completed|behavior_alert|device_offline|daily_summary|weekly_report|..."
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_notif_parent", "parent_id"),
        Index("idx_notif_parent_read", "parent_id", "is_read"),
        Index("idx_notif_created", "created_at"),
    )
```

- [ ] **Step 2: Commit**

```bash
git add app/models/notification.py
git commit -m "feat: add NotificationSettings and Notification models"
```

---

### Task 13: Create FileUpload model

**Files:**
- Create: `cloud/backend/app/models/file_upload.py`

- [ ] **Step 1: Write the model**

```python
"""File upload model — metadata for parent-uploaded files (messages, avatars)."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class FileUpload(Base):
    """Metadata for a file uploaded by a parent.

    Actual file content is stored on local disk (production: OSS/S3).
    status: pending (upload initiated) | available (upload confirmed) | expired (TTL exceeded)
    """

    __tablename__ = "file_upload"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("parent_account.id"), nullable=False
    )
    purpose: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "purpose IN ('parent_message_image','parent_message_audio','parent_avatar','child_avatar')",
            name="ck_file_purpose",
        ),
        nullable=False,
    )
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(Text, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "status IN ('pending','available','expired')",
            name="ck_file_status",
        ),
        nullable=False,
        default="pending",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("idx_file_parent", "parent_id"),
        Index("idx_file_status", "status"),
    )
```

- [ ] **Step 2: Commit**

```bash
git add app/models/file_upload.py
git commit -m "feat: add FileUpload model for parent file uploads"
```

---

### Task 14: Generate alembic migration for all new models

**Files:**
- Create: `cloud/backend/alembic/versions/20260802_a1b2c3_phase3_new_tables.py`
- Modify: `cloud/backend/alembic/env.py` (import new models)
- Modify: `cloud/backend/tests/conftest.py` (import new models)

- [ ] **Step 1: Update alembic/env.py model imports**

Add after the existing model imports (around line 25):

```python
from app.models.behavior import BehaviorEvent  # noqa: F401
from app.models.message import ParentMessage  # noqa: F401
from app.models.navigation import NavigationInstruction  # noqa: F401
from app.models.notification import Notification, NotificationSettings  # noqa: F401
from app.models.file_upload import FileUpload  # noqa: F401
```

- [ ] **Step 2: Update tests/conftest.py model imports**

Add in the same import block:

```python
from app.models.behavior import BehaviorEvent  # noqa: F401
from app.models.message import ParentMessage  # noqa: F401
from app.models.navigation import NavigationInstruction  # noqa: F401
from app.models.notification import Notification, NotificationSettings  # noqa: F401
from app.models.file_upload import FileUpload  # noqa: F401
```

- [ ] **Step 3: Generate migration**

```bash
cd cloud/backend
alembic revision --autogenerate -m "phase3_new_tables"
```

Rename the generated file to `20260802_a1b2c3_phase3_new_tables.py` if needed.

- [ ] **Step 4: Verify migration is valid**

```bash
cd cloud/backend && python -m pytest tests/test_parent_goal.py::test_get_goal_empty -v
```

This test creates/drops all tables via conftest. If it passes, the new models are correctly registered with Base.metadata.

- [ ] **Step 5: Commit**

```bash
git add alembic/versions/20260802_a1b2c3_phase3_new_tables.py alembic/env.py tests/conftest.py
git commit -m "feat: add alembic migration for Phase 3 models (6 new tables)"
```

---

## Phase 2: New API Modules (Tasks 15-22)

### Task 15: Behavior analysis module (4 GET endpoints)

**Files:**
- Create: `cloud/backend/app/parent/behavior/__init__.py`
- Create: `cloud/backend/app/parent/behavior/router.py`
- Create: `cloud/backend/app/parent/behavior/service.py`
- Create: `cloud/backend/app/parent/behavior/schemas.py`
- Create: `cloud/backend/tests/test_parent_behavior.py`
- Modify: `cloud/backend/app/router.py` (register behavior_router)

**Interfaces:**
- Produces: `behavior_router` with prefix="/children"
- Consumes: `verify_parent_access` from `app.parent.service`
- Consumes: `get_current_parent` from `app.auth.dependencies`
- Consumes: `get_db` from `app.db`

- [ ] **Step 1: Write schemas.py**

```python
"""Parent behavior schemas — focus, posture, location, insights."""

from datetime import date, datetime

from pydantic import BaseModel


class BehaviorScorePoint(BaseModel):
    date: date
    score: int


class BehaviorStat(BaseModel):
    label: str
    value: float
    unit: str


class FocusOut(BaseModel):
    period: str
    score: int = 0
    change_percent: int = 0
    stats: list[BehaviorStat] = []
    daily_series: list[BehaviorScorePoint] = []


class PostureDistribution(BaseModel):
    label: str
    percent: int


class PostureOut(BaseModel):
    period: str
    score: int = 0
    change_percent: int = 0
    reminder_count: int = 0
    distribution: list[PostureDistribution] = []
    weekly_series: list[BehaviorScorePoint] = []


class ZoneDistribution(BaseModel):
    zone: str
    percent: int


class LocationOut(BaseModel):
    period: str
    active_zones_count: int = 0
    distribution: list[ZoneDistribution] = []
    anomaly_detected: bool = False


class InsightTag(BaseModel):
    text: str
    cls: str


class InsightItem(BaseModel):
    insight_id: str
    type: str
    title: str
    description: str
    tags: list[InsightTag] = []
    occurred_at: datetime | None = None


class InsightsOut(BaseModel):
    items: list[InsightItem] = []
```

- [ ] **Step 2: Write service.py**

```python
"""Parent behavior business logic — focus, posture, location, insights."""

from datetime import date, timedelta
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.behavior import BehaviorEvent
from app.parent.service import verify_parent_access

Period = Literal["day", "week", "month"]


def _period_days(period: Period) -> int:
    return {"day": 1, "week": 7, "month": 30}[period]


async def _compute_score(
    db: AsyncSession, child_id: str, event_type: str, days: int,
) -> tuple[int, list[dict]]:
    """Return average score and daily series for an event type over N days."""
    cutoff = date.today() - timedelta(days=days - 1)
    today = date.today()

    result = await db.execute(
        select(
            func.date(BehaviorEvent.recorded_at).label("d"),
            func.avg(BehaviorEvent.score).label("avg_score"),
        )
        .where(
            BehaviorEvent.child_id == child_id,
            BehaviorEvent.event_type == event_type,
            func.date(BehaviorEvent.recorded_at) >= cutoff,
        )
        .group_by(func.date(BehaviorEvent.recorded_at))
        .order_by(func.date(BehaviorEvent.recorded_at))
    )
    rows = result.all()

    # Build a map date->score, fill missing dates with 0
    score_map = {}
    total = 0
    count = 0
    for d, avg in rows:
        d_str = d.isoformat() if isinstance(d, date) else str(d)
        score_map[d_str] = int(avg)
        total += avg
        count += 1

    overall = int(total / count) if count > 0 else 0

    # Fill all dates in range
    series = []
    for i in range(days):
        d = today - timedelta(days=days - 1 - i)
        d_str = d.isoformat()
        series.append({"date": d, "score": score_map.get(d_str, 0)})

    return overall, series


async def get_focus(
    db: AsyncSession, parent_id: str, child_id: str, period: Period = "week",
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None
    days = _period_days(period)
    score, series = await _compute_score(db, child_id, "focus", days)
    # Compute stats from raw events
    cutoff = date.today() - timedelta(days=days - 1)
    raw = await db.execute(
        select(BehaviorEvent.payload)
        .where(
            BehaviorEvent.child_id == child_id,
            BehaviorEvent.event_type == "focus",
            func.date(BehaviorEvent.recorded_at) >= cutoff,
        )
    )
    payloads = [r[0] for r in raw.all() if r[0]]
    distract_count = sum(1 for p in payloads if p.get("is_distracted"))
    max_focus = max((p.get("focus_duration_seconds", 0) for p in payloads), default=0)
    focus_pct = int(sum(1 for p in payloads if not p.get("is_distracted")) / max(len(payloads), 1) * 100)
    interrupt_count = sum(1 for p in payloads if p.get("interrupted"))
    return {
        "period": period, "score": score, "change_percent": 0,
        "stats": [
            {"label": "分散次数", "value": distract_count, "unit": "次"},
            {"label": "最长专注", "value": round(max_focus / 60, 1), "unit": "min"},
            {"label": "专注占比", "value": focus_pct, "unit": "%"},
            {"label": "打断次数", "value": interrupt_count, "unit": "次"},
        ],
        "daily_series": series,
    }


async def get_posture(
    db: AsyncSession, parent_id: str, child_id: str, period: Period = "week",
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None
    days = _period_days(period)
    score, series = await _compute_score(db, child_id, "posture", days)
    cutoff = date.today() - timedelta(days=days - 1)
    raw = await db.execute(
        select(BehaviorEvent.payload)
        .where(
            BehaviorEvent.child_id == child_id,
            BehaviorEvent.event_type == "posture",
            func.date(BehaviorEvent.recorded_at) >= cutoff,
        )
    )
    payloads = [r[0] for r in raw.all() if r[0]]
    reminder = sum(1 for p in payloads if p.get("reminder_sent"))
    good = sum(1 for p in payloads if p.get("posture_label") == "good")
    slight = sum(1 for p in payloads if p.get("posture_label") == "slight_tilt")
    bad = sum(1 for p in payloads if p.get("posture_label") == "obvious_slant")
    total = max(len(payloads), 1)
    return {
        "period": period, "score": score, "change_percent": 0,
        "reminder_count": reminder,
        "distribution": [
            {"label": "标准坐姿", "percent": round(good / total * 100)},
            {"label": "轻微倾斜", "percent": round(slight / total * 100)},
            {"label": "明显歪斜", "percent": round(bad / total * 100)},
        ],
        "weekly_series": series,
    }


async def get_location(
    db: AsyncSession, parent_id: str, child_id: str, period: Period = "week",
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None
    days = _period_days(period)
    cutoff = date.today() - timedelta(days=days - 1)
    raw = await db.execute(
        select(BehaviorEvent.payload)
        .where(
            BehaviorEvent.child_id == child_id,
            BehaviorEvent.event_type.in_(["location", "zone"]),
            func.date(BehaviorEvent.recorded_at) >= cutoff,
        )
    )
    payloads = [r[0] for r in raw.all() if r[0]]
    zone_counts: dict[str, int] = {}
    for p in payloads:
        zone = p.get("zone_name", "未知")
        zone_counts[zone] = zone_counts.get(zone, 0) + 1
    total = max(len(payloads), 1)
    distribution = [
        {"zone": z, "percent": round(c / total * 100)}
        for z, c in sorted(zone_counts.items(), key=lambda x: -x[1])
    ]
    return {
        "period": period,
        "active_zones_count": len(zone_counts),
        "distribution": distribution,
        "anomaly_detected": False,
    }


async def get_insights(
    db: AsyncSession, parent_id: str, child_id: str, period: Period = "week",
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None
    days = _period_days(period)
    cutoff = date.today() - timedelta(days=days - 1)
    # Insights are stored as behavior_event with event_type='focus'/'posture'
    # and payload.insight populated.
    raw = await db.execute(
        select(BehaviorEvent)
        .where(
            BehaviorEvent.child_id == child_id,
            BehaviorEvent.event_type.in_(["focus", "posture"]),
            func.date(BehaviorEvent.recorded_at) >= cutoff,
        )
        .order_by(BehaviorEvent.recorded_at.desc())
        .limit(10)
    )
    events = raw.scalars().all()
    items = []
    for e in events:
        p = e.payload if isinstance(e.payload, dict) else {}
        insight = p.get("insight")
        if insight:
            items.append({
                "insight_id": str(e.id),
                "type": e.event_type,
                "title": insight.get("title", ""),
                "description": insight.get("description", ""),
                "tags": [
                    {"text": t.get("text", ""), "cls": t.get("cls", "")}
                    for t in insight.get("tags", [])
                ],
                "occurred_at": e.recorded_at,
            })
    return {"items": items}
```

- [ ] **Step 3: Write router.py**

```python
"""Parent behavior routes — focus, posture, location, insights."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.db import get_db
from app.parent.behavior.schemas import FocusOut, InsightsOut, LocationOut, PostureOut
from app.parent.behavior.service import get_focus, get_insights, get_location, get_posture
from app.schemas.common import error, ok

behavior_router = APIRouter(prefix="/children", tags=["parent-behavior"])


@behavior_router.get("/{child_id}/behavior/focus")
async def focus(
    child_id: str,
    period: str = Query(default="week", pattern=r"^(day|week|month)$"),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await get_focus(db, parent_id, child_id, period)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))
    return ok(FocusOut(**data).model_dump())


@behavior_router.get("/{child_id}/behavior/posture")
async def posture(
    child_id: str,
    period: str = Query(default="week", pattern=r"^(day|week|month)$"),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await get_posture(db, parent_id, child_id, period)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))
    return ok(PostureOut(**data).model_dump())


@behavior_router.get("/{child_id}/behavior/location")
async def location(
    child_id: str,
    period: str = Query(default="week", pattern=r"^(day|week|month)$"),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await get_location(db, parent_id, child_id, period)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))
    return ok(LocationOut(**data).model_dump())


@behavior_router.get("/{child_id}/behavior/insights")
async def insights(
    child_id: str,
    period: str = Query(default="week", pattern=r"^(day|week|month)$"),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await get_insights(db, parent_id, child_id, period)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))
    return ok(InsightsOut(**data).model_dump())
```

- [ ] **Step 4: Write __init__.py**

```python
"""Parent behavior analysis — focus, posture, location, AI insights."""
```

- [ ] **Step 5: Write tests**

```python
"""Integration tests for parent behavior API."""

import pytest
from httpx import AsyncClient

from app.auth.security import create_parent_access_token
from app.models.child import Child
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild


@pytest.fixture
async def _behavior_setup(db_session):
    parent = ParentAccount(wx_openid="test_behavior", status="active")
    db_session.add(parent)
    await db_session.flush()
    family = Family(name="行为测试家庭")
    db_session.add(family)
    await db_session.flush()
    child = Child(family_id=family.id, nickname="行为孩子")
    db_session.add(child)
    await db_session.flush()
    pc = ParentChild(parent_id=parent.id, child_id=child.id, family_id=family.id, status="active", is_default=True)
    db_session.add(pc)
    await db_session.commit()
    token = create_parent_access_token(parent_id=str(parent.id))
    return token, str(child.id)


@pytest.mark.asyncio
async def test_focus_empty(async_client: AsyncClient, _behavior_setup):
    token, child_id = _behavior_setup
    res = await async_client.get(
        f"/v1/api/parent/children/{child_id}/behavior/focus",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["score"] == 0
    assert body["data"]["daily_series"] != []


@pytest.mark.asyncio
async def test_posture_empty(async_client: AsyncClient, _behavior_setup):
    token, child_id = _behavior_setup
    res = await async_client.get(
        f"/v1/api/parent/children/{child_id}/behavior/posture",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert body["data"]["score"] == 0


@pytest.mark.asyncio
async def test_location_empty(async_client: AsyncClient, _behavior_setup):
    token, child_id = _behavior_setup
    res = await async_client.get(
        f"/v1/api/parent/children/{child_id}/behavior/location",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_behavior_require_auth(async_client: AsyncClient):
    res = await async_client.get("/v1/api/parent/children/any-id/behavior/focus")
    assert res.status_code == 401
```

- [ ] **Step 6: Register behavior_router in app/router.py**

Add import:
```python
from app.parent.behavior.router import behavior_router
```

Add after the reports_router line:
```python
parent_router.include_router(behavior_router)
```

- [ ] **Step 7: Run tests**

```bash
cd cloud/backend && python -m pytest tests/test_parent_behavior.py -v
```

- [ ] **Step 8: Commit**

```bash
git add app/parent/behavior/ tests/test_parent_behavior.py app/router.py
git commit -m "feat: add parent behavior analysis module (focus/posture/location/insights)"
```

---

### Task 16: Usage module (2 GET endpoints)

**Files:**
- Create: `cloud/backend/app/parent/usage/__init__.py`
- Create: `cloud/backend/app/parent/usage/router.py`
- Create: `cloud/backend/app/parent/usage/service.py`
- Create: `cloud/backend/app/parent/usage/schemas.py`
- Create: `cloud/backend/tests/test_parent_usage.py`
- Modify: `cloud/backend/app/router.py` (register usage_router)

- [ ] **Step 1: Write schemas.py**

```python
"""Parent usage schemas — daily/weekly/monthly usage and module breakdown."""

from datetime import date

from pydantic import BaseModel


class UsagePoint(BaseModel):
    date: date
    total_minutes: int


class UsageSeriesOut(BaseModel):
    granularity: str
    daily_goal_minutes: int = 30
    series: list[UsagePoint] = []


class ModuleUsage(BaseModel):
    module: str
    module_label: str
    minutes: int = 0
    percent: int = 0


class ModuleBreakdownOut(BaseModel):
    date: date
    total_minutes: int = 0
    modules: list[ModuleUsage] = []
```

- [ ] **Step 2: Write service.py**

```python
"""Parent usage business logic — daily/weekly/monthly series, module breakdown."""

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.answer import AnswerRecord
from app.models.learning import LearningSession
from app.models.task import DailyTask
from app.parent.service import verify_parent_access

MODULE_LABELS = {
    "science": "科学探秘", "math": "数学思维",
    "english": "英语角", "poems": "诗词歌赋",
    "music": "音乐乐园", "quiz": "趣味问答",
}


async def get_usage_series(
    db: AsyncSession, parent_id: str, child_id: str,
    granularity: str = "day",
) -> dict | None:
    """Return daily/weekly/monthly usage minutes series.
    
    Computed from completed tasks count and session durations.
    Phase 3 approximation: 5 min per completed task + session count * 5 min.
    Phase 4: use actual behavior_event duration data.
    """
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    days = {"day": 7, "week": 28, "month": 90}.get(granularity, 7)
    cutoff = date.today() - timedelta(days=days - 1)
    today = date.today()

    # Completed tasks per day
    task_result = await db.execute(
        select(
            DailyTask.business_date,
            func.count().label("cnt"),
        )
        .where(
            DailyTask.child_id == child_id,
            DailyTask.business_date >= cutoff,
            DailyTask.status == "completed",
        )
        .group_by(DailyTask.business_date)
    )
    task_map = {str(r.business_date): r.cnt for r in task_result.all()}

    # Sessions per day
    sess_result = await db.execute(
        select(
            func.date(LearningSession.created_at).label("d"),
            func.count().label("cnt"),
        )
        .where(
            LearningSession.child_id == child_id,
            func.date(LearningSession.created_at) >= cutoff,
        )
        .group_by(func.date(LearningSession.created_at))
    )
    sess_map = {str(r.d): r.cnt for r in sess_result.all()}

    series = []
    for i in range(days):
        d = today - timedelta(days=days - 1 - i)
        d_str = d.isoformat()
        tasks = task_map.get(d_str, 0)
        sessions_val = sess_map.get(d_str, 0)
        # Approximation: 5 min per completed task, 5 min per session
        minutes = tasks * 5 + sessions_val * 5
        series.append({"date": d, "total_minutes": minutes})

    return {"granularity": granularity, "daily_goal_minutes": 30, "series": series}


async def get_module_breakdown(
    db: AsyncSession, parent_id: str, child_id: str, target_date: date | None = None,
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    if target_date is None:
        target_date = date.today()

    # Count answers per module for the date
    result = await db.execute(
        select(
            AnswerRecord.module,
            func.count().label("cnt"),
        )
        .where(
            AnswerRecord.child_id == child_id,
            func.date(AnswerRecord.answered_at) == target_date,
        )
        .group_by(AnswerRecord.module)
    )
    rows = result.all()
    total = sum(r.cnt for r in rows)
    modules = []
    for module, cnt in rows:
        pct = round(cnt / total * 100) if total > 0 else 0
        modules.append({
            "module": module,
            "module_label": MODULE_LABELS.get(module, module),
            "minutes": cnt * 2,  # approx 2 min per answer
            "percent": pct,
        })

    estimated_minutes = total * 2
    return {"date": target_date, "total_minutes": estimated_minutes, "modules": modules}
```

- [ ] **Step 3: Write router.py**

```python
"""Parent usage routes — daily/weekly/monthly series, module breakdown."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.db import get_db
from app.parent.usage.schemas import ModuleBreakdownOut, UsageSeriesOut
from app.parent.usage.service import get_module_breakdown, get_usage_series
from app.schemas.common import error, ok

usage_router = APIRouter(prefix="/children", tags=["parent-usage"])


@usage_router.get("/{child_id}/usage")
async def usage_series(
    child_id: str,
    granularity: str = Query(default="day", pattern=r"^(day|week|month)$"),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await get_usage_series(db, parent_id, child_id, granularity)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))
    return ok(UsageSeriesOut(**data).model_dump())


@usage_router.get("/{child_id}/usage/modules")
async def module_breakdown(
    child_id: str,
    date_param: date | None = Query(default=None, alias="date"),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await get_module_breakdown(db, parent_id, child_id, date_param)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))
    return ok(ModuleBreakdownOut(**data).model_dump())
```

- [ ] **Step 4: Write __init__.py**

```python
"""Parent usage tracking — daily/weekly/monthly series and module breakdown."""
```

- [ ] **Step 5: Write tests (3 cases)**

```python
"""Integration tests for parent usage API."""

import pytest
from httpx import AsyncClient
from app.auth.security import create_parent_access_token
from app.models.child import Child
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild


@pytest.fixture
async def _usage_setup(db_session):
    parent = ParentAccount(wx_openid="test_usage", status="active")
    db_session.add(parent)
    await db_session.flush()
    family = Family(name="时长测试家庭")
    db_session.add(family)
    await db_session.flush()
    child = Child(family_id=family.id, nickname="时长孩子")
    db_session.add(child)
    await db_session.flush()
    pc = ParentChild(parent_id=parent.id, child_id=child.id, family_id=family.id, status="active", is_default=True)
    db_session.add(pc)
    await db_session.commit()
    return create_parent_access_token(parent_id=str(parent.id)), str(child.id)


@pytest.mark.asyncio
async def test_usage_empty(async_client: AsyncClient, _usage_setup):
    token, child_id = _usage_setup
    res = await async_client.get(
        f"/v1/api/parent/children/{child_id}/usage",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert len(body["data"]["series"]) > 0


@pytest.mark.asyncio
async def test_module_breakdown_empty(async_client: AsyncClient, _usage_setup):
    token, child_id = _usage_setup
    res = await async_client.get(
        f"/v1/api/parent/children/{child_id}/usage/modules",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_usage_require_auth(async_client: AsyncClient):
    res = await async_client.get("/v1/api/parent/children/any-id/usage")
    assert res.status_code == 401
```

- [ ] **Step 6: Register usage_router in app/router.py**

```python
from app.parent.usage.router import usage_router
# ...
parent_router.include_router(usage_router)
```

- [ ] **Step 7: Run tests and commit**

```bash
cd cloud/backend && python -m pytest tests/test_parent_usage.py -v
```

```bash
git add app/parent/usage/ tests/test_parent_usage.py app/router.py
git commit -m "feat: add parent usage module (series + module breakdown)"
```

---

### Task 17: Online status module (1 GET endpoint)

**Files:**
- Create: `cloud/backend/app/parent/online/__init__.py`
- Create: `cloud/backend/app/parent/online/router.py`
- Create: `cloud/backend/app/parent/online/service.py`
- Create: `cloud/backend/app/parent/online/schemas.py`
- Create: `cloud/backend/tests/test_parent_online.py`
- Modify: `cloud/backend/app/router.py`

- [ ] **Step 1: Write schemas.py**

```python
"""Parent online status schemas."""

from datetime import datetime

from pydantic import BaseModel


class OnlineStatusOut(BaseModel):
    online: bool = False
    ws_connected: bool = False
    last_seen_at: datetime | None = None
    current_zone: str | None = None
    current_route_key: str | None = None
    current_activity: str | None = None
```

- [ ] **Step 2: Write service.py**

```python
"""Parent online status — in-memory cache for Phase 3, Redis for production."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.parent.service import verify_parent_access

# In-memory store: child_id -> status dict
# Phase 4: replace with Redis (key: online_status:{child_id}, TTL 300s)
_online_store: dict[str, dict] = {}

SHANGHAI_TZ = timezone(timedelta(hours=8))


async def get_online_status(
    db: AsyncSession, parent_id: str, child_id: str,
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None
    
    status = _online_store.get(child_id)
    if status is None:
        return {
            "online": False, "ws_connected": False,
            "last_seen_at": None, "current_zone": None,
            "current_route_key": None, "current_activity": None,
        }
    # Check if the status is stale (> 5 min since last update)
    last = status.get("updated_at")
    if last and (datetime.now(SHANGHAI_TZ) - last).total_seconds() > 300:
        status["online"] = False
        status["ws_connected"] = False
    return {
        "online": status.get("online", False),
        "ws_connected": status.get("ws_connected", False),
        "last_seen_at": status.get("last_seen_at"),
        "current_zone": status.get("current_zone"),
        "current_route_key": status.get("current_route_key"),
        "current_activity": status.get("current_activity"),
    }


# Called by car telemetry / WebSocket heartbeat (Phase 4)
def update_online_status(child_id: str, **kwargs) -> None:
    """Update in-memory online status for a child. Used by car heartbeat."""
    if child_id not in _online_store:
        _online_store[child_id] = {}
    _online_store[child_id].update(kwargs)
    _online_store[child_id]["updated_at"] = datetime.now(SHANGHAI_TZ)
```

- [ ] **Step 3: Write router.py**

```python
"""Parent online status route."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.db import get_db
from app.parent.online.schemas import OnlineStatusOut
from app.parent.online.service import get_online_status
from app.schemas.common import ok, error
from fastapi.responses import JSONResponse

online_router = APIRouter(prefix="/children", tags=["parent-online"])


@online_router.get("/{child_id}/online-status")
async def online_status(
    child_id: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await get_online_status(db, parent_id, child_id)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))
    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))
    return ok(OnlineStatusOut(**data).model_dump())
```

- [ ] **Step 4: Write __init__.py, tests, register router, commit**

Same pattern as Task 15. Tests: empty status returns offline=false, auth required, valid child.

```bash
git add app/parent/online/ tests/test_parent_online.py app/router.py
git commit -m "feat: add parent online status module (in-memory, Phase 4 Redis migration planned)"
```

---

### Task 18: Messages module (GET list, POST create, DELETE)

**Files:**
- Create: `cloud/backend/app/parent/messages/__init__.py`
- Create: `cloud/backend/app/parent/messages/router.py`
- Create: `cloud/backend/app/parent/messages/service.py`
- Create: `cloud/backend/app/parent/messages/schemas.py`
- Create: `cloud/backend/tests/test_parent_messages.py`
- Modify: `cloud/backend/app/router.py`

- [ ] **Step 1: Write schemas.py**

```python
"""Parent messages schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class MessageReply(BaseModel):
    reply_id: str
    type: str
    preset_code: str | None = None
    text: str | None = None
    created_at: datetime


class MessageOut(BaseModel):
    message_id: str
    direction: str
    type: str
    content: dict
    created_at: datetime
    replies: list[MessageReply] = []


class PaginatedMessages(BaseModel):
    items: list[MessageOut]
    pagination: dict


class SendMessageText(BaseModel):
    text: str


class SendMessageImage(BaseModel):
    file_id: str


class SendMessageAudio(BaseModel):
    file_id: str
    duration_ms: int = 0


class SendMessageTaskCard(BaseModel):
    task_id: str
    task_category: str
    module: str | None = None
    module_label: str | None = None
    title: str


class SendMessageRequest(BaseModel):
    type: str = Field(..., pattern=r"^(text|image|audio|task_card)$")
    content: dict
```

- [ ] **Step 2: Write service.py**

```python
"""Parent messages business logic."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import ParentMessage
from app.parent.service import verify_parent_access

SHANGHAI_TZ = timezone(timedelta(hours=8))


async def get_messages(
    db: AsyncSession, parent_id: str, child_id: str,
    page: int = 1, page_size: int = 20,
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    query = (
        select(ParentMessage)
        .where(
            ParentMessage.child_id == child_id,
            ParentMessage.parent_id == parent_id,
            ParentMessage.is_deleted == False,
        )
        .order_by(ParentMessage.created_at.desc())
    )
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    msgs = result.scalars().all()

    items = []
    for m in msgs:
        # Fetch replies
        reply_result = await db.execute(
            select(ParentMessage)
            .where(
                ParentMessage.replied_to_id == m.id,
                ParentMessage.is_deleted == False,
            )
            .order_by(ParentMessage.created_at)
        )
        replies = [
            {
                "reply_id": str(r.id), "type": r.msg_type,
                "preset_code": r.content.get("preset_code") if isinstance(r.content, dict) else None,
                "text": r.content.get("text") if isinstance(r.content, dict) else None,
                "created_at": r.created_at,
            }
            for r in reply_result.scalars().all()
        ]
        items.append({
            "message_id": str(m.id),
            "direction": m.direction,
            "type": m.msg_type,
            "content": m.content if isinstance(m.content, dict) else {},
            "created_at": m.created_at,
            "replies": replies,
        })

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        "items": items,
        "pagination": {"page": page, "page_size": page_size, "total": total, "total_pages": total_pages},
    }


async def create_message(
    db: AsyncSession, parent_id: str, child_id: str,
    msg_type: str, content: dict,
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    msg = ParentMessage(
        child_id=child_id,
        parent_id=parent_id,
        direction="parent_to_child",
        msg_type=msg_type,
        content=content,
    )
    db.add(msg)
    await db.flush()

    return {
        "message_id": str(msg.id),
        "direction": msg.direction,
        "type": msg.msg_type,
        "content": content,
        "created_at": msg.created_at,
        "replies": [],
    }


async def delete_message(
    db: AsyncSession, parent_id: str, child_id: str, message_id: str,
) -> bool:
    if not await verify_parent_access(db, parent_id, child_id):
        return False
    try:
        mid = uuid.UUID(message_id)
    except ValueError:
        return False
    result = await db.execute(
        select(ParentMessage).where(
            ParentMessage.id == mid,
            ParentMessage.child_id == child_id,
            ParentMessage.parent_id == parent_id,
        )
    )
    msg = result.scalar_one_or_none()
    if msg is None:
        return False
    msg.is_deleted = True
    await db.flush()
    return True
```

- [ ] **Step 3-6: Write router.py, __init__.py, tests, register, commit**

Router endpoints: GET list (`?page=1&page_size=20`), POST create, DELETE `/{message_id}`.
Tests: list empty, create text, create task_card, delete, auth required.
Same patterns as previous tasks.

```bash
git add app/parent/messages/ tests/test_parent_messages.py app/router.py
git commit -m "feat: add parent messages module (list/create/delete)"
```

---

### Task 19: Navigation module (1 POST endpoint)

**Files:**
- Create: `cloud/backend/app/parent/navigation/__init__.py`
- Create: `cloud/backend/app/parent/navigation/router.py`
- Create: `cloud/backend/app/parent/navigation/service.py`
- Create: `cloud/backend/app/parent/navigation/schemas.py`
- Create: `cloud/backend/tests/test_parent_navigation.py`
- Modify: `cloud/backend/app/router.py`

- [ ] **Step 1: Write schemas.py**

```python
"""Parent navigation schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class NavigationRequest(BaseModel):
    destination: str = Field(..., pattern=r"^(learning|chat|parent_messages)$")
    route_key: str
    module: str | None = None
    custom_batch_size: int | None = Field(default=None, ge=1, le=20)
    title: str | None = None
    expires_in_seconds: int = Field(default=600, ge=60, le=3600)


class NavigationOut(BaseModel):
    navigation_id: str
    destination: str
    route_key: str
    module: str | None = None
    custom_batch_size: int | None = None
    title: str | None = None
    expires_at: datetime
    created_at: datetime
```

- [ ] **Step 2: Write service.py**

```python
"""Parent navigation business logic."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.navigation import NavigationInstruction
from app.parent.service import verify_parent_access

SHANGHAI_TZ = timezone(timedelta(hours=8))


async def create_navigation(
    db: AsyncSession, parent_id: str, child_id: str,
    destination: str, route_key: str,
    module: str | None = None,
    custom_batch_size: int | None = None,
    title: str | None = None,
    expires_in_seconds: int = 600,
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    now = datetime.now(SHANGHAI_TZ)
    expires_at = now + timedelta(seconds=expires_in_seconds)

    nav = NavigationInstruction(
        child_id=child_id,
        parent_id=parent_id,
        destination=destination,
        route_key=route_key,
        module=module,
        custom_batch_size=custom_batch_size,
        title=title,
        expires_at=expires_at,
        status="pending",
    )
    db.add(nav)
    await db.flush()

    return {
        "navigation_id": str(nav.id),
        "destination": destination,
        "route_key": route_key,
        "module": module,
        "custom_batch_size": custom_batch_size,
        "title": title,
        "expires_at": expires_at,
        "created_at": now,
    }
```

- [ ] **Step 3-6: Write router.py, __init__.py, tests, register, commit**

POST `/{child_id}/navigations`.
Tests: create learning nav, create chat nav, module required for learning, auth required.

```bash
git add app/parent/navigation/ tests/test_parent_navigation.py app/router.py
git commit -m "feat: add parent navigation module (remote control instructions)"
```

---

### Task 20: Notifications module (settings GET/PUT, notification list/read)

**Files:**
- Create: `cloud/backend/app/parent/notifications/__init__.py`
- Create: `cloud/backend/app/parent/notifications/router.py`
- Create: `cloud/backend/app/parent/notifications/service.py`
- Create: `cloud/backend/app/parent/notifications/schemas.py`
- Create: `cloud/backend/tests/test_parent_notifications.py`
- Modify: `cloud/backend/app/router.py`

- [ ] **Step 1: Write schemas.py**

```python
"""Parent notification schemas."""

from datetime import datetime, time

from pydantic import BaseModel, Field

DEFAULT_SETTINGS = {
    "task_completed": True, "task_expired": True,
    "child_replied": True, "behavior_alert": True,
    "realtime_alert": True, "goal_achieved": True,
    "daily_summary": True, "weekly_report": True,
    "device_offline": True, "learning_milestone": False,
}


class DndSettings(BaseModel):
    enabled: bool = False
    start_time: str = "22:00"
    end_time: str = "08:00"


class UpdateNotificationSettingsRequest(BaseModel):
    settings: dict = Field(default_factory=dict)
    dnd: DndSettings = Field(default_factory=DndSettings)


class NotificationSettingsOut(BaseModel):
    child_id: str
    settings: dict
    dnd: DndSettings
    updated_at: datetime | None = None


class NotificationItem(BaseModel):
    notification_id: str
    type: str
    icon: str = ""
    title: str
    description: str
    child_id: str
    child_nickname: str = ""
    is_read: bool = False
    created_at: datetime


class PaginatedNotifications(BaseModel):
    unread_count: int = 0
    items: list[NotificationItem] = []
    pagination: dict
```

- [ ] **Step 2: Write service.py**

```python
"""Parent notifications business logic."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationSettings
from app.parent.service import verify_parent_access

SHANGHAI_TZ = timezone(timedelta(hours=8))
DEFAULT_SETTINGS = {
    "task_completed": True, "task_expired": True,
    "child_replied": True, "behavior_alert": True,
    "realtime_alert": True, "goal_achieved": True,
    "daily_summary": True, "weekly_report": True,
    "device_offline": True, "learning_milestone": False,
}


async def get_notification_settings(
    db: AsyncSession, parent_id: str, child_id: str,
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None
    result = await db.execute(
        select(NotificationSettings).where(NotificationSettings.child_id == child_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return {
            "child_id": child_id, "settings": DEFAULT_SETTINGS,
            "dnd": {"enabled": False, "start_time": "22:00", "end_time": "08:00"},
            "updated_at": None,
        }
    return {
        "child_id": str(row.child_id),
        "settings": row.settings if isinstance(row.settings, dict) else DEFAULT_SETTINGS,
        "dnd": {
            "enabled": row.dnd_enabled,
            "start_time": row.dnd_start_time.isoformat() if row.dnd_start_time else "22:00",
            "end_time": row.dnd_end_time.isoformat() if row.dnd_end_time else "08:00",
        },
        "updated_at": row.updated_at,
    }


async def update_notification_settings(
    db: AsyncSession, parent_id: str, child_id: str,
    settings: dict, dnd_enabled: bool, dnd_start: str, dnd_end: str,
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    from datetime import time
    st = time.fromisoformat(dnd_start) if dnd_start else None
    et = time.fromisoformat(dnd_end) if dnd_end else None

    stmt = pg_insert(NotificationSettings).values(
        child_id=child_id,
        settings=settings,
        dnd_enabled=dnd_enabled,
        dnd_start_time=st,
        dnd_end_time=et,
    ).on_conflict_do_update(
        index_elements=["child_id"],
        set_={
            "settings": settings,
            "dnd_enabled": dnd_enabled,
            "dnd_start_time": st,
            "dnd_end_time": et,
        },
    ).returning(NotificationSettings)
    result = await db.execute(stmt)
    row = result.scalar_one()
    await db.flush()
    return {
        "child_id": str(row.child_id),
        "settings": row.settings if isinstance(row.settings, dict) else DEFAULT_SETTINGS,
        "dnd": {
            "enabled": row.dnd_enabled,
            "start_time": row.dnd_start_time.isoformat() if row.dnd_start_time else "22:00",
            "end_time": row.dnd_end_time.isoformat() if row.dnd_end_time else "08:00",
        },
        "updated_at": row.updated_at,
    }


async def get_notifications(
    db: AsyncSession, parent_id: str,
    filter_type: str = "all", page: int = 1, page_size: int = 20,
) -> dict:
    # Notification endpoints are parent-scoped (no child_id), no verify_parent_access
    query = select(Notification).where(Notification.parent_id == parent_id)
    if filter_type == "unread":
        query = query.where(Notification.is_read == False)

    query = query.order_by(Notification.created_at.desc())

    # Unread count
    unread_q = select(func.count()).select_from(
        select(Notification).where(
            Notification.parent_id == parent_id,
            Notification.is_read == False,
        ).subquery()
    )
    unread = (await db.execute(unread_q)).scalar() or 0

    # Count total
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.scalars().all()
    items = [
        {
            "notification_id": str(r.id), "type": r.notif_type, "icon": "",
            "title": r.title, "description": r.description,
            "child_id": str(r.child_id), "child_nickname": "",
            "is_read": r.is_read, "created_at": r.created_at,
        }
        for r in rows
    ]
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        "unread_count": unread, "items": items,
        "pagination": {"page": page, "page_size": page_size, "total": total, "total_pages": total_pages},
    }


async def mark_notification_read(
    db: AsyncSession, parent_id: str, notification_id: str,
) -> dict | None:
    try:
        nid = uuid.UUID(notification_id)
    except ValueError:
        return None
    result = await db.execute(
        select(Notification).where(
            Notification.id == nid,
            Notification.parent_id == parent_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    row.is_read = True
    row.read_at = datetime.now(SHANGHAI_TZ)
    await db.flush()
    return {"notification_id": notification_id, "is_read": True, "read_at": row.read_at}
```

- [ ] **Step 3-6: Write router.py, __init__.py, tests, register, commit**

Note: notification list and read endpoints use `prefix=""` (parent-scoped, no child_id in path).
Settings endpoints use `prefix="/children"` (child-scoped).

Tests: 6 cases covering settings get/update, notification list empty/filtered, mark read, auth.

```bash
git add app/parent/notifications/ tests/test_parent_notifications.py app/router.py
git commit -m "feat: add parent notifications module (settings CRUD + notification center)"
```

---

### Task 21: Files module (3 endpoints)

**Files:**
- Create: `cloud/backend/app/parent/files/__init__.py`
- Create: `cloud/backend/app/parent/files/router.py`
- Create: `cloud/backend/app/parent/files/service.py`
- Create: `cloud/backend/app/parent/files/schemas.py`
- Create: `cloud/backend/tests/test_parent_files.py`
- Modify: `cloud/backend/app/router.py`

- [ ] **Step 1: Write schemas.py, service.py, router.py**

File service in Phase 3 uses local disk storage (`uploads/` directory). Production: replace with OSS/S3 presigned URLs.

Router has 3 endpoints:
1. `POST /v1/api/parent/files/uploads` — init upload, returns upload_id and local path
2. `POST /v1/api/parent/files/uploads/{upload_id}/complete` — confirm upload, mark status=available
3. `GET /v1/api/parent/files/{file_id}/access` — get access URL (local path for dev)

- [ ] **Step 2: Write tests, register, commit**

```bash
git add app/parent/files/ tests/test_parent_files.py app/router.py
git commit -m "feat: add parent files module (upload init/complete/access)"
```

---

### Task 22: Update reports weekly endpoint to consume behavior_event data

**Files:**
- Modify: `cloud/backend/app/parent/reports/service.py`

- [ ] **Step 1: Update _build_weekly_report to query behavior_event**

Replace the hardcoded behavior fields in `_build_weekly_report()` with actual queries against `BehaviorEvent`:

```python
    # --- Behavior data (from behavior_event table) ---
    from app.models.behavior import BehaviorEvent

    # Focus score for this week
    focus_result = await db.execute(
        select(func.avg(BehaviorEvent.score))
        .where(
            BehaviorEvent.child_id == child_id,
            BehaviorEvent.event_type == "focus",
            func.date(BehaviorEvent.recorded_at).between(monday, sunday),
        )
    )
    focus_avg = focus_result.scalar()
    focus_score = int(focus_avg) if focus_avg else 0

    # Posture score for this week
    posture_result = await db.execute(
        select(func.avg(BehaviorEvent.score))
        .where(
            BehaviorEvent.child_id == child_id,
            BehaviorEvent.event_type == "posture",
            func.date(BehaviorEvent.recorded_at).between(monday, sunday),
        )
    )
    posture_avg = posture_result.scalar()
    posture_score = int(posture_avg) if posture_avg else 0

    # Focus daily series
    focus_series_result = await db.execute(
        select(
            func.date(BehaviorEvent.recorded_at).label("d"),
            func.avg(BehaviorEvent.score).label("avg_score"),
        )
        .where(
            BehaviorEvent.child_id == child_id,
            BehaviorEvent.event_type == "focus",
            func.date(BehaviorEvent.recorded_at).between(monday, sunday),
        )
        .group_by(func.date(BehaviorEvent.recorded_at))
        .order_by(func.date(BehaviorEvent.recorded_at))
    )
    focus_series = [
        {"date": date.fromisoformat(str(r.d)), "score": int(r.avg_score)}
        for r in focus_series_result.all()
    ]

    # Anomalies and discoveries from behavior insights
    from app.models.behavior import BehaviorEvent
    insight_result = await db.execute(
        select(BehaviorEvent)
        .where(
            BehaviorEvent.child_id == child_id,
            BehaviorEvent.event_type.in_(["focus", "posture"]),
            func.date(BehaviorEvent.recorded_at).between(monday, sunday),
        )
        .limit(20)
    )
    anomalies = []
    discoveries = []
    for e in insight_result.scalars().all():
        p = e.payload if isinstance(e.payload, dict) else {}
        if p.get("is_anomaly"):
            anomalies.append({
                "title": p.get("title", ""),
                "description": p.get("description", ""),
                "tags": [{"text": t.get("text", ""), "cls": t.get("cls", "")} for t in p.get("tags", [])],
            })
        if p.get("is_discovery"):
            discoveries.append({
                "title": p.get("title", ""),
                "description": p.get("description", ""),
                "color": p.get("color", "#778ccd"),
            })

    return {
        # ... existing fields remain ...
        "behavior_summary": {
            "focus_score": focus_score, "focus_change_percent": 0,
            "posture_score": posture_score, "posture_change_percent": 0,
            "anomaly_count": len(anomalies), "discovery_count": len(discoveries),
        },
        "focus_daily_series": focus_series,
        "posture_weekly_series": [],
        "anomalies": anomalies,
        "discoveries": discoveries,
        "ai_summary": "",
    }
```

- [ ] **Step 2: Run reports tests, commit**

```bash
cd cloud/backend && python -m pytest tests/test_parent_reports.py -v
```

```bash
git add app/parent/reports/service.py
git commit -m "feat: wire weekly reports to behavior_event data (Phase 3 integration)"
```

---

## Phase 3: Seed Scripts (Tasks 23-24)

### Task 23: Write seed_behavior_data.py

**Files:**
- Create: `cloud/backend/scripts/seed_behavior_data.py`

- [ ] **Step 1: Write the seed script**

The script generates 14 days of behavior events for each child in the database:

```python
"""Seed behavior events for demo — 14 days of focus/posture/location/zone data.

Usage: cd cloud/backend && python scripts/seed_behavior_data.py
"""

import asyncio
import random
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db import async_engine
from app.models.behavior import BehaviorEvent
from app.models.child import Child

SHANGHAI_TZ = timezone(timedelta(hours=8))

ZONES = ["客厅", "书房", "卧室"]
FOCUS_INSIGHTS = [
    {"title": "周三下午专注度骤降", "description": "15:30-16:20 跌至 62 分，与自由探索时间吻合。", "tags": [{"text":"专注度","cls":"tf"},{"text":"使用时长","cls":"tt"}]},
    {"title": "早上专注度最佳", "description": "9:00-11:00 专注度平均 88 分，比下午高 15%。", "tags": [{"text":"专注度","cls":"tf"}]},
]
POSTURE_INSIGHTS = [
    {"title": "使用时长>90分钟→坐姿问题+40%", "description": "3天超过90分钟，坐姿问题次数平均多出40%。", "tags": [{"text":"坐姿","cls":"tp"},{"text":"使用时长","cls":"tt"}]},
    {"title": "连续3天坐姿改善", "description": "本周坐姿评分持续上升，提醒次数减少。", "tags": [{"text":"坐姿","cls":"tp"}]},
]


async def seed_behavior_for_child(session: AsyncSession, child_id: uuid.UUID) -> None:
    """Generate 14 days of behavior events for one child."""
    today = date.today()
    for days_ago in range(14):
        d = today - timedelta(days=days_ago)
        dt = datetime(d.year, d.month, d.day, tzinfo=SHANGHAI_TZ)

        # 8 focus events per day (roughly one per hour during learning hours)
        for hour in [9, 10, 11, 14, 15, 16, 17, 19]:
            event_time = dt.replace(hour=hour, minute=random.randint(0, 59))
            base_score = 85 + random.randint(-10, 10)
            # Worse on weekends (day 5,6 of week)
            if d.weekday() in (5, 6):
                base_score -= random.randint(5, 15)
            is_distracted = random.random() < 0.15
            is_interrupted = random.random() < 0.10
            payload = {
                "focus_duration_seconds": random.randint(60, 1800),
                "is_distracted": is_distracted,
                "interrupted": is_interrupted,
                "activity": random.choice(["math", "science", "english", "poems", "music"]),
            }
            # Attach insight to some events
            if days_ago == 3 and hour == 15 and random.random() < 0.7:
                payload["insight"] = FOCUS_INSIGHTS[0]
                payload["is_anomaly"] = True
                payload["title"] = FOCUS_INSIGHTS[0]["title"]
                payload["description"] = FOCUS_INSIGHTS[0]["description"]
                payload["tags"] = FOCUS_INSIGHTS[0]["tags"]
            if days_ago == 7 and hour == 9 and random.random() < 0.7:
                payload["insight"] = FOCUS_INSIGHTS[1]
                payload["is_discovery"] = True
                payload["title"] = FOCUS_INSIGHTS[1]["title"]
                payload["description"] = FOCUS_INSIGHTS[1]["description"]
                payload["color"] = "#f9b370"

            session.add(BehaviorEvent(
                child_id=child_id, event_type="focus",
                score=max(0, min(100, base_score)),
                payload=payload, recorded_at=event_time,
            ))

        # 3-5 posture events per day
        for _ in range(random.randint(3, 5)):
            event_time = dt.replace(hour=random.randint(8, 20), minute=random.randint(0, 59))
            posture_label = random.choices(["good", "slight_tilt", "obvious_slant"], weights=[7, 2, 1])[0]
            score_map = {"good": 85, "slight_tilt": 60, "obvious_slant": 35}
            payload = {"posture_label": posture_label, "reminder_sent": posture_label != "good"}
            if days_ago == 2 and posture_label == "obvious_slant" and random.random() < 0.7:
                payload["insight"] = POSTURE_INSIGHTS[0]
                payload["is_discovery"] = True
                payload["title"] = POSTURE_INSIGHTS[0]["title"]
                payload["description"] = POSTURE_INSIGHTS[0]["description"]
                payload["color"] = "#778ccd"
            session.add(BehaviorEvent(
                child_id=child_id, event_type="posture",
                score=score_map[posture_label] + random.randint(-5, 5),
                payload=payload, recorded_at=event_time,
            ))

        # 1-2 zone events per day
        zone = random.choice(ZONES)
        for _ in range(random.randint(1, 2)):
            event_time = dt.replace(hour=random.randint(8, 20), minute=random.randint(0, 59))
            session.add(BehaviorEvent(
                child_id=child_id, event_type="location",
                score=100, payload={"zone_name": zone, "zone_change": False},
                recorded_at=event_time,
            ))

    await session.flush()
    print(f"  Behavior events seeded for child {child_id}")


async def main():
    session_factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        result = await session.execute(select(Child).limit(10))
        children = result.scalars().all()
        if not children:
            from app.models.family import Family
            family = Family(name="种子家庭-行为")
            session.add(family)
            await session.flush()
            child = Child(family_id=family.id, nickname="测试孩子")
            session.add(child)
            await session.flush()
            children = [child]
            print(f"Created child: {child.nickname} ({child.id})")

        for child in children:
            # Check if already seeded
            existing = await session.execute(
                select(BehaviorEvent).where(BehaviorEvent.child_id == child.id).limit(1)
            )
            if existing.scalar_one_or_none():
                print(f"  Child {child.id} already has behavior data, skipping")
                continue
            await seed_behavior_for_child(session, child.id)

        await session.commit()
        print("Seed behavior data complete.")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Verify script runs**

```bash
cd cloud/backend && python scripts/seed_behavior_data.py
```

- [ ] **Step 3: Commit**

```bash
git add scripts/seed_behavior_data.py
git commit -m "feat: add behavior event seed script (14 days per child)"
```

---

### Task 24: Write seed_full_demo.py — one-shot full demo setup

**Files:**
- Create: `cloud/backend/scripts/seed_full_demo.py`

- [ ] **Step 1: Write the script**

This script orchestrates all seeding: family → child → device → config → goal → content → tasks → sessions → answers → behavior. It calls existing seed functions and adds the missing pieces.

```python
"""One-shot full demo data seeder.

Creates a complete demo environment with:
  - 1 family, 1 child, 1 device binding
  - 6 module configs with defaults
  - Learning goal (120 min/day)
  - Content for all 6 modules
  - 7 days of daily tasks
  - 5 completed learning sessions with answers
  - 14 days of behavior events

Usage: cd cloud/backend && python scripts/seed_full_demo.py
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db import async_engine
from app.models.child import Child
from app.models.family import Family
from app.models.parent_child import ParentChild
from app.models.parent import ParentAccount
from app.models.device_binding import DeviceBinding
from scripts.seed_learning_data import seed_configs, seed_content
from scripts.seed_behavior_data import seed_behavior_for_child


async def main():
    session_factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        # 1. Create demo parent
        parent = ParentAccount(wx_openid="demo_parent_seed", nickname="演示家长", status="active", phone_masked="138****0000")
        existing = await session.execute(select(ParentAccount).where(ParentAccount.wx_openid == "demo_parent_seed"))
        if existing.scalar_one_or_none():
            print("Demo data already exists, skipping.")
            return
        session.add(parent)
        await session.flush()

        # 2. Create family
        family = Family(name="演示家庭")
        session.add(family)
        await session.flush()

        # 3. Create child
        child = Child(family_id=family.id, nickname="小宇", birth_date="2019-06-01", gender="boy")
        session.add(child)
        await session.flush()

        # 4. Parent-child binding
        pc = ParentChild(parent_id=parent.id, child_id=child.id, family_id=family.id, status="active", is_default=True)
        session.add(pc)

        # 5. Device binding
        device = DeviceBinding(device_id="demo_car_001", child_id=child.id, device_name="小宇的车机", device_type="car", bind_status="active")
        session.add(device)

        await session.flush()
        print(f"Created: parent={parent.id}, family={family.id}, child={child.id}")

        # 6. Seed configs and content
        await seed_configs(session, child.id)
        await seed_content(session)

        # 7. Seed learning goal (via raw insert — reuse goal module defaults)
        from app.models.config import LearningGoal
        session.add(LearningGoal(
            child_id=child.id, daily_goal_minutes=120,
            module_goals=[
                {"module": "math", "goal_minutes": 30},
                {"module": "science", "goal_minutes": 20},
                {"module": "english", "goal_minutes": 20},
                {"module": "poems", "goal_minutes": 20},
                {"module": "music", "goal_minutes": 15},
                {"module": "quiz", "goal_minutes": 15},
            ],
        ))

        # 8. Create 7 days of daily tasks
        from datetime import date, datetime, timedelta, timezone
        from app.models.task import DailyTask
        tz = timezone(timedelta(hours=8))
        today = date.today()
        modules = ["math", "science", "english", "poems", "music", "quiz"]
        for days_ago in range(7):
            d = today - timedelta(days=days_ago)
            for mod in modules:
                expires = datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=tz)
                status = "completed" if days_ago > 0 else random.choice(["completed", "in_progress", "assigned"])
                session.add(DailyTask(
                    child_id=child.id, business_date=d, module=mod,
                    task_category="learning", title=f"今日{MODULE_LABELS[mod]}",
                    status=status, progress_completed=random.randint(5, 10) if status == "completed" else 0,
                    progress_total=10, expires_at=expires,
                ))

        # 9. Create learning sessions with answers
        from app.models.learning import LearningSession
        from app.models.answer import AnswerRecord
        import random
        for days_ago in [1, 2, 3, 4, 5]:
            d = today - timedelta(days=days_ago)
            for mod in random.sample(modules, 3):
                st = datetime(d.year, d.month, d.day, random.randint(9, 17), 0, 0, tzinfo=tz)
                session_obj = LearningSession(child_id=child.id, module=mod, source="today_task", status="completed", created_at=st)
                session.add(session_obj)
                await session.flush()
                # Generate 5-10 answers per session
                for _ in range(random.randint(5, 10)):
                    is_correct = random.random() < 0.75
                    session.add(AnswerRecord(
                        session_id=session_obj.id, batch_item_id=uuid.uuid4(),
                        child_id=child.id, module=mod,
                        question_snapshot={"question": f"Demo question {_}", "options": []},
                        selected_option_id="A" if is_correct else "B",
                        correct_option_id="A", is_correct=is_correct,
                        answer_duration_ms=random.randint(2000, 15000),
                        answered_at=st + timedelta(minutes=random.randint(1, 30)),
                    ))

        await session.flush()
        print("Created: tasks, sessions, answers")

        # 10. Seed behavior events
        await seed_behavior_for_child(session, child.id)

        await session.commit()
        print("\n=== Full demo seed complete! ===")
        print(f"Parent demo_openid: demo_parent_seed")
        print(f"Child ID: {child.id}")
        print(f"Run: uvicorn app.main:app --reload")
        print(f"Then: GET /v1/api/parent/children/{child.id}/behavior/focus (with JWT)")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Test and commit**

```bash
git add scripts/seed_full_demo.py
git commit -m "feat: add one-shot full demo seed script (family→child→device→content→tasks→sessions→answers→behavior)"
```

---

## Phase 4: Deployment Documentation (Task 25)

### Task 25: Write deployment guide for 88bill99.top

**Files:**
- Create: `cloud/backend/docs/deployment.md`

- [ ] **Step 1: Write deployment.md**

A step-by-step guide in Chinese for deploying on the server 88bill99.top. Cover:

1. Prerequisites (Docker, Docker Compose, git)
2. Clone repo
3. Configure .env (JWT_SECRET, WX_APPID, WX_SECRET, DATABASE_URL pointing to docker db service)
4. `docker compose up -d`
5. `docker compose exec backend alembic upgrade head`
6. `docker compose exec backend python scripts/seed_full_demo.py`
7. Nginx config snippet for reverse proxy
8. Verify: `curl https://88bill99.top/health`
9. Troubleshooting (DB connection, port conflicts, CORS)

- [ ] **Step 2: Commit**

```bash
git add docs/deployment.md
git commit -m "docs: add deployment guide for 88bill99.top server"
```

---

## Phase 5: Final Integration (Task 26)

### Task 26: Full test suite run and router audit

- [ ] **Step 1: Run all tests**

```bash
cd cloud/backend && python -m pytest tests/ -v --tb=short
```

- [ ] **Step 2: Verify router.py has all 8 new routers registered**

```python
from app.parent.behavior.router import behavior_router
from app.parent.usage.router import usage_router
from app.parent.online.router import online_router
from app.parent.messages.router import messages_router
from app.parent.navigation.router import navigation_router
from app.parent.notifications.router import notifications_router
from app.parent.files.router import files_router
```

And all included on `parent_router`:
```python
parent_router.include_router(behavior_router)
parent_router.include_router(usage_router)
parent_router.include_router(online_router)
parent_router.include_router(messages_router)
parent_router.include_router(notifications_router)
parent_router.include_router(navigation_router)
parent_router.include_router(files_router)
```

- [ ] **Step 3: Verify alembic/env.py imports all 6 new models**

- [ ] **Step 4: Run ruff lint**

```bash
cd cloud/backend && ruff check app/ tests/ scripts/
```

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: complete Phase 3 — 7 new modules, 6 models, 9 fixes, seed scripts, deployment docs

New modules: behavior, usage, online, messages, navigation, notifications, files
New models: BehaviorEvent, ParentMessage, NavigationInstruction, NotificationSettings, Notification, FileUpload
Fixes: goal sum validation, dispatch learning block, pepper→config, CORS comment, docstrings, reports TODOs
Scripts: seed_behavior_data.py, seed_full_demo.py
Docs: deployment.md"
```

---

## Plan Summary

| Phase | Tasks | Files Created | Files Modified |
|-------|-------|--------------|----------------|
| 0: Fixes | 8 | 0 | 10 |
| 1: Models | 6 | 6 (models) + 1 (migration) | 2 (env, conftest) |
| 2: API Modules | 8 | 32 (8 modules × 4 files) + 7 (tests) | 1 (router.py) |
| 3: Seed Scripts | 2 | 2 | 0 |
| 4: Deployment | 1 | 1 | 0 |
| 5: Integration | 1 | 0 | 3 |
| **Total** | **26** | **~50 new files** | **~16 modified files** |

**Estimated: ~2,500 lines of new code + ~1,500 lines of tests**
