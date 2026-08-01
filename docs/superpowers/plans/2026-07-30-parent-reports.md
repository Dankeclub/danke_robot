# Phase 3: 家长端学习报告与深度链路 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 12 个家长端 API 端点，覆盖学习目标设置、任务派发、学习进度/会话/错题/周报查询。

**Architecture:** 3 个新模块 `goal/`、`dispatch/`、`reports/`，遵循现有 `router → service → schemas` 三层模式。1 张新表 `learning_goal`，1 个 DDL 放宽 `daily_task.module` 约束。周报实时聚合，行为层返回 placeholder。

**Tech Stack:** Python 3.13, FastAPI 0.136.3, SQLAlchemy 2.0.43 (async), Pydantic v2, Alembic, pytest + httpx AsyncClient

## Global Constraints

- 所有端点使用 `ApiEnvelope` 包装 (`ok()` / `error()` helper)
- 所有端点通过 `Depends(get_current_parent)` 鉴权
- 子资源访问必须验证 `verify_parent_access(db, parent_id, child_id)`
- 时区统一使用 Asia/Shanghai (UTC+8)
- 返回字段对齐 `cloud/backend/docs/parent-openapi.yaml` schemas
- ruff 零告警，所有测试通过
- 遵循现有命名约定：router 变量 `X_router`，前缀 `"/children"`，tags `"parent-X"`
- 分支：`feature/parent-reports`（从 main 切出，Phase 2 已 commit）

---

### Task 0: 分支准备 — Commit Phase 2 + 切 feature/parent-reports

**Files:**
- Modify: 无（git 操作）
- Create: 无

**Produces:** 干净的 `feature/parent-reports` 分支，所有 Phase 2 代码已提交在 `feature/car-learning-chain`。

- [ ] **Step 1: 检查当前状态**

```bash
git status --short --branch
```

- [ ] **Step 2: Commit Phase 2 changes on feature/car-learning-chain**

```bash
git add cloud/backend/alembic/versions/20260729_f9d0e1f2a3b4_create_config_audit.py
git add cloud/backend/app/parent/
git add cloud/backend/tests/test_parent_children.py
git add cloud/backend/tests/test_parent_config.py
git add cloud/backend/tests/test_parent_dashboard.py
git add cloud/backend/tests/test_parent_device.py
git add cloud/backend/app/models/config.py
git add cloud/backend/app/router.py
git add cloud/backend/app/auth/router_car.py
git add cloud/backend/app/auth/router_parent.py
git add cloud/backend/app/auth/schemas.py
git add cloud/backend/alembic/env.py
git add cloud/backend/tests/conftest.py
git commit -m "feat: Phase 2 parent backend core — children, device, config, dashboard (14 files, 9 endpoints, 18 tests)

- 4 modules: children/device/config/dashboard (13 files)
- 1 model: ConfigAudit + 1 migration
- 9 APIs: GET/POST children, GET/PUT/DELETE child, GET/PUT/DELETE device, POST bind, GET/PUT config, GET audit, GET dashboard
- Fixed parent auth: wx_code/app_id/invite_code, RefreshTokenRequest, /token/refresh
- 46/46 tests pass, ruff 0 warnings"
```

- [ ] **Step 3: 切回 main 并创建新分支**

```bash
git checkout main
git checkout -b feature/parent-reports
```

- [ ] **Step 4: 验证分支干净**

```bash
git log --oneline -3
```

---

### Task 1: 数据库模型 — LearningGoal + 放宽 daily_task 约束

**Files:**
- Modify: `cloud/backend/app/models/config.py` (行 104 之后追加)
- Modify: `cloud/backend/tests/conftest.py` (行 14)
- Create: `cloud/backend/alembic/versions/20260730_a1b2c3_learning_goal.py`
- Create: `cloud/backend/alembic/versions/20260730_a1b2c4_relax_daily_task_module.py`

**Interfaces:**
- Produces: `LearningGoal` ORM model (`app.models.config.LearningGoal`)
- Produces: `learning_goal` 表 (id, child_id, daily_goal_minutes, module_goals JSONB, created_at, updated_at)
- Produces: `daily_task.module` → nullable, CHECK 约束放宽

- [ ] **Step 1: 在 config.py 中新增 LearningGoal model**

在 `app/models/config.py` 文件末尾（`ConfigAudit` 类之后）追加：

```python
class LearningGoal(Base):
    """Per-child daily learning time goals.

    One row per child. Stores total daily_goal_minutes and per-module
    goal_minutes as a JSONB array. Updated by parents via the learning
    goal endpoint.
    """

    __tablename__ = "learning_goal"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child.id"), nullable=False
    )
    daily_goal_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30
    )
    module_goals: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=list
    )
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
        UniqueConstraint("child_id", name="uq_learning_goal_child"),
        Index("idx_learning_goal_child", "child_id"),
    )
```

- [ ] **Step 2: 在 conftest.py 中导入 LearningGoal**

修改 `cloud/backend/tests/conftest.py` 第 14 行：

```python
# Before:
from app.models.config import ConfigAudit, LearningModuleConfig  # noqa: F401
# After:
from app.models.config import ConfigAudit, LearningGoal, LearningModuleConfig  # noqa: F401
```

- [ ] **Step 3: 创建 learning_goal 迁移**

创建文件 `cloud/backend/alembic/versions/20260730_a1b2c3_learning_goal.py`：

```python
"""create learning_goal

Revision ID: a1b2c3d4e5f6
Revises: f9d0e1f2a3b4
Create Date: 2026-07-30 10:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: str | Sequence[str] | None = 'f9d0e1f2a3b4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'learning_goal',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            'child_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('child.id'),
            nullable=False,
        ),
        sa.Column(
            'daily_goal_minutes',
            sa.Integer(),
            nullable=False,
            server_default=sa.text('30'),
        ),
        sa.Column(
            'module_goals',
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
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
        sa.UniqueConstraint('child_id', name='uq_learning_goal_child'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_learning_goal_child', 'learning_goal', ['child_id'])


def downgrade() -> None:
    op.drop_table('learning_goal')
```

- [ ] **Step 4: 创建 daily_task 约束放宽迁移**

创建文件 `cloud/backend/alembic/versions/20260730_a1b2c4_relax_daily_task_module.py`：

```python
"""relax daily_task module constraint to allow NULL

Revision ID: a1b2c4d5e6f7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-30 10:01:00.000000

"""
from collections.abc import Sequence

from alembic import op

revision: str = 'a1b2c4d5e6f7'
down_revision: str | Sequence[str] | None = 'a1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE daily_task ALTER COLUMN module DROP NOT NULL")
    op.execute("ALTER TABLE daily_task DROP CONSTRAINT IF EXISTS ck_task_module")
    op.execute(
        "ALTER TABLE daily_task ADD CONSTRAINT ck_task_module "
        "CHECK (module IS NULL OR module IN "
        "('science','math','english','poems','music','quiz'))"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE daily_task SET module = 'custom' WHERE module IS NULL"
    )
    op.execute("ALTER TABLE daily_task DROP CONSTRAINT IF EXISTS ck_task_module")
    op.execute(
        "ALTER TABLE daily_task ADD CONSTRAINT ck_task_module "
        "CHECK (module IN ('science','math','english','poems','music','quiz'))"
    )
    op.execute("ALTER TABLE daily_task ALTER COLUMN module SET NOT NULL")
```

- [ ] **Step 5: 验证模型导入正确**

```bash
cd cloud/backend && python -c "from app.models.config import LearningGoal; print('LearningGoal imported OK, table:', LearningGoal.__tablename__)"
```

Expected: `LearningGoal imported OK, table: learning_goal`

---

### Task 2: 共享时区工具 — 提取到 parent/service.py

**Files:**
- Modify: `cloud/backend/app/parent/service.py`
- Modify: `cloud/backend/app/parent/dashboard/service.py`

**Interfaces:**
- Produces: `today_shanghai() -> date`
- Produces: `datetime_range_shanghai(d: date) -> tuple[datetime, datetime]`
- Consumes: 来自 datetime, timezone, timedelta 标准库

- [ ] **Step 1: 在 parent/service.py 末尾添加时区工具**

在 `cloud/backend/app/parent/service.py` 末尾追加：

