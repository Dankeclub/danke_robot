# Phase 3：家长端学习报告与深度链路

> **状态**：设计中
> **日期**：2026-07-30
> **作者**：贝尔 / Doctor Bill
> **分支**：`feature/parent-reports`

## 一、背景与目标

### 背景

Phase 1（车端学习链路）和 Phase 2（家长端核心）已完成。家长可以查看孩子、管理设备、调整学习配置、查看今日大盘。但不具备：
- 设置每日学习目标的能力
- 派发自定义任务的能力
- 查看历史学习进度、会话记录、错题本、周报的能力

### 目标

新增 12 个家长端 API 端点，覆盖三个新模块：**学习目标**（goal）、**派发任务**（dispatch）、**学习报告**（reports）。

### 非目标

- 行为数据（专注度/坐姿/位置）— 数据表未建，返回 placeholder
- LLM 生成 AI 评语 — 异步任务基础设施未建，返回空字符串
- 消息下发、远程控制、通知、文件服务 — 后续 Phase

---

## 二、架构

### 目录结构

```
app/parent/
  goal/                   ← 新建
    __init__.py
    router.py
    schemas.py
    service.py
  dispatch/               ← 新建
    __init__.py
    router.py
    schemas.py
    service.py
  reports/                ← 新建
    __init__.py
    router.py
    schemas.py
    service.py
  service.py              ← 扩展：提取 _today() 时区工具
```

### Router 前缀

每个子 router 使用 `prefix="/children"`。完整路径由 `app/router.py` 拼装：

```python
parent_router = APIRouter(prefix="/v1/api/parent")
parent_router.include_router(goal_router)       # → /v1/api/parent/children/...
parent_router.include_router(dispatch_router)
parent_router.include_router(reports_router)
```

### 数据流

```
小程序                         后端                               DB
──────                        ────                               ──
PUT /learning/goal ────→ goal/service.py ────────────────→ learning_goal (upsert)
GET /today-tasks ────→ dispatch/service.py ──────────────→ daily_task
GET /dispatched-tasks → dispatch/service.py ──────────────→ daily_task
POST /dispatched-tasks → dispatch/service.py ─────────────→ daily_task (insert)
GET /learning/progress → reports/service.py ──────────────→ daily_task + learning_session + answer_record
GET /learning/sessions → reports/service.py ──────────────→ learning_session + answer_record
GET /wrong-answers ──→ reports/service.py ────────────────→ wrong_answer
GET /reports/weekly ─→ reports/service.py ────────────────→ 跨三表实时聚合
```

---

## 三、数据库变更

### 3.1 新增 `learning_goal` 表

每个孩子一行，存储每日学习时长目标和分模块目标。

| 列 | 类型 | 约束 | 默认值 |
|---|---|---|---|
| `id` | UUID | PK | gen_random_uuid() |
| `child_id` | UUID | FK → child, NOT NULL | |
| `daily_goal_minutes` | Integer | NOT NULL | 30 |
| `module_goals` | JSONB | NOT NULL | `'[]'` |
| `created_at` | TIMESTAMPTZ | NOT NULL | now() |
| `updated_at` | TIMESTAMPTZ | NOT NULL | now(), onupdate |

- UNIQUE: `(child_id)`
- INDEX: `idx_learning_goal_child (child_id)`

`module_goals` JSONB 格式：
```json
[{"module": "math", "goal_minutes": 20}, {"module": "english", "goal_minutes": 15}]
```

### 3.2 修改 `daily_task` 表

放宽 `module` 列约束以支持非学习类派发任务：

```sql
ALTER TABLE daily_task ALTER COLUMN module DROP NOT NULL;
ALTER TABLE daily_task DROP CONSTRAINT IF EXISTS ck_task_module;
ALTER TABLE daily_task ADD CONSTRAINT ck_task_module
    CHECK (module IS NULL OR module IN ('science','math','english','poems','music','quiz'));
```

PostgreSQL 中 NULL 值不触发 UNIQUE 冲突，所以 `(child_id, business_date, module)` 的唯一约束对 `module=NULL` 的行为正确 — 多个 NULL 行可以共存。

