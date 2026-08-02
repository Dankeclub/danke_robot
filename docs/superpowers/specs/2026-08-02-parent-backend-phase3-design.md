# 家长端后端 Phase 3 — 缺失模块补齐设计

- **日期**：2026-08-02
- **分支**：`feature/parent-reports`
- **状态**：已批准，进入实施

## 1. 范围

补齐 parent-api-design.md 中标记但未实现的 7 个接口组，修复 Phase 1-2 遗留的 9 个问题，编写种子数据脚本和部署指南。

### 1.1 新增模块

| # | 模块 | 接口 | 新表 |
|---|------|------|------|
| 1 | 行为分析 | 4 GET（专注度/坐姿/位置/洞察） | `behavior_event` |
| 2 | 使用时长 | 2 GET（日周月序列/模块分布） | 无（查已有表） |
| 3 | 在线状态 | 1 GET | 无（内存缓存） |
| 4 | 家长消息 | 1 GET + 1 POST + 1 DELETE | `parent_message` |
| 5 | 远程遥控 | 1 POST | `navigation_instruction` |
| 6 | 通知设置 | 1 GET + 1 PUT | `notification_settings` |
| 7 | 通知中心 | 1 GET + 1 PUT | `notification` |
| 8 | 文件服务 | 3 endpoints | `file_upload` |

### 1.2 修复清单

| # | 严重度 | 模块 | 问题 |
|---|--------|------|------|
| F1 | 🟡 | goal | 模块分钟之和 ≤ daily_goal_minutes 未校验 |
| F2 | 🟡 | goal | 入参 Schema 包含出参字段 module_label |
| F3 | 🟡 | dispatch | dispatched-tasks POST 可接收 learning 类但 GET 查不到 |
| F4 | 🟡 | reports | 行为字段硬编码 0，缺少 TODO 注释 |
| F5 | 🟢 | reports | task/answer 时间字段口径差异缺少注释 |
| F6 | 🟢 | cors | `allow_origins=["*"]` 产品化需收紧 |
| F7 | 🟢 | security | pepper 常量硬编码，迁移到 config |
| F8 | 🟢 | scripts | seed_fake_data.py 空占位 |
| F9 | 🟢 | 全局 | 空 `__init__.py` 补充 docstring |

## 2. 数据策略

**核心原则**：所有表 schema 对生产数据和种子数据完全一致。生产端（car behavioral 模块）写入 behavior_event 的格式与种子脚本一致。接入生产端时：不改表、不改 API、不改查询——只需 car 端开始上报即可。

### 2.1 种子数据脚本

- `scripts/seed_behavior_data.py`：为每个孩子生成 14 天行为事件（focus_score 波动、posture 记录、zone 分布、insights）
- `scripts/seed_full_demo.py`：一键全量种子（family → child → device → config → goal → content → tasks → sessions → answers → behavior）

## 3. 新表设计

### behavior_event
```sql
child_id UUID FK → child
event_type TEXT CHECK IN ('focus','posture','location','zone')
score INTEGER (0-100)
payload JSONB (详细信息)
recorded_at TIMESTAMPTZ
```

### parent_message
```sql
child_id, parent_id, direction TEXT, msg_type TEXT,
content JSONB, replied_to_id UUID?, is_deleted BOOL
```

### navigation_instruction
```sql
child_id, parent_id, destination TEXT, route_key TEXT,
module TEXT?, custom_batch_size INT?, title TEXT,
expires_at TIMESTAMPTZ, status TEXT
```

### notification_settings
```sql
child_id UNIQUE, settings JSONB, dnd_enabled BOOL,
dnd_start_time TIME, dnd_end_time TIME
```

### notification
```sql
parent_id, child_id, notif_type TEXT, title TEXT,
description TEXT, is_read BOOL, read_at TIMESTAMPTZ?
```

### file_upload
```sql
parent_id, purpose TEXT, file_name TEXT, content_type TEXT,
size_bytes INT, sha256 TEXT, storage_path TEXT, status TEXT
```

## 4. 部署

### 本地开发
```bash
docker compose up -d db          # 启动 PostgreSQL
alembic upgrade head              # 建表
python scripts/seed_full_demo.py  # 灌种子数据
uvicorn app.main:app --reload     # 启动后端
```

### 生产部署（88bill99.top）
```bash
# 服务器上
git clone <repo> && cd cloud/backend
cp .env.example .env  # 编辑填入真实 JWT_SECRET, WX_APPID, WX_SECRET
docker compose up -d
alembic upgrade head
python scripts/seed_full_demo.py
# Nginx 反代 :8000，证书用已有的 Let's Encrypt
```

## 5. 文件结构

```
app/parent/
├── behavior/          # 新增：专注度/坐姿/位置/洞察
├── usage/             # 新增：使用时长
├── online/            # 新增：在线状态
├── messages/          # 新增：家长消息
├── navigation/        # 新增：远程遥控
├── notifications/     # 新增：通知设置+通知中心
├── files/             # 新增：文件服务
├── children/          # 已有
├── config/            # 已有
├── dashboard/         # 已有
├── device/            # 已有
├── dispatch/          # 已有
├── goal/              # 已有
├── reports/           # 已有
└── service.py         # 已有共享
```

## 6. 自检清单

- [ ] 所有新路由注册到 app/router.py
- [ ] 所有新模型导入到 alembic/env.py 和 tests/conftest.py
- [ ] 每个模块至少 3 个集成测试
- [ ] 种子脚本可重复执行（幂等：检查已有数据跳过）
- [ ] .env.example 更新新增配置项
- [ ] 不新增依赖（使用已有 fastapi/sqlalchemy/asyncpg）