```python
from datetime import date, datetime, timedelta, timezone


def today_shanghai() -> date:
    """Return today's date in Asia/Shanghai timezone."""
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).date()


def datetime_range_shanghai(d: date) -> tuple[datetime, datetime]:
    """Return [start_of_day, start_of_next_day) in Asia/Shanghai TZ."""
    tz = timezone(timedelta(hours=8))
    start = datetime(d.year, d.month, d.day, tzinfo=tz)
    end = start + timedelta(days=1)
    return start, end
```

- [ ] **Step 2: 重构 dashboard/service.py 使用共享工具**

修改 `cloud/backend/app/parent/dashboard/service.py`：

```python
# 删除第 3-4 行的 standalone import:
# from datetime import date, datetime, timedelta, timezone

# 删除第 23-26 行的 _today() 函数

# 在第 12 行后添加:
from app.parent.service import datetime_range_shanghai, today_shanghai
```

然后将第 48 行的 `today = _today()` 改为 `today = today_shanghai()`，第 62-63 行的日期范围计算改为：

```python
today_start, tomorrow_start = datetime_range_shanghai(today)
```

删除原来第 62-63 行：
```python
# 删除:
# today_start = datetime(today.year, today.month, today.day, tzinfo=timezone(timedelta(hours=8)))
# tomorrow_start = today_start + timedelta(days=1)
```

- [ ] **Step 3: 验证导入正确**

```bash
cd cloud/backend && python -c "from app.parent.service import today_shanghai, datetime_range_shanghai; d = today_shanghai(); print('Today (Shanghai):', d); s, e = datetime_range_shanghai(d); print('Range:', s, '->', e)"
```

Expected: print today's date and range with `+08:00` timezone.

---

### Task 3: 学习目标模块 — `app/parent/goal/`

**Files:**
- Create: `cloud/backend/app/parent/goal/__init__.py`
- Create: `cloud/backend/app/parent/goal/schemas.py`
- Create: `cloud/backend/app/parent/goal/service.py`
- Create: `cloud/backend/app/parent/goal/router.py`

**Interfaces:**
- Consumes: `app.parent.service.verify_parent_access`
- Consumes: `app.models.config.LearningGoal`
- Produces: `goal_router` (APIRouter, prefix="/children", tags=["parent-goal"])
- Produces: `GET /{child_id}/learning/goal` → `LearningGoalOut`
- Produces: `PUT /{child_id}/learning/goal` → `LearningGoalOut`

- [ ] **Step 1: 创建 `__init__.py`**

```bash
# Create empty file
```

`cloud/backend/app/parent/goal/__init__.py` — 空文件。

- [ ] **Step 2: 创建 schemas.py**

创建 `cloud/backend/app/parent/goal/schemas.py`：

```python
"""Parent learning goal schemas — aligned with parent-openapi.yaml."""

from pydantic import BaseModel, Field

VALID_MODULES = {"science", "math", "english", "poems", "music", "quiz"}
MODULE_LABELS = {
    "science": "科学探秘",
    "math": "数学思维",
    "english": "英语角",
    "poems": "诗词歌赋",
    "music": "音乐乐园",
    "quiz": "趣味问答",
}


class LearningGoalModule(BaseModel):
    """Per-module goal minutes."""
    module: str
    module_label: str = ""
    goal_minutes: int = 0


class LearningGoalOut(BaseModel):
    """GET / PUT response for learning goal."""
    daily_goal_minutes: int = 30
    modules: list[LearningGoalModule] = []


class UpdateLearningGoalRequest(BaseModel):
    """PUT request body for updating learning goal."""
    daily_goal_minutes: int = Field(..., ge=0)
    modules: list[LearningGoalModule] = Field(default_factory=list)
```

- [ ] **Step 3: 创建 service.py**

创建 `cloud/backend/app/parent/goal/service.py`：

```python
"""Parent learning goal business logic."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.config import LearningGoal
from app.parent.goal.schemas import MODULE_LABELS, VALID_MODULES
from app.parent.service import verify_parent_access


async def get_learning_goal(
    db: AsyncSession, parent_id: str, child_id: str,
) -> dict | None:
    """Get learning goal for a child. Returns defaults if not set."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    result = await db.execute(
        select(LearningGoal).where(LearningGoal.child_id == child_id)
    )
    goal = result.scalar_one_or_none()

    if goal is None:
        return _default_goal()

    return _goal_to_dict(goal)


async def upsert_learning_goal(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    daily_goal_minutes: int,
    modules: list[dict],
) -> dict | None:
    """Create or update learning goal for a child.

    Raises ValueError if any module name is invalid.
    """
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    # Validate modules
    for m in modules:
        mod_name = m.get("module", "")
        if mod_name not in VALID_MODULES:
            raise ValueError(f"invalid_module: {mod_name}")

    module_goals = [
        {"module": m["module"], "goal_minutes": m.get("goal_minutes", 0)}
        for m in modules
    ]

    stmt = pg_insert(LearningGoal).values(
        child_id=child_id,
        daily_goal_minutes=daily_goal_minutes,
        module_goals=module_goals,
    ).on_conflict_do_update(
        index_elements=["child_id"],
        set_={
            "daily_goal_minutes": daily_goal_minutes,
            "module_goals": module_goals,
        },
    ).returning(LearningGoal)

    result = await db.execute(stmt)
    goal = result.scalar_one()
    await db.flush()

    return _goal_to_dict(goal)


def _goal_to_dict(goal: LearningGoal) -> dict:
    """Convert a LearningGoal ORM object to response dict."""
    raw_modules = goal.module_goals if isinstance(goal.module_goals, list) else []
    modules = []
    for m in raw_modules:
        mod_name = m.get("module", "")
        modules.append({
            "module": mod_name,
            "module_label": MODULE_LABELS.get(mod_name, mod_name),
            "goal_minutes": m.get("goal_minutes", 0),
        })
    return {
        "daily_goal_minutes": goal.daily_goal_minutes,
        "modules": modules,
    }


def _default_goal() -> dict:
    """Return default goal (30 min total, empty per-module)."""
    return {
        "daily_goal_minutes": 30,
        "modules": [],
    }
```

- [ ] **Step 4: 创建 router.py**

创建 `cloud/backend/app/parent/goal/router.py`：

```python
"""Parent learning goal routes — GET/PUT daily learning goal."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.db import get_db
from app.parent.goal.schemas import LearningGoalOut, UpdateLearningGoalRequest
from app.parent.goal.service import get_learning_goal, upsert_learning_goal
from app.schemas.common import error, ok

goal_router = APIRouter(prefix="/children", tags=["parent-goal"])


@goal_router.get("/{child_id}/learning/goal")
async def get_goal(
    child_id: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get daily learning goal for a child."""
    try:
        data = await get_learning_goal(db, parent_id, child_id)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok(LearningGoalOut(**data).model_dump())


@goal_router.put("/{child_id}/learning/goal")
async def update_goal(
    child_id: str,
    body: UpdateLearningGoalRequest,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Update daily learning goal for a child."""
    modules_data = [
        {"module": m.module, "goal_minutes": m.goal_minutes}
        for m in body.modules
    ]

    try:
        data = await upsert_learning_goal(
            db, parent_id, child_id, body.daily_goal_minutes, modules_data,
        )
        await db.commit()
    except ValueError as e:
        await db.rollback()
        msg = str(e)
        if msg.startswith("invalid_module"):
            return JSONResponse(status_code=400, content=error(400, msg))
        return JSONResponse(status_code=400, content=error(400, msg))
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok(LearningGoalOut(**data).model_dump())
```

- [ ] **Step 5: 验证模块导入**

```bash
cd cloud/backend && python -c "from app.parent.goal.router import goal_router; print('goal_router prefix:', goal_router.prefix)"
```

Expected: `goal_router prefix: /children`

---

### Task 4: 派发任务 + 今日任务模块 — `app/parent/dispatch/`

**Files:**
- Create: `cloud/backend/app/parent/dispatch/__init__.py`
- Create: `cloud/backend/app/parent/dispatch/schemas.py`
- Create: `cloud/backend/app/parent/dispatch/service.py`
- Create: `cloud/backend/app/parent/dispatch/router.py`