### 3.3 区分系统任务 vs 派发任务

不引入新列。用 `task_category` 区分：

| 来源 | task_category | module | 示例 title |
|------|-------------|--------|-----------|
| 系统生成 | `learning` | science/math/... | "今日科学探秘" |
| 家长派发 | `lifestyle` | nullable | "刷牙" |
| 家长派发 | `sports` | nullable | "跳绳 100 下" |
| 家长派发 | `custom` | nullable | 任意自定义 |

### 3.4 Python 模型

`LearningGoal` 放在 `app/models/config.py`（与 `LearningModuleConfig` 相邻，都是配置类）。

---

## 四、端点详细设计

### 4.1 学习目标 — `goal/`

#### GET `/{child_id}/learning/goal`

- 权限：`verify_parent_access`
- 逻辑：查 `learning_goal` WHERE child_id
- 不存在时返回默认值（daily_goal_minutes=30, modules=空数组，每个 module 默认 label）
- 响应：`ok(LearningGoalOut)`

#### PUT `/{child_id}/learning/goal`

- 权限：`verify_parent_access`
- 请求体：`UpdateLearningGoalRequest`
  - `daily_goal_minutes: int` (≥0)
  - `modules: list[{module, goal_minutes}]` — module 必须是 6 个内置值之一
- 逻辑：upsert（INSERT ON CONFLICT (child_id) DO UPDATE）
- body 不含 `module_label`，服务端填充
- 响应：`ok(LearningGoalOut)`

#### Schemas

```python
class LearningGoalModule(BaseModel):
    module: str
    module_label: str = ""
    goal_minutes: int = 0

class LearningGoalOut(BaseModel):
    daily_goal_minutes: int
    modules: list[LearningGoalModule]

class UpdateLearningGoalRequest(BaseModel):
    daily_goal_minutes: int
    modules: list[LearningGoalModule]  # module_label 忽略
```

---

### 4.2 今日任务 + 派发 — `dispatch/`

#### GET `/{child_id}/today-tasks`

- 参数：`?date=2026-07-30`（可选，默认今天）
- 权限：`verify_parent_access`
- 逻辑：查 `daily_task` WHERE child_id + business_date，按 created_at DESC 排序
- 返回 `list[TodayTask]`（复用 dashboard 的 TodayTask + TaskProgress schema）
- **必须过滤 `module IS NOT NULL`** — 排除家长派发任务（无 module）

#### GET `/{child_id}/today-tasks/{task_id}`

- 权限：`verify_parent_access`
- 逻辑：查 `daily_task` by id + child_id + `module IS NOT NULL`
- 返回 `TodayTask`

#### GET `/{child_id}/dispatched-tasks`

- 参数：`?date=2026-07-30`（可选，默认今天）
- 权限：`verify_parent_access`
- 逻辑：查 `daily_task` WHERE child_id + business_date + `task_category != 'learning'`（或 `task_category IN ('lifestyle','sports','custom')`）
- 返回 `list[TodayTask]`

#### POST `/{child_id}/dispatched-tasks`

- 权限：`verify_parent_access`
- 幂等：`Idempotency-Key` header
- 请求体：`DispatchTasksRequest`
  - `tasks: list[{task_category, module?, title}]`
  - module 仅在 task_category=learning 时必填
- 逻辑：逐条插入 `DailyTask`
  - `business_date = _today()`（Asia/Shanghai）
  - `status = "assigned"`
  - `expires_at = 当天 23:59:59 Asia/Shanghai`
  - `module = body.module` 或 None
- 响应：`ok([TodayTask, ...])`

---

### 4.3 学习报告 — `reports/`

#### GET `/{child_id}/learning/progress`

- 参数：`?start_date=...&end_date=...`（可选，默认最近 7 天）
- 权限：`verify_parent_access`
- 逻辑：聚合查询 daily_task + answer_record
  ```sql
  SELECT module,
         COUNT(*) FILTER (WHERE status='completed') AS completed,
         COUNT(*) AS total
  FROM daily_task
  WHERE child_id=$1 AND module IS NOT NULL AND business_date BETWEEN $2 AND $3
  GROUP BY module
  ```