**Interfaces:**
- Consumes: `app.parent.service.verify_parent_access`, `today_shanghai`, `datetime_range_shanghai`
- Consumes: `app.models.task.DailyTask`
- Produces: `dispatch_router` (APIRouter, prefix="/children", tags=["parent-dispatch"])
- Produces: `GET /{child_id}/today-tasks`, `GET /{child_id}/today-tasks/{task_id}`
- Produces: `GET /{child_id}/dispatched-tasks`, `POST /{child_id}/dispatched-tasks`

- [ ] **Step 1: 创建 `__init__.py`**

`cloud/backend/app/parent/dispatch/__init__.py` — 空文件。

- [ ] **Step 2: 创建 schemas.py**

创建 `cloud/backend/app/parent/dispatch/schemas.py`：

```python
"""Parent dispatch schemas — aligned with parent-openapi.yaml."""

from datetime import datetime

from pydantic import BaseModel, Field

MODULE_LABELS = {
    "science": "科学探秘", "math": "数学思维",
    "english": "英语角", "poems": "诗词歌赋",
    "music": "音乐乐园", "quiz": "趣味问答",
}
VALID_TASK_CATEGORIES = {"learning", "lifestyle", "sports", "custom"}
VALID_MODULES = {"science", "math", "english", "poems", "music", "quiz"}


class TaskProgress(BaseModel):
    completed_count: int = 0
    total_count: int = 0
    accuracy: float | None = None
    correct_count: int | None = None
    wrong_count: int | None = None
    is_final: bool | None = None


class TodayTaskOut(BaseModel):
    task_id: str
    task_category: str
    module: str | None = None
    module_label: str | None = None
    status: str
    title: str
    progress: TaskProgress
    expires_at: datetime | None = None


class DispatchTaskItem(BaseModel):
    task_category: str = Field(..., pattern=r"^(learning|lifestyle|sports|custom)$")
    module: str | None = None
    title: str = Field(..., min_length=1)


class DispatchTasksRequest(BaseModel):
    tasks: list[DispatchTaskItem] = Field(..., min_length=1)
```

- [ ] **Step 3: 创建 service.py**

创建 `cloud/backend/app/parent/dispatch/service.py`：

```python
"""Parent dispatch business logic — today-tasks view + dispatched tasks."""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import DailyTask
from app.parent.dispatch.schemas import MODULE_LABELS
from app.parent.service import (
    datetime_range_shanghai,
    today_shanghai,
    verify_parent_access,
)


async def get_today_tasks(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    business_date: date | None = None,
) -> list[dict] | None:
    """Get today's learning tasks (module IS NOT NULL) for a child.

    Returns None if parent has no access to child.
    """
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    bdate = business_date or today_shanghai()

    result = await db.execute(
        select(DailyTask)
        .where(
            DailyTask.child_id == child_id,
            DailyTask.business_date == bdate,
            DailyTask.module.isnot(None),
        )
        .order_by(DailyTask.created_at.desc())
    )
    tasks = result.scalars().all()
    return [_task_to_dict(t) for t in tasks]


async def get_task_detail(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    task_id: str,
) -> dict | None:
    """Get a single task detail by ID. Only returns learning tasks."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        return None

    result = await db.execute(
        select(DailyTask).where(
            DailyTask.id == task_uuid,
            DailyTask.child_id == child_id,
            DailyTask.module.isnot(None),
        )
    )
    task = result.scalar_one_or_none()
    if task is None:
        return None
    return _task_to_dict(task)


async def get_dispatched_tasks(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    business_date: date | None = None,
) -> list[dict] | None:
    """Get dispatched (non-learning) tasks for a child."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    bdate = business_date or today_shanghai()

    result = await db.execute(
        select(DailyTask)
        .where(
            DailyTask.child_id == child_id,
            DailyTask.business_date == bdate,
            DailyTask.task_category.in_(["lifestyle", "sports", "custom"]),
        )
        .order_by(DailyTask.created_at.desc())
    )
    tasks = result.scalars().all()
    return [_task_to_dict(t) for t in tasks]


async def create_dispatched_tasks(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    tasks: list[dict],
) -> list[dict] | None:
    """Create dispatched (non-learning) tasks for a child.

    Each task dict: {task_category, title, module?}
    """
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    today = today_shanghai()
    today_start, _ = datetime_range_shanghai(today)
    from datetime import timedelta

    expires_at = today_start.replace(hour=23, minute=59, second=59)

    created = []
    for t in tasks:
        module = t.get("module") if t.get("task_category") == "learning" else None
        task = DailyTask(
            child_id=child_id,
            business_date=today,
            module=module,
            task_category=t.get("task_category", "custom"),
            title=t["title"],
            status="assigned",
            progress_total=1,
            expires_at=expires_at,
        )
        db.add(task)
        created.append(task)

    await db.flush()
    return [_task_to_dict(t) for t in created]


def _task_to_dict(t: DailyTask) -> dict:
    return {
        "task_id": str(t.id),
        "task_category": t.task_category,
        "module": t.module,
        "module_label": MODULE_LABELS.get(t.module, "") if t.module else None,
        "status": t.status,
        "title": t.title,
        "progress": {
            "completed_count": t.progress_completed,
            "total_count": t.progress_total,
            "accuracy": None,
            "correct_count": None,
            "wrong_count": None,
            "is_final": t.status in ("completed", "expired"),
        },
        "expires_at": t.expires_at.isoformat() if t.expires_at else None,
    }
```

- [ ] **Step 4: 创建 router.py**

创建 `cloud/backend/app/parent/dispatch/router.py`：

```python
"""Parent dispatch routes — today tasks list/detail, dispatched tasks."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.db import get_db
from app.parent.dispatch.schemas import (
    DispatchTasksRequest,
    TodayTaskOut,
)
from app.parent.dispatch.service import (
    create_dispatched_tasks,
    get_dispatched_tasks,
    get_task_detail,
    get_today_tasks,
)
from app.schemas.common import error, ok

dispatch_router = APIRouter(prefix="/children", tags=["parent-dispatch"])


@dispatch_router.get("/{child_id}/today-tasks")
async def list_today_tasks(
    child_id: str,
    date_param: date | None = Query(default=None, alias="date"),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get today's learning tasks for a child."""
    try:
        items = await get_today_tasks(db, parent_id, child_id, business_date=date_param)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if items is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok([TodayTaskOut(**item).model_dump() for item in items])


@dispatch_router.get("/{child_id}/today-tasks/{task_id}")
async def get_today_task_detail(
    child_id: str,
    task_id: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get a single task detail."""
    try:
        item = await get_task_detail(db, parent_id, child_id, task_id)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if item is None:
        return JSONResponse(status_code=404, content=error(404, "task_not_found"))

    return ok(TodayTaskOut(**item).model_dump())


@dispatch_router.get("/{child_id}/dispatched-tasks")
async def list_dispatched_tasks(
    child_id: str,
    date_param: date | None = Query(default=None, alias="date"),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get dispatched (non-learning) tasks for a child."""
    try:
        items = await get_dispatched_tasks(db, parent_id, child_id, business_date=date_param)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if items is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok([TodayTaskOut(**item).model_dump() for item in items])


@dispatch_router.post("/{child_id}/dispatched-tasks")
async def create_dispatched_tasks_endpoint(
    child_id: str,
    body: DispatchTasksRequest,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Create dispatched tasks for a child."""
    tasks_data = [
        {"task_category": t.task_category, "module": t.module, "title": t.title}
        for t in body.tasks
    ]

    try:
        items = await create_dispatched_tasks(db, parent_id, child_id, tasks_data)
        await db.commit()
    except ValueError as e:
        await db.rollback()
        return JSONResponse(status_code=400, content=error(400, str(e)))
    except Exception:
        await db.rollback()
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if items is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok([TodayTaskOut(**item).model_dump() for item in items])
```

- [ ] **Step 5: 验证模块导入**

```bash
cd cloud/backend && python -c "from app.parent.dispatch.router import dispatch_router; print('dispatch_router prefix:', dispatch_router.prefix); print('routes:', [r.path for r in dispatch_router.routes])"
```

---

### Task 5: 学习报告模块 — `app/parent/reports/`

**Files:**
- Create: `cloud/backend/app/parent/reports/__init__.py`
- Create: `cloud/backend/app/parent/reports/schemas.py`
- Create: `cloud/backend/app/parent/reports/service.py`
- Create: `cloud/backend/app/parent/reports/router.py`

**Interfaces:**
- Consumes: `app.parent.service.verify_parent_access`, `today_shanghai`, `datetime_range_shanghai`
- Consumes: `app.models.task.DailyTask`, `app.models.learning.LearningSession`, `app.models.answer.AnswerRecord`, `app.models.answer.WrongAnswer`
- Produces: `reports_router` (APIRouter, prefix="/children", tags=["parent-reports"])
- Produces: 6 GET endpoints for progress, sessions, session detail, wrong-answers, weekly list, weekly detail

- [ ] **Step 1: 创建 `__init__.py`**

`cloud/backend/app/parent/reports/__init__.py` — 空文件。

- [ ] **Step 2: 创建 schemas.py**

创建 `cloud/backend/app/parent/reports/schemas.py`：

```python
"""Parent reports schemas — aligned with parent-openapi.yaml."""

from datetime import date, datetime

from pydantic import BaseModel


# --- Learning Progress ---

class ModuleProgressSummary(BaseModel):
    module: str
    module_label: str
    completed_tasks: int = 0
    total_tasks: int = 0
    accuracy: float | None = None
    total_correct: int = 0
    total_wrong: int = 0


class LearningProgressOut(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    modules: list[ModuleProgressSummary] = []
    overall_completed: int = 0
    overall_total: int = 0
    overall_accuracy: float | None = None
    overall_correct: int = 0
    overall_wrong: int = 0


# --- Session ---

class SessionSummary(BaseModel):
    completed_count: int = 0
    total_count: int = 0
    accuracy: float | None = None
    correct_count: int | None = None
    wrong_count: int | None = None
    total_active_duration_ms: int = 0


class LearningSessionOut(BaseModel):
    session_id: str
    module: str
    module_label: str
    source: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None
    summary: SessionSummary


class Pagination(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedSessions(BaseModel):
    items: list[LearningSessionOut]
    pagination: Pagination


# --- Wrong Answer ---

class Option(BaseModel):
    option_id: str
    text: str


class QuestionSnapshot(BaseModel):
    question_id: str
    question: str
    options: list[Option]
    correct_option_id: str


class WrongAnswerOut(BaseModel):
    wrong_answer_id: str
    module: str
    module_label: str
    question_snapshot: QuestionSnapshot | None = None
    selected_option_id: str
    first_wrong_at: datetime
    last_wrong_at: datetime
    wrong_count: int


class PaginatedWrongAnswers(BaseModel):
    items: list[WrongAnswerOut]
    pagination: Pagination


# --- Weekly Report ---

class WeeklyReportLearningSummary(BaseModel):
    total_active_duration_minutes: int = 0
    completed_tasks: int = 0
    total_tasks: int = 0
    average_accuracy: float | None = None
    modules_touched: list[str] = []


class WeeklyReportSummary(BaseModel):
    focus_score: int = 0
    focus_change_percent: int = 0
    posture_score: int = 0
    posture_change_percent: int = 0
    anomaly_count: int = 0
    discovery_count: int = 0


class DailyScorePoint(BaseModel):
    date: date
    score: int


class WeeklyScorePoint(BaseModel):
    week_key: str
    score: int


class BehaviorInsightTag(BaseModel):
    text: str
    cls: str


class AnomalyItem(BaseModel):
    title: str
    description: str
    tags: list[BehaviorInsightTag] = []


class DiscoveryItem(BaseModel):
    title: str
    description: str
    color: str


class WeeklyReportOut(BaseModel):
    week_key: str
    label: str
    start_date: date
    end_date: date
    learning_summary: WeeklyReportLearningSummary
    behavior_summary: WeeklyReportSummary
    focus_daily_series: list[DailyScorePoint] = []
    posture_weekly_series: list[WeeklyScorePoint] = []
    anomalies: list[AnomalyItem] = []
    discoveries: list[DiscoveryItem] = []
    ai_summary: str = ""


class WeeklyReportListItem(BaseModel):
    week_key: str
    label: str
    start_date: date
    end_date: date
```

- [ ] **Step 3: 创建 service.py**

创建 `cloud/backend/app/parent/reports/service.py`：