- accuracy 从 answer_record 按 module 聚合（同一日期范围）
- 响应：`ok(LearningProgressOut)`

#### Schemas：LearningProgress

```python
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
```

#### GET `/{child_id}/learning/sessions`

- 参数：`?module=&status=&start_date=&end_date=&page=1&page_size=20`
- 权限：`verify_parent_access`
- 逻辑：分页查询 `learning_session`，对每个 session 聚合 answer_record 生成 summary
- summary：`completed_count, total_count, accuracy, correct_count, wrong_count, total_active_duration_ms`
- 响应：`PaginatedLearningSessions(items, pagination)`

#### GET `/{child_id}/learning/sessions/{session_id}`

- 权限：`verify_parent_access`
- 逻辑：单 session 查询 + answer_record 聚合
- 响应：`LearningSession`

#### GET `/{child_id}/learning/wrong-answers`

- 参数：`?module=&page=1&page_size=20`
- 权限：`verify_parent_access`
- 逻辑：分页查询 `wrong_answer`，按 `last_wrong_at DESC`
- 响应：`PaginatedWrongAnswers(items, pagination)`

#### GET `/{child_id}/reports/weekly`

- 权限：`verify_parent_access`
- 逻辑：返回最近 8 周的 week_key 列表，不计算详细数据
- week_key = 该周周一的日期（ISO 8601，如 `"2026-07-27"`）
- 响应：`[{week_key, label, start_date, end_date}, ...]`

#### GET `/{child_id}/reports/weekly/{week_key}`

- 权限：`verify_parent_access`
- 逻辑：实时聚合学习数据（DailyTask + LearningSession + AnswerRecord）
- **行为层返回默认值**（behavior_summary 全 0，daily_series 空数组，anomalies/discoveries 空数组）
- **ai_summary 返回 `""`**（LLM 管线未接入）
- 时区：Asia/Shanghai，week_key 解析为周一 00:00 → 周日 23:59:59
- 响应：`WeeklyReport`

#### WeeklyReport 字段说明

| 字段 | 数据来源 | Phase 3 行为 |
|------|---------|-------------|
| `learning_summary.total_active_duration_minutes` | Session 时间戳差值 | 返回 0（暂无精确计时） |
| `learning_summary.completed_tasks` | DailyTask status=completed, 本周 | 实时聚合 |
| `learning_summary.total_tasks` | DailyTask, 本周 | 实时聚合 |
| `learning_summary.average_accuracy` | AnswerRecord 本周 | 实时聚合 |
| `learning_summary.modules_touched` | DailyTask module DISTINCT, 本周 | 实时聚合 |
| `behavior_summary.*` | 行为数据表 | 全 0（表未建） |
| `focus_daily_series` | 专注度行为表 | `[]`（表未建） |
| `posture_weekly_series` | 坐姿行为表 | `[]`（表未建） |
| `anomalies` | 行为洞察表 | `[]`（表未建） |
| `discoveries` | 行为洞察表 | `[]`（表未建） |
| `ai_summary` | LLM 生成 | `""`（管线未建） |

---

## 五、车端防御性修复

`daily_task` 约束放宽后，车端代码必须防御 `module=NULL` 的行。

### [car/task/service.py](cloud/backend/app/car/task/service.py)

1. **`ensure_daily_tasks` 查询加过滤**：`WHERE module IS NOT NULL`
2. **`_task_to_dict` 防御**：`module_label = _mod_label(t.module) if t.module else ""`

---

## 六、共享工具

### `app/parent/service.py` 扩展

提取 `_today()` 函数（从 `dashboard/service.py` 移至共享）：

```python
def today_shanghai() -> date:
    """Asia/Shanghai 时区的今日日期。"""
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).date()

def datetime_range_shanghai(d: date) -> tuple[datetime, datetime]:
    """返回给定日期在 Asia/Shanghai 的 [start, end) datetime。"""
    tz = timezone(timedelta(hours=8))
    start = datetime(d.year, d.month, d.day, tzinfo=tz)
    end = start + timedelta(days=1)
    return start, end
```