```python
"""Parent reports business logic — progress, sessions, wrong-answers, weekly."""

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.answer import AnswerRecord, WrongAnswer
from app.models.learning import LearningSession
from app.models.task import DailyTask
from app.parent.service import datetime_range_shanghai, verify_parent_access

MODULE_LABELS = {
    "science": "科学探秘", "math": "数学思维",
    "english": "英语角", "poems": "诗词歌赋",
    "music": "音乐乐园", "quiz": "趣味问答",
}
SHANGHAI_TZ = timezone(timedelta(hours=8))


# --- Learning Progress ---

async def get_learning_progress(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict | None:
    """Aggregate learning progress per module and overall."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=6)

    # Aggregate tasks per module
    task_result = await db.execute(
        select(
            DailyTask.module,
            func.count().label("total"),
            func.count().filter(DailyTask.status == "completed").label("completed"),
        )
        .where(
            DailyTask.child_id == child_id,
            DailyTask.module.isnot(None),
            DailyTask.business_date.between(start_date, end_date),
        )
        .group_by(DailyTask.module)
    )
    task_rows = task_result.all()

    # Aggregate answers per module for accuracy
    start_dt, end_dt_excl = datetime_range_shanghai(start_date)
    _, end_dt_end = datetime_range_shanghai(end_date)
    end_dt = end_dt_end  # inclusive end

    answer_result = await db.execute(
        select(
            AnswerRecord.module,
            func.count().label("total"),
            func.count().filter(AnswerRecord.is_correct == True).label("correct"),
        )
        .where(
            AnswerRecord.child_id == child_id,
            AnswerRecord.answered_at >= start_dt,
            AnswerRecord.answered_at < end_dt + timedelta(days=1),
        )
        .group_by(AnswerRecord.module)
    )
    answer_rows = {r.module: (r.total, r.correct) for r in answer_result.all()}

    modules = []
    overall_completed = 0
    overall_total = 0
    overall_correct = 0
    overall_wrong = 0

    for mod, total, completed in task_rows:
        ans_total, ans_correct = answer_rows.get(mod, (0, 0))
        accuracy = round(ans_correct / ans_total, 4) if ans_total > 0 else None
        modules.append({
            "module": mod,
            "module_label": MODULE_LABELS.get(mod, mod),
            "completed_tasks": completed or 0,
            "total_tasks": total or 0,
            "accuracy": accuracy,
            "total_correct": ans_correct,
            "total_wrong": ans_total - ans_correct,
        })
        overall_completed += completed or 0
        overall_total += total or 0
        overall_correct += ans_correct
        overall_wrong += ans_total - ans_correct

    overall_ans_total = overall_correct + overall_wrong
    overall_accuracy = (
        round(overall_correct / overall_ans_total, 4)
        if overall_ans_total > 0 else None
    )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "modules": modules,
        "overall_completed": overall_completed,
        "overall_total": overall_total,
        "overall_accuracy": overall_accuracy,
        "overall_correct": overall_correct,
        "overall_wrong": overall_wrong,
    }


# --- Learning Sessions ---

async def get_sessions(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    module: str | None = None,
    status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict | None:
    """Paginated list of learning sessions with answer summaries."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    # Build query
    query = (
        select(LearningSession)
        .where(LearningSession.child_id == child_id)
    )

    if module:
        query = query.where(LearningSession.module == module)
    if status:
        query = query.where(LearningSession.status == status)
    if start_date:
        s_dt, _ = datetime_range_shanghai(start_date)
        query = query.where(LearningSession.created_at >= s_dt)
    if end_date:
        _, e_dt = datetime_range_shanghai(end_date)
        query = query.where(LearningSession.created_at < e_dt)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.order_by(LearningSession.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    sessions = result.scalars().all()

    items = []
    for s in sessions:
        summary = await _get_session_summary(db, s.id)
        items.append({
            "session_id": str(s.id),
            "module": s.module,
            "module_label": MODULE_LABELS.get(s.module, s.module),
            "source": s.source,
            "status": s.status,
            "created_at": s.created_at,
            "completed_at": s.updated_at if s.status == "completed" else None,
            "summary": summary,
        })

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        },
    }


async def get_session_detail(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    session_id: str,
) -> dict | None:
    """Get a single learning session with answer summary."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    try:
        sid_uuid = uuid.UUID(session_id)
    except ValueError:
        return None

    result = await db.execute(
        select(LearningSession).where(
            LearningSession.id == sid_uuid,
            LearningSession.child_id == child_id,
        )
    )
    s = result.scalar_one_or_none()
    if s is None:
        return None

    summary = await _get_session_summary(db, s.id)

    return {
        "session_id": str(s.id),
        "module": s.module,
        "module_label": MODULE_LABELS.get(s.module, s.module),
        "source": s.source,
        "status": s.status,
        "created_at": s.created_at,
        "completed_at": s.updated_at if s.status == "completed" else None,
        "summary": summary,
    }


async def _get_session_summary(db: AsyncSession, session_id: uuid.UUID) -> dict:
    """Aggregate answer records for a session into a summary."""
    result = await db.execute(
        select(
            func.count().label("total"),
            func.count().filter(AnswerRecord.is_correct == True).label("correct"),
        )
        .where(AnswerRecord.session_id == session_id)
    )
    row = result.one()
    total = row.total or 0
    correct = row.correct or 0
    wrong = total - correct
    accuracy = round(correct / total, 4) if total > 0 else None

    return {
        "completed_count": correct,
        "total_count": total,
        "accuracy": accuracy,
        "correct_count": correct,
        "wrong_count": wrong,
        "total_active_duration_ms": 0,
    }


# --- Wrong Answers ---

async def get_wrong_answers(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    module: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict | None:
    """Paginated list of wrong answers."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    query = (
        select(WrongAnswer)
        .where(WrongAnswer.child_id == child_id)
    )
    if module:
        query = query.where(WrongAnswer.module == module)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.order_by(WrongAnswer.last_wrong_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    rows = result.scalars().all()

    items = []
    for r in rows:
        qs = r.question_snapshot if isinstance(r.question_snapshot, dict) else {}
        items.append({
            "wrong_answer_id": str(r.id),
            "module": r.module,
            "module_label": MODULE_LABELS.get(r.module, r.module),
            "question_snapshot": qs if qs else None,
            "selected_option_id": r.selected_option_id,
            "first_wrong_at": r.first_wrong_at,
            "last_wrong_at": r.last_wrong_at,
            "wrong_count": r.wrong_count,
        })

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        },
    }


# --- Weekly Report ---

def _week_boundaries(week_key: str) -> tuple[date, date]:
    """Parse a week_key (Monday's date) and return (monday, sunday)."""
    monday = date.fromisoformat(week_key)
    sunday = monday + timedelta(days=6)
    return monday, sunday


def _recent_week_keys(count: int = 8) -> list[dict]:
    """Return the last `count` week keys ending at the current week."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    keys = []
    for i in range(count):
        wk = monday - timedelta(weeks=i)
        keys.append({
            "week_key": wk.isoformat(),
            "label": f"{wk} ~ {wk + timedelta(days=6)}",
            "start_date": wk,
            "end_date": wk + timedelta(days=6),
        })
    return keys


async def get_weekly_report_list(
    db: AsyncSession, parent_id: str, child_id: str,
) -> list[dict] | None:
    """Return last 8 week keys without detailed data."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None
    return _recent_week_keys(8)


async def get_weekly_report_detail(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    week_key: str,
) -> dict | None:
    """Build a weekly report for the given week_key (Monday's date)."""
    if not await verify_parent_access(db, parent_id, child_id):
        return None

    try:
        monday, sunday = _week_boundaries(week_key)
    except ValueError:
        return None

    return await _build_weekly_report(db, child_id, week_key, monday, sunday)


async def _build_weekly_report(
    db: AsyncSession, child_id: str, week_key: str, monday: date, sunday: date,
) -> dict:
    """Aggregate learning data for a week and return a WeeklyReport dict."""

    # Tasks completed in this week
    task_result = await db.execute(
        select(
            func.count().label("total"),
            func.count().filter(DailyTask.status == "completed").label("completed"),
        )
        .where(
            DailyTask.child_id == child_id,
            DailyTask.module.isnot(None),
            DailyTask.business_date.between(monday, sunday),
        )
    )
    task_row = task_result.one()

    # Modules touched
    mod_result = await db.execute(
        select(DailyTask.module)
        .where(
            DailyTask.child_id == child_id,
            DailyTask.module.isnot(None),
            DailyTask.business_date.between(monday, sunday),
        )
        .distinct()
    )
    modules_touched = [r[0] for r in mod_result.all()]

    # Answers accuracy this week
    monday_dt, _ = datetime_range_shanghai(monday)
    _, sunday_dt = datetime_range_shanghai(sunday)
    answer_end = sunday_dt + timedelta(days=1)

    ans_result = await db.execute(
        select(
            func.count().label("total"),
            func.count().filter(AnswerRecord.is_correct == True).label("correct"),
        )
        .where(
            AnswerRecord.child_id == child_id,
            AnswerRecord.answered_at >= monday_dt,
            AnswerRecord.answered_at < answer_end,
        )
    )
    ans_row = ans_result.one()
    ans_total = ans_row.total or 0
    ans_correct = ans_row.correct or 0
    avg_accuracy = round(ans_correct / ans_total, 4) if ans_total > 0 else None

    label = f"{monday} ~ {sunday}"

    return {
        "week_key": week_key,
        "label": label,
        "start_date": monday,
        "end_date": sunday,
        "learning_summary": {
            "total_active_duration_minutes": 0,
            "completed_tasks": task_row.completed or 0,
            "total_tasks": task_row.total or 0,
            "average_accuracy": avg_accuracy,
            "modules_touched": modules_touched,
        },
        "behavior_summary": {
            "focus_score": 0, "focus_change_percent": 0,
            "posture_score": 0, "posture_change_percent": 0,
            "anomaly_count": 0, "discovery_count": 0,
        },
        "focus_daily_series": [],
        "posture_weekly_series": [],
        "anomalies": [],
        "discoveries": [],
        "ai_summary": "",
    }
```

- [ ] **Step 4: 创建 router.py**

创建 `cloud/backend/app/parent/reports/router.py`：

```python
"""Parent reports routes — progress, sessions, wrong-answers, weekly."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.db import get_db
from app.parent.reports.schemas import (
    LearningProgressOut,
    LearningSessionOut,
    PaginatedSessions,
    PaginatedWrongAnswers,
    WeeklyReportListItem,
    WeeklyReportOut,
    WrongAnswerOut,
)
from app.parent.reports.service import (
    get_learning_progress,
    get_session_detail,
    get_sessions,
    get_weekly_report_detail,
    get_weekly_report_list,
    get_wrong_answers,
)
from app.schemas.common import error, ok

reports_router = APIRouter(prefix="/children", tags=["parent-reports"])


# --- Learning Progress ---

@reports_router.get("/{child_id}/learning/progress")
async def learning_progress(
    child_id: str,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get learning progress overview for a child."""
    try:
        data = await get_learning_progress(
            db, parent_id, child_id, start_date, end_date,
        )
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok(LearningProgressOut(**data).model_dump())


# --- Learning Sessions ---

@reports_router.get("/{child_id}/learning/sessions")
async def list_sessions(
    child_id: str,
    module: str | None = Query(default=None),
    status: str | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated learning sessions for a child."""
    try:
        data = await get_sessions(
            db, parent_id, child_id,
            module=module, status=status,
            start_date=start_date, end_date=end_date,
            page=page, page_size=page_size,
        )
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok(PaginatedSessions(
        items=[LearningSessionOut(**item) for item in data["items"]],
        pagination=data["pagination"],
    ).model_dump())


@reports_router.get("/{child_id}/learning/sessions/{session_id}")
async def session_detail(
    child_id: str,
    session_id: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get a single learning session detail."""
    try:
        item = await get_session_detail(db, parent_id, child_id, session_id)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if item is None:
        return JSONResponse(status_code=404, content=error(404, "session_not_found"))

    return ok(LearningSessionOut(**item).model_dump())


# --- Wrong Answers ---

@reports_router.get("/{child_id}/learning/wrong-answers")
async def list_wrong_answers(
    child_id: str,
    module: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated wrong answers for a child."""
    try:
        data = await get_wrong_answers(
            db, parent_id, child_id,
            module=module, page=page, page_size=page_size,
        )
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok(PaginatedWrongAnswers(
        items=[WrongAnswerOut(**item) for item in data["items"]],
        pagination=data["pagination"],
    ).model_dump())


# --- Weekly Reports ---

@reports_router.get("/{child_id}/reports/weekly")
async def list_weekly_reports(
    child_id: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get list of recent weekly report keys."""
    try:
        items = await get_weekly_report_list(db, parent_id, child_id)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if items is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok([WeeklyReportListItem(**item).model_dump() for item in items])


@reports_router.get("/{child_id}/reports/weekly/{week_key}")
async def weekly_report_detail(
    child_id: str,
    week_key: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed weekly report for a specific week."""
    try:
        data = await get_weekly_report_detail(db, parent_id, child_id, week_key)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if data is None:
        return JSONResponse(status_code=404, content=error(404, "report_not_found"))

    return ok(WeeklyReportOut(**data).model_dump())
```

- [ ] **Step 5: 验证模块导入**

```bash
cd cloud/backend && python -c "from app.parent.reports.router import reports_router; print('reports_router prefix:', reports_router.prefix); print('routes:', [r.path for r in reports_router.routes])"
```

---

### Task 6: Router 注册 — 更新 `app/router.py`

**Files:**
- Modify: `cloud/backend/app/router.py`

**Interfaces:**
- Consumes: `goal_router`, `dispatch_router`, `reports_router`
- Produces: 3 个新 router 注册到 parent_router

- [ ] **Step 1: 在 app/router.py 中添加导入和注册**

修改 `cloud/backend/app/router.py`：

在现有 parent imports（第 9-13 行）后添加：

```python
from app.parent.goal.router import goal_router
from app.parent.dispatch.router import dispatch_router
from app.parent.reports.router import reports_router
```

在 `parent_router.include_router(dashboard_router)` 之后添加：

```python
parent_router.include_router(goal_router)
parent_router.include_router(dispatch_router)
parent_router.include_router(reports_router)
```

- [ ] **Step 2: 验证 router 注册正确**

```bash
cd cloud/backend && python -c "
from app.main import create_app
app = create_app()
routes = [r.path for r in app.routes if hasattr(r, 'path')]
for r in sorted(routes):
    if 'parent' in r and ('goal' in r or 'today-tasks' in r or 'dispatched' in r or 'progress' in r or 'sessions' in r or 'wrong' in r or 'weekly' in r):
        print(r)
"
```

Expected: 12 Phase 3 routes listed.

---

### Task 7: 车端防御性修复 — `car/task/service.py`

**Files:**
- Modify: `cloud/backend/app/car/task/service.py`

**Interfaces:**
- Modifies: `ensure_daily_tasks` — 查询加 `module IS NOT NULL` 过滤
- Modifies: `_task_to_dict` — `module` 为 None 时防御

- [ ] **Step 1: 修复 `ensure_daily_tasks` 查询**

在 `app/car/task/service.py` 的 `ensure_daily_tasks` 函数中，第 24 行后添加 `.where(DailyTask.module.isnot(None))`：

```python
# 修改前:
result = await db.execute(
    select(DailyTask).where(
        DailyTask.child_id == child_uuid,
        DailyTask.business_date == business_date,
    )
)

# 修改后:
result = await db.execute(
    select(DailyTask).where(
        DailyTask.child_id == child_uuid,
        DailyTask.business_date == business_date,
        DailyTask.module.isnot(None),
    )
)
```

- [ ] **Step 2: 修复 `_task_to_dict` 防御**

修改 `_task_to_dict` 第 111 行，将：

```python
"module_label": _mod_label(t.module),
```

改为：

```python
"module_label": _mod_label(t.module) if t.module else "",
```

- [ ] **Step 3: 验证**

```bash
cd cloud/backend && python -c "from app.car.task.service import ensure_daily_tasks, get_tasks; print('Car task service imports OK')"
```

---

### Task 8: 集成测试 — 目标模块

**Files:**
- Create: `cloud/backend/tests/test_parent_goal.py`

**Interfaces:**
- Consumes: `async_client`, `db_session` fixtures (from conftest)
- Tests: GET/PUT goal, 默认值, 无效 module, 未授权

- [ ] **Step 1: 创建 test_parent_goal.py**

创建 `cloud/backend/tests/test_parent_goal.py`：

```python
"""Integration tests for parent learning goal API."""

import pytest
from httpx import AsyncClient

from app.auth.security import create_parent_access_token
from app.models.child import Child
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild


@pytest.fixture
async def _goal_setup(db_session):
    """Create parent and child, return (token, child_id)."""
    parent = ParentAccount(wx_openid="test_goal", status="active")
    db_session.add(parent)
    await db_session.flush()

    family = Family(name="目标测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="目标孩子")
    db_session.add(child)
    await db_session.flush()

    pc = ParentChild(
        parent_id=parent.id, child_id=child.id, family_id=family.id,
        status="active", is_default=True,
    )
    db_session.add(pc)
    await db_session.commit()

    token = create_parent_access_token(parent_id=str(parent.id))
    return token, str(child.id)


@pytest.fixture
async def _goal_token(_goal_setup) -> str:
    return _goal_setup[0]


@pytest.fixture
async def _goal_child_id(_goal_setup) -> str:
    return _goal_setup[1]


@pytest.mark.asyncio
async def test_get_goal_default(
    async_client: AsyncClient, _goal_token: str, _goal_child_id: str,
):
    """GET goal returns defaults when not set."""
    res = await async_client.get(
        f"/v1/api/parent/children/{_goal_child_id}/learning/goal",
        headers={"Authorization": f"Bearer {_goal_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["daily_goal_minutes"] == 30
    assert body["data"]["modules"] == []


@pytest.mark.asyncio
async def test_put_and_get_goal(
    async_client: AsyncClient, _goal_token: str, _goal_child_id: str,
):
    """PUT goal then GET returns the updated goal."""
    res = await async_client.put(
        f"/v1/api/parent/children/{_goal_child_id}/learning/goal",
        headers={"Authorization": f"Bearer {_goal_token}"},
        json={
            "daily_goal_minutes": 45,
            "modules": [
                {"module": "math", "goal_minutes": 20},
                {"module": "english", "goal_minutes": 15},
            ],
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["daily_goal_minutes"] == 45
    assert len(body["data"]["modules"]) == 2

    # Verify GET returns same data
    res2 = await async_client.get(
        f"/v1/api/parent/children/{_goal_child_id}/learning/goal",
        headers={"Authorization": f"Bearer {_goal_token}"},
    )
    assert res2.status_code == 200
    body2 = res2.json()
    assert body2["data"]["daily_goal_minutes"] == 45


@pytest.mark.asyncio
async def test_put_goal_invalid_module(
    async_client: AsyncClient, _goal_token: str, _goal_child_id: str,
):
    """PUT goal with invalid module returns 400."""
    res = await async_client.put(
        f"/v1/api/parent/children/{_goal_child_id}/learning/goal",
        headers={"Authorization": f"Bearer {_goal_token}"},
        json={
            "daily_goal_minutes": 30,
            "modules": [{"module": "invalid_mod", "goal_minutes": 10}],
        },
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_goal_requires_auth(async_client: AsyncClient):
    """Goal endpoint requires parent JWT."""
    res = await async_client.get(
        "/v1/api/parent/children/some-id/learning/goal",
    )
    assert res.status_code == 401
```

- [ ] **Step 2: 运行测试验证**

```bash
cd cloud/backend && python -m pytest tests/test_parent_goal.py -v
```

Expected: 4 passed.

---

### Task 9: 集成测试 — 派发模块

**Files:**
- Create: `cloud/backend/tests/test_parent_dispatch.py`

**Interfaces:**
- Consumes: `async_client`, `db_session` fixtures
- Tests: today-tasks empty, today-tasks with data, task detail, dispatched-tasks CRUD, auth check

- [ ] **Step 1: 创建 test_parent_dispatch.py**

创建 `cloud/backend/tests/test_parent_dispatch.py`：