`dashboard/service.py` 重构为从 `parent.service` 导入。

---

## 七、测试计划

遵循现有测试模式（`async_client`, token-based auth, composite fixtures）。

| 测试文件 | 覆盖端点 | 预估用例 |
|---------|---------|---------|
| `test_parent_goal.py` | GET/PUT goal | 4 |
| `test_parent_dispatch.py` | GET/POST dispatched-tasks, GET today-tasks + detail | 6 |
| `test_parent_reports.py` | progress, sessions, session detail, wrong-answers, weekly list, weekly detail | 8 |
| **总计** | | **18** |

关键测试场景：
- 未授权访问（无 token → 401，其他 parent 的 child → 404）
- Goal CRUD + 默认值
- Dispatch 批量创建 + 按日期查询
- Session 分页 + 过滤
- Wrong-answer 分页
- Weekly report 学习数据聚合正确性
- Weekly report 空数据（孩子本周无活动）

加上现有 46 tests，全部 46+18=64 tests 通过。ruff 零告警。

---

## 八、交付清单

| # | 文件 | 类型 |
|---|------|------|
| 1 | `app/models/config.py` | 修改：加 LearningGoal model |
| 2 | `alembic/versions/<stamp>_learning_goal.py` | 新建：learning_goal 迁移 |
| 3 | `alembic/versions/<stamp>_relax_daily_task.py` | 新建：daily_task 约束放宽 |
| 4 | `app/parent/service.py` | 修改：提取 _today() 时区工具 |
| 5 | `tests/conftest.py` | 修改：导入 LearningGoal 到 Base.metadata |
| 6 | `app/parent/goal/__init__.py` | 新建 |
| 7 | `app/parent/goal/schemas.py` | 新建 |
| 8 | `app/parent/goal/service.py` | 新建 |
| 9 | `app/parent/goal/router.py` | 新建 |
| 10 | `app/parent/dispatch/__init__.py` | 新建 |
| 11 | `app/parent/dispatch/schemas.py` | 新建 |
| 12 | `app/parent/dispatch/service.py` | 新建 |
| 13 | `app/parent/dispatch/router.py` | 新建 |
| 14 | `app/parent/reports/__init__.py` | 新建 |
| 15 | `app/parent/reports/schemas.py` | 新建 |
| 16 | `app/parent/reports/service.py` | 新建 |
| 17 | `app/parent/reports/router.py` | 新建 |
| 18 | `app/parent/dashboard/service.py` | 修改：用共享 _today() |
| 19 | `app/router.py` | 修改：注册 3 个新 router |
| 20 | `app/car/task/service.py` | 修改：防御 module=NULL |
| 21 | `tests/test_parent_goal.py` | 新建 |
| 22 | `tests/test_parent_dispatch.py` | 新建 |
| 23 | `tests/test_parent_reports.py` | 新建 |
| 24 | `.superpowers/sdd/2026-07-29-backend-fullstack/progress.md` | 修改：更新 Phase 3 进度 |

---

## 九、风险与回滚

| 风险 | 缓解 |
|------|------|
| `daily_task` 约束放宽影响车端 | 同步修复 `car/task/service.py`，加测试 |
| 周报行为数据缺失致小程序 UI 异常 | 返回完整 schema 但默认值，前端应该兼容空数据 |
| 实时聚合性能 | Phase 3 数据量小（每孩子每周 ≤ 几十条），后续必要时加物化 |

回滚：revert merge commit。DDL 迁移可逆（ALTER TABLE 改回 NOT NULL + 原 CHECK）。

---

## 十、待确认项

- [x] Learning Goal 存储 → 新建 `learning_goal` 表
- [x] Dispatched Tasks 存储 → 复用 `daily_task`，放宽 module 约束
- [x] Weekly Report 生成方式 → 实时聚合，行为层 placeholder
- [x] 分支策略 → 先 commit Phase 2，再切 `feature/parent-reports`
- [ ] 用户验收本 spec