```python
"""Integration tests for parent dispatch API — today-tasks + dispatched."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.auth.security import create_parent_access_token
from app.models.child import Child
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild
from app.models.task import DailyTask


@pytest.fixture
async def _dispatch_setup(db_session):
    """Create parent, child. Return (token, child_id)."""
    parent = ParentAccount(wx_openid="test_dispatch", status="active")
    db_session.add(parent)
    await db_session.flush()

    family = Family(name="派发测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="派发孩子")
    db_session.add(child)
    await db_session.flush()

    pc = ParentChild(
        parent_id=parent.id, child_id=child.id, family_id=family.id,
        status="active", is_default=True,
    )
    db_session.add(pc)
    await db_session.commit()

    token = create_parent_access_token(parent_id=str(parent.id))
    return token, str(child.id)


@pytest.fixture
async def _dispatch_token(_dispatch_setup) -> str:
    return _dispatch_setup[0]


@pytest.fixture
async def _dispatch_child_id(_dispatch_setup) -> str:
    return _dispatch_setup[1]


@pytest.mark.asyncio
async def test_today_tasks_empty(
    async_client: AsyncClient, _dispatch_token: str, _dispatch_child_id: str,
):
    """GET today-tasks returns empty when no tasks exist."""
    res = await async_client.get(
        f"/v1/api/parent/children/{_dispatch_child_id}/today-tasks",
        headers={"Authorization": f"Bearer {_dispatch_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"] == []


@pytest.mark.asyncio
async def test_today_tasks_with_data(
    async_client: AsyncClient, _dispatch_token: str, _dispatch_child_id: str, db_session,
):
    """GET today-tasks returns learning tasks."""
    tz = timezone(timedelta(hours=8))
    today = datetime.now(tz).date()
    expires = datetime.now(tz) + timedelta(hours=23)

    task = DailyTask(
        child_id=_dispatch_child_id, business_date=today,
        module="math", task_category="learning",
        title="今日数学思维", status="assigned",
        progress_total=10, expires_at=expires,
    )
    db_session.add(task)
    await db_session.commit()

    res = await async_client.get(
        f"/v1/api/parent/children/{_dispatch_child_id}/today-tasks",
        headers={"Authorization": f"Bearer {_dispatch_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert len(body["data"]) == 1
    assert body["data"][0]["module"] == "math"


@pytest.mark.asyncio
async def test_today_task_detail(
    async_client: AsyncClient, _dispatch_token: str, _dispatch_child_id: str, db_session,
):
    """GET today-tasks/{id} returns task detail."""
    tz = timezone(timedelta(hours=8))
    today = datetime.now(tz).date()
    expires = datetime.now(tz) + timedelta(hours=23)

    task = DailyTask(
        child_id=_dispatch_child_id, business_date=today,
        module="science", task_category="learning",
        title="今日科学探秘", status="assigned",
        progress_total=5, expires_at=expires,
    )
    db_session.add(task)
    await db_session.commit()

    res = await async_client.get(
        f"/v1/api/parent/children/{_dispatch_child_id}/today-tasks/{task.id}",
        headers={"Authorization": f"Bearer {_dispatch_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["data"]["title"] == "今日科学探秘"


@pytest.mark.asyncio
async def test_dispatched_tasks_crud(
    async_client: AsyncClient, _dispatch_token: str, _dispatch_child_id: str,
):
    """POST and GET dispatched-tasks."""
    # Create dispatched tasks
    res = await async_client.post(
        f"/v1/api/parent/children/{_dispatch_child_id}/dispatched-tasks",
        headers={"Authorization": f"Bearer {_dispatch_token}"},
        json={
            "tasks": [
                {"task_category": "lifestyle", "title": "刷牙"},
                {"task_category": "sports", "title": "跳绳100下"},
            ],
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert len(body["data"]) == 2

    # Get dispatched tasks
    res2 = await async_client.get(
        f"/v1/api/parent/children/{_dispatch_child_id}/dispatched-tasks",
        headers={"Authorization": f"Bearer {_dispatch_token}"},
    )
    assert res2.status_code == 200
    body2 = res2.json()
    assert len(body2["data"]) == 2


@pytest.mark.asyncio
async def test_dispatched_tasks_excluded_from_today(
    async_client: AsyncClient, _dispatch_token: str, _dispatch_child_id: str,
):
    """Dispatched tasks are NOT returned in today-tasks."""
    # Create dispatched task
    await async_client.post(
        f"/v1/api/parent/children/{_dispatch_child_id}/dispatched-tasks",
        headers={"Authorization": f"Bearer {_dispatch_token}"},
        json={"tasks": [{"task_category": "lifestyle", "title": "整理书包"}]},
    )

    # today-tasks should not include it
    res = await async_client.get(
        f"/v1/api/parent/children/{_dispatch_child_id}/today-tasks",
        headers={"Authorization": f"Bearer {_dispatch_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert len(body["data"]) == 0  # no learning tasks created


@pytest.mark.asyncio
async def test_dispatch_requires_auth(async_client: AsyncClient):
    """Dispatch endpoints require parent JWT."""
    res = await async_client.get(
        "/v1/api/parent/children/some-id/dispatched-tasks",
    )
    assert res.status_code == 401
```

- [ ] **Step 2: 运行测试验证**

```bash
cd cloud/backend && python -m pytest tests/test_parent_dispatch.py -v
```

Expected: 6 passed.

---

### Task 10: 集成测试 — 报告模块

**Files:**
- Create: `cloud/backend/tests/test_parent_reports.py`

**Interfaces:**
- Consumes: `async_client`, `db_session` fixtures
- Tests: progress, sessions, session detail, wrong-answers, weekly list, weekly detail

- [ ] **Step 1: 创建 test_parent_reports.py**

创建 `cloud/backend/tests/test_parent_reports.py`：

```python
"""Integration tests for parent reports API — progress, sessions, wrong-answers, weekly."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.auth.security import create_parent_access_token
from app.models.answer import AnswerRecord, WrongAnswer
from app.models.child import Child
from app.models.family import Family
from app.models.learning import LearningSession
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild
from app.models.task import DailyTask


@pytest.fixture
async def _reports_setup(db_session):
    """Create parent, child. Return (token, child_id)."""
    parent = ParentAccount(wx_openid="test_reports", status="active")
    db_session.add(parent)
    await db_session.flush()

    family = Family(name="报告测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="报告孩子")
    db_session.add(child)
    await db_session.flush()

    pc = ParentChild(
        parent_id=parent.id, child_id=child.id, family_id=family.id,
        status="active", is_default=True,
    )
    db_session.add(pc)
    await db_session.commit()

    token = create_parent_access_token(parent_id=str(parent.id))
    return token, str(child.id)


@pytest.fixture
async def _reports_token(_reports_setup) -> str:
    return _reports_setup[0]


@pytest.fixture
async def _reports_child_id(_reports_setup) -> str:
    return _reports_setup[1]


@pytest.mark.asyncio
async def test_progress_empty(
    async_client: AsyncClient, _reports_token: str, _reports_child_id: str,
):
    """GET progress returns empty when no data."""
    res = await async_client.get(
        f"/v1/api/parent/children/{_reports_child_id}/learning/progress",
        headers={"Authorization": f"Bearer {_reports_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["modules"] == []
    assert body["data"]["overall_total"] == 0


@pytest.mark.asyncio
async def test_progress_with_data(
    async_client: AsyncClient, _reports_token: str, _reports_child_id: str, db_session,
):
    """GET progress returns aggregated stats when data exists."""
    tz = timezone(timedelta(hours=8))
    today = datetime.now(tz).date()
    expires = datetime.now(tz) + timedelta(hours=23)

    task = DailyTask(
        child_id=_reports_child_id, business_date=today,
        module="math", task_category="learning",
        title="今日数学", status="completed",
        progress_completed=10, progress_total=10, expires_at=expires,
    )
    db_session.add(task)
    await db_session.commit()

    res = await async_client.get(
        f"/v1/api/parent/children/{_reports_child_id}/learning/progress",
        headers={"Authorization": f"Bearer {_reports_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["overall_total"] >= 1


@pytest.mark.asyncio
async def test_sessions_empty(
    async_client: AsyncClient, _reports_token: str, _reports_child_id: str,
):
    """GET sessions returns empty pagination when no data."""
    res = await async_client.get(
        f"/v1/api/parent/children/{_reports_child_id}/learning/sessions",
        headers={"Authorization": f"Bearer {_reports_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["items"] == []
    assert body["data"]["pagination"]["total"] == 0


@pytest.mark.asyncio
async def test_sessions_with_data(
    async_client: AsyncClient, _reports_token: str, _reports_child_id: str, db_session,
):
    """GET sessions returns session list when data exists."""
    session = LearningSession(
        child_id=_reports_child_id, module="math",
        source="today_task", status="active",
    )
    db_session.add(session)
    await db_session.commit()

    res = await async_client.get(
        f"/v1/api/parent/children/{_reports_child_id}/learning/sessions",
        headers={"Authorization": f"Bearer {_reports_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert len(body["data"]["items"]) >= 1
    assert body["data"]["items"][0]["module"] == "math"


@pytest.mark.asyncio
async def test_session_detail(
    async_client: AsyncClient, _reports_token: str, _reports_child_id: str, db_session,
):
    """GET sessions/{id} returns session detail."""
    session = LearningSession(
        child_id=_reports_child_id, module="science",
        source="free_learning", status="completed",
    )
    db_session.add(session)
    await db_session.commit()

    res = await async_client.get(
        f"/v1/api/parent/children/{_reports_child_id}/learning/sessions/{session.id}",
        headers={"Authorization": f"Bearer {_reports_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["data"]["module"] == "science"
    assert body["data"]["source"] == "free_learning"


@pytest.mark.asyncio
async def test_wrong_answers_empty(
    async_client: AsyncClient, _reports_token: str, _reports_child_id: str,
):
    """GET wrong-answers returns empty pagination."""
    res = await async_client.get(
        f"/v1/api/parent/children/{_reports_child_id}/learning/wrong-answers",
        headers={"Authorization": f"Bearer {_reports_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["items"] == []


@pytest.mark.asyncio
async def test_weekly_list(
    async_client: AsyncClient, _reports_token: str, _reports_child_id: str,
):
    """GET weekly returns week key list."""
    res = await async_client.get(
        f"/v1/api/parent/children/{_reports_child_id}/reports/weekly",
        headers={"Authorization": f"Bearer {_reports_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert len(body["data"]) == 8  # 8 weeks


@pytest.mark.asyncio
async def test_weekly_detail_empty(
    async_client: AsyncClient, _reports_token: str, _reports_child_id: str,
):
    """GET weekly/{week_key} returns report with empty data."""
    # Use a recent Monday as week_key
    from datetime import date
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    week_key = monday.isoformat()

    res = await async_client.get(
        f"/v1/api/parent/children/{_reports_child_id}/reports/weekly/{week_key}",
        headers={"Authorization": f"Bearer {_reports_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["week_key"] == week_key
    assert body["data"]["learning_summary"]["completed_tasks"] == 0
    assert body["data"]["ai_summary"] == ""


@pytest.mark.asyncio
async def test_reports_require_auth(async_client: AsyncClient):
    """Reports endpoints require parent JWT."""
    res = await async_client.get(
        "/v1/api/parent/children/some-id/learning/progress",
    )
    assert res.status_code == 401
```

- [ ] **Step 2: 运行测试验证**

```bash
cd cloud/backend && python -m pytest tests/test_parent_reports.py -v
```

Expected: 10 passed.

---

### Task 11: 全量回归测试 + ruff 检查

**Files:**
- 无新建/修改

- [ ] **Step 1: 运行所有现有测试**

```bash
cd cloud/backend && python -m pytest tests/ -v
```

Expected: 46 existing + 20 new = **66 tests** all pass.

- [ ] **Step 2: 运行 ruff 检查**

```bash
cd cloud/backend && ruff check app/ tests/
```

Expected: 0 warnings.

- [ ] **Step 3: 运行 ruff format 检查**

```bash
cd cloud/backend && ruff format --check app/ tests/
```

Expected: "N files already formatted" or similar success message.

- [ ] **Step 4: 如果有 ruff issues，先 fix**

```bash
cd cloud/backend && ruff check --fix app/ tests/
```

- [ ] **Step 5: 提交所有更改**

```bash
git add -A
git status
git commit -m "feat: Phase 3 parent reports — goal, dispatch, reports (24 files, 12 endpoints, 20 tests)

- 3 new modules: goal/, dispatch/, reports/ (12 files)
- 1 new model: LearningGoal + 1 migration
- 1 migration: relax daily_task.module for dispatched tasks
- 2 shared utils: today_shanghai(), datetime_range_shanghai()
- 12 APIs across 3 modules
- 20 new integration tests (total 66)
- Car-side defensive fix: filter module IS NOT NULL

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 12: 更新进度文件

**Files:**
- Modify: `.superpowers/sdd/2026-07-29-backend-fullstack/progress.md`

- [ ] **Step 1: 添加 Phase 3 完成记录**

在 progress.md 末尾追加：

```markdown

## Phase 3: 学习报告与深度链路 (feature/parent-reports)

| 任务 | 状态 | 说明 |
|------|------|------|
| 3.1 学习目标 API | complete | GET/PUT /learning/goal |
| 3.2 今日任务+派发 API | complete | GET today-tasks, GET detail, GET/POST dispatched-tasks |
| 3.3 学习报告 API | complete | progress, sessions, wrong-answers, weekly |
| 3.4 车端防御性修复 | complete | car/task/service: filter+defend module=NULL |
| 3.5 集成测试+验证 | complete | 20 new tests, 66/66 pass, ruff clean |

### Phase 3 交付物
- 3 个业务模块（goal/dispatch/reports，12 个新文件）
- 1 个新模型 LearningGoal + 1 个迁移
- 1 个 DDL 迁移（daily_task 约束放宽）
- 12 个 API 路由
- 20 个集成测试
- 车端 2 处防御性修复

### 新端点列表
```
GET    /v1/api/parent/children/{child_id}/learning/goal
PUT    /v1/api/parent/children/{child_id}/learning/goal
GET    /v1/api/parent/children/{child_id}/today-tasks
GET    /v1/api/parent/children/{child_id}/today-tasks/{task_id}
GET    /v1/api/parent/children/{child_id}/dispatched-tasks
POST   /v1/api/parent/children/{child_id}/dispatched-tasks
GET    /v1/api/parent/children/{child_id}/learning/progress
GET    /v1/api/parent/children/{child_id}/learning/sessions
GET    /v1/api/parent/children/{child_id}/learning/sessions/{session_id}
GET    /v1/api/parent/children/{child_id}/learning/wrong-answers
GET    /v1/api/parent/children/{child_id}/reports/weekly
GET    /v1/api/parent/children/{child_id}/reports/weekly/{week_key}
```
```

- [ ] **Step 2: 提交进度文件**

```bash
git add .superpowers/sdd/2026-07-29-backend-fullstack/progress.md
git commit -m "docs: update progress with Phase 3 completion"
```

---

## Self-Review Checklist (for plan reviewer)

**1. Spec coverage:**
- ✅ Learning Goal GET/PUT → Task 3
- ✅ Today-tasks GET + detail → Task 4
- ✅ Dispatched tasks GET/POST → Task 4
- ✅ Learning progress → Task 5
- ✅ Learning sessions list + detail → Task 5
- ✅ Wrong answers → Task 5
- ✅ Weekly reports list + detail → Task 5
- ✅ LearningGoal model + migration → Task 1
- ✅ daily_task constraint relax + migration → Task 1
- ✅ Shared timezone utils → Task 2
- ✅ Car defensive fixes → Task 7
- ✅ tests/conftest.py import → Task 1 Step 2
- ✅ Progress schema → Task 5 schemas (LearningProgressOut)

**2. Placeholder scan:** No TBDs, TODOs, or vague directives. All code is concrete.

**3. Type consistency:**
- `today_shanghai()` returns `date` — used consistently in Task 3-5
- `verify_parent_access(db, parent_id, child_id)` signature consistent across all tasks
- `uuid.UUID` casts consistent with existing patterns
- Schema names match YAML: `LearningGoalOut`, `TodayTaskOut`, `LearningProgressOut`, etc.
- Router variable names: `goal_router`, `dispatch_router`, `reports_router` — match Task 6 imports
