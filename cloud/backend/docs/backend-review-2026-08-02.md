# 蛋壳后端技术审查报告

> **审查日期**: 2026-08-02 | **分支**: `feature/parent-reports` | **审查人**: super_bill
>
> **代码量**: 12,157 行 Python | **测试**: 95 条用例 | **数据表**: 21 张

---

## 一、项目概览

蛋壳后端是一个基于 FastAPI + PostgreSQL 的儿童早教智能体系统后端，服务于两个客户端：

- **小车端 (Car/Device)**: 运行在 SC171 硬件上，提供学习内容、任务领取、遥测上报、消息收发
- **家长端 (Parent)**: 微信小程序，提供孩子管理、学习报告、行为分析、远程控制

```
cloud/backend/
├── app/
│   ├── main.py                   ← FastAPI 应用工厂 + 生命周期
│   ├── config.py                 ← 全局配置 (pydantic-settings, .env)
│   ├── db.py                     ← AsyncEngine + session 工厂 (asyncpg)
│   ├── router.py                 ← 顶层路由聚合
│   │
│   ├── models/  (15 文件, 21 表)  ← ORM 模型层
│   ├── auth/    (5 文件)          ← JWT + refresh token rotation + 限流
│   ├── car/     (4 模块)          ← 车机端 API
│   ├── parent/  (15 模块)         ← 家长端 API
│   ├── telemetry/ (3 文件)        ← 遥测事件摄入
│   ├── middleware/ (3 文件)       ← CORS / RequestID / 异常处理
│   └── schemas/  (1 文件)        ← 通用响应格式 ok() / error()
│
├── alembic/  (18 个迁移版本)       ← 数据库版本管理
├── tests/    (25 文件, 95 条用例)  ← 集成测试
├── scripts/  (3 个种子脚本)        ← 演示数据
└── docs/     (7 份设计/部署文档)   ← API 设计 + 部署指南
```

---

## 二、层级架构

每个功能模块严格遵循 **三层分离**：

```
router.py  → HTTP 层：路由注册、参数提取、JWT 依赖注入、HTTP 状态码
service.py → 业务层：SQLAlchemy 查询、聚合计算、权限校验
schemas.py → 数据层：Pydantic 入参/出参模型
```

**交叉依赖规则**：

- `router` → `service` + `schemas` + `auth/dependencies` + `db`
- `service` → `models` + `parent/service`（共享工具函数）
- `schemas` → 纯 Pydantic，无外部依赖
- `models` → `base`（DeclarativeBase）
- 路由之间互不引用，通过 `app/router.py` 统一注册

**评价**：分层清晰，模块边界明确，依赖方向正确（router→service→models）。新模块遵循统一结构（router/schemas/service 三件套），可维护性高。

---

## 三、API 完成度

### 3.1 家长端 — 23/23 接口组 ✅ 100%

| # | 接口组 | 路由 | 状态 |
|---|--------|------|------|
| 1 | 认证 | `POST auth/wechat/login`, `POST auth/phone/bind`, `POST auth/token/refresh`, `POST auth/logout` | ✅ |
| 2 | 孩子管理 | `GET/POST children`, `GET/PUT/DELETE children/{id}` | ✅ |
| 3 | 设备管理 | `GET/PUT/DELETE children/{id}/device`, `POST children/{id}/device/bind` | ✅ |
| 4 | 学习配置 | `GET/PUT children/{id}/learning/config`, `GET config/audit` | ✅ |
| 5 | 学习目标 | `GET/PUT children/{id}/learning/goal` | ✅ |
| 6 | 今日大盘 | `GET children/{id}/dashboard/today` | ✅ |
| 7 | 今日任务 | `GET children/{id}/today-tasks`, `GET today-tasks/{id}` | ✅ |
| 8 | 派发任务 | `GET/POST children/{id}/dispatched-tasks` | ✅ |
| 9 | 学习进度 | `GET children/{id}/learning/progress` | ✅ |
| 10 | 学习会话 | `GET children/{id}/learning/sessions`, `GET sessions/{id}` | ✅ |
| 11 | 错题本 | `GET children/{id}/learning/wrong-answers` | ✅ |
| 12 | 周报 | `GET children/{id}/reports/weekly`, `GET reports/weekly/{key}` | ✅ |
| 13 | 专注度 | `GET children/{id}/behavior/focus` | ✅ |
| 14 | 坐姿 | `GET children/{id}/behavior/posture` | ✅ |
| 15 | 位置 | `GET children/{id}/behavior/location` | ✅ |
| 16 | 行为洞察 | `GET children/{id}/behavior/insights` | ✅ |
| 17 | 使用时长 | `GET children/{id}/usage`, `GET usage/modules` | ✅ |
| 18 | 在线状态 | `GET children/{id}/online-status` | ✅ |
| 19 | 家长消息 | `GET/POST children/{id}/messages`, `DELETE messages/{id}` | ✅ |
| 20 | 远程遥控 | `POST children/{id}/navigations` | ✅ |
| 21 | 通知设置 | `GET/PUT children/{id}/notification-settings` | ✅ |
| 22 | 通知中心 | `GET notifications`, `PUT notifications/{id}/read` | ✅ |
| 23 | 文件服务 | `POST files/uploads`, `POST uploads/{id}/complete`, `GET files/{id}/access` | ✅ |

### 3.2 车机端 — 10/12 接口组 ✅ 83%

| # | 接口组 | 路由 | 状态 |
|---|--------|------|------|
| 1 | 认证 | `POST auth/login`, `POST auth/refresh`, `POST auth/logout` | ✅ |
| 2 | 学习乐园 | `GET learning/park` | ✅ |
| 3 | 学习会话 | `POST learning/{module}/sessions` (6 模块) | ✅ |
| 4 | 内容批次 | `POST learning/{module}/sessions/{id}/batches` (6 模块) | ✅ |
| 5 | 今日任务 | `GET today-tasks`, `GET today-tasks/{id}`, `POST today-tasks/{id}/claim` | ✅ |
| 6 | 遥测上报 | `POST telemetry/events:batch` | ✅ |
| 7 | 会话完成 | `POST telemetry/sessions/{id}/complete` | ✅ |
| 8 | 会话汇总 | `GET telemetry/sessions/{id}/summary` | ✅ |
| 9 | 文件服务 | `POST files/uploads`, `POST uploads/{id}/complete`, `GET files/{id}/access` | ✅ |
| 10 | 家长消息 | `GET parent-messages`, `POST parent-messages/{id}/replies` | ✅ |
| 11 | 蛋仔聊天 | `POST chat/sessions`, `GET chat/sessions/{id}/messages`, `POST asr/transcriptions`, `POST chat/completions` (SSE) | ❌ Phase 4 |
| 12 | WebSocket | `wss://<host>/v1/api/car/ws` (双向通道: 弹窗/跳转/心跳) | ❌ Phase 4 |

---

## 四、数据库设计 (21 张表)

### 核心表

| 表名 | 用途 | 关键字段 |
|------|------|---------|
| `parent_account` | 家长账号 | `wx_openid`, `phone_hash`, `status` |
| `family` | 家庭 | `name` |
| `child` | 孩子档案 | `family_id`, `nickname`, `gender`, `birth_date` |
| `parent_child` | 家长-孩子绑定 | `parent_id`, `child_id`, `status`, `is_default` |
| `device_binding` | 设备绑定 | `device_id`, `child_id`, `bind_status`, `device_type` |
| `refresh_token` | 刷新令牌 | `token_hash`, `revoked_at`, `rotated_from_id` |

### 学习系统

| 表名 | 用途 | 关键字段 |
|------|------|---------|
| `learning_module_config` | 学习模块配置 | `child_id`, `module`, `enabled`, `difficulty`, `batch_size` |
| `learning_goal` | 每日学习目标 | `child_id`, `daily_goal_minutes`, `module_goals(JSONB)` |
| `config_audit` | 配置变更审计 | `child_id`, `module`, `old_values`, `new_values` |
| `daily_task` | 每日任务 | `child_id`, `business_date`, `module`, `status`, `progress` |
| `learning_session` | 学习会话 | `child_id`, `module`, `source`, `status`, `config_snapshot` |
| `learning_batch` | 内容批次 | `session_id`, `module`, `sequence_no` |
| `batch_item` | 批次内容项 | `batch_id`, `content_type`, `content_snapshot` |
| `answer_record` | 答题记录 | `session_id`, `batch_item_id`, `selected_option_id`, `is_correct` |
| `wrong_answer` | 错题聚合 | `child_id`, `question_id`, `wrong_count` |
| `learning_event` | 遥测事件 | `device_id`, `event_id`, `event_type`, `payload` |

### 内容库

| 表名 | 用途 |
|------|------|
| `science_article` | 科学文章 (difficulty, title, content) |
| `math_question` | 数学题 (difficulty, question, option_a~d, correct_option_id) |
| `english_word` | 英语单词 (difficulty, chinese, english, phonetic) |
| `poem_content` | 诗词 (difficulty, title, content_text) |
| `music_track` | 音乐 (category, name, duration_ms) |
| `quiz_question` | 趣味问答 (difficulty, question, option_a~d, correct_option_id) |

### Phase 3 新增

| 表名 | 用途 |
|------|------|
| `behavior_event` ⭐ | 行为事件 (child_id, event_type, score, payload) |
| `parent_message` ⭐ | 家长消息 (child_id, parent_id, direction, msg_type, content) |
| `navigation_instruction` ⭐ | 远程跳转 (child_id, parent_id, destination, route_key) |
| `notification_settings` ⭐ | 通知设置 (child_id, settings(JSONB), dnd_enabled) |
| `notification` ⭐ | 通知记录 (parent_id, child_id, notif_type, is_read) |
| `file_upload` ⭐ | 文件上传 (parent_id, purpose, storage_path, status) |

**评价**：表结构完整，CheckConstraint 保证数据完整性，JSONB 灵活存储半结构化数据，索引覆盖常见查询路径。`config_audit` 提供完整的配置变更审计追踪。

---

## 五、代码能力评估

### 5.1 认证安全 — 高水准

| 特性 | 实现 |
|------|------|
| JWT 签发/校验 | ✅ `create_access_token` / `decode_token`，scope-based 权限分离 (car vs parent) |
| Refresh token rotation | ✅ 每次刷新换新 token，旧 token 立即吊销 |
| Replay detection | ✅ 检测到重放攻击时撤销整条 rotation chain |
| 手机号哈希 | ✅ HMAC-SHA256 + server-side pepper (`phone_pepper`) |
| Token 哈希 | ✅ HMAC-SHA256 + server-side pepper (`token_pepper`) |
| 手机号脱敏 | ✅ `+8613800138000` → `138****8000` |
| 速率限制 | ✅ 进程内滑动窗口 (标记 TODO: Phase 4 迁移 Redis) |

### 5.2 业务逻辑 — 扎实

- 所有父子资源访问经过 `verify_parent_access()` 校验绑定关系
- 分页查询使用 subquery count，避免两次全表扫描
- 聚合计算（专注度/坐姿分数、学习进度/准确率）正确，包含空值保护
- 时区处理：`Asia/Shanghai` 贯穿所有业务时间计算
- `seed_full_demo.py` 一键生成完整演示数据（1家长+1孩子+14天数据）
- 文件上传采用三段式流程：init → upload → complete

### 5.3 数据库操作 — 规范

- 全异步 SQLAlchemy 2.0+ (`asyncpg` + `AsyncSession`)
- 使用 `mapped_column` / `Mapped[]` 新式声明
- PostgreSQL 特有类型充分利用 (`JSONB`, `UUID`, `CheckConstraint`)
- `on_conflict_do_update` (upsert) 用于幂等操作
- Alembic 管理 schema 变更，18 个有序迁移版本
- `commit`/`rollback` 在 router 层统一管理，service 层只做 `flush`

### 5.4 错误处理 — 一致

- 所有 router 都有 `try/except` + `await db.rollback()` 保护
- 统一 `ok()`/`error()` 响应格式 (`{"code": 0, "msg": "ok", "data": {...}}`)
- 全局异常处理器兜底未捕获异常
- `X-Request-ID` 中间件实现请求全链路追踪
- Pydantic 入参校验自动返回 422 错误

### 5.5 测试覆盖 — 较完善

| 测试文件 | 用例数 | 覆盖模块 |
|---------|--------|---------|
| `test_auth_car_api.py` | 5 | 车机认证 |
| `test_car_learning.py` | 4 | 车机学习 |
| `test_car_files.py` | 3 | 车机文件 |
| `test_car_messages.py` | 3 | 车机消息 |
| `test_telemetry_api.py` | 3 | 遥测上报 |
| `test_parent_reports.py` | 9 | 家长报告 |
| `test_parent_children.py` | 7 | 家长孩子管理 |
| `test_parent_dispatch.py` | 6 | 家长派发任务 |
| `test_parent_behavior.py` | 5 | 家长行为分析 |
| `test_parent_config.py` | 4 | 家长配置 |
| `test_parent_messages.py` | 4 | 家长消息 |
| `test_parent_notifications.py` | 4 | 家长通知 |
| `child/device/goal/dashboard/files/navigation/online/usage` | 2~3 each | 其余模块 |

**测试特点**：
- 使用 `httpx.AsyncClient` + `ASGITransport` 做真实 HTTP 集成测试
- 测试数据库完全隔离（NullPool 连接池，建表/删表 per test）
- 依赖注入覆盖（`dependency_overrides` 替换 DB session）
- Rate limit store 自动清理 fixture 防止测试间污染

### 5.6 可观测性 — 基础完备

- `X-Request-ID` 中间件：每个请求携带唯一 ID
- 全局异常处理器：统一错误格式 + 日志
- 种子脚本可验证：开发环境一键还原完整数据

### 5.7 可部署性 — 就绪

- `Dockerfile` + `docker-compose.yml`（PostgreSQL + Backend）
- `.env` 配置管理，敏感值不入库
- 部署文档完整（本地开发 + 服务器部署）
- 服务器已部署运行 (`88bill99.top`)

---

## 六、历史 Bug 修复记录

| ID | 严重度 | 问题 | 修复 Commit | 状态 |
|----|--------|------|-------------|------|
| B1 | 🔴 严重 | `_session_summary_dict()` 返回硬编码零值，summary 接口无意义 | `8153389` | ✅ |
| B2 | 🟡 中等 | `expires_at` 使用 UTC 而非上海时区 | `122ae22` | ✅ |
| B3 | 🟡 中等 | `issued_at` 使用 UTC 而非上海时区 | `b8f6d17` | ✅ |
| B4 | 🟢 低 | `create_session` 未校验 source 枚举 | `366f011` | ✅ |
| B5 | 🟢 低 | 在线状态进程内存存储 (标记 TODO) | `d54dffc` | ✅ (文档化) |

---

## 七、剩余工作 (Phase 4)

| 优先级 | 项目 | 描述 | 工作量估计 |
|--------|------|------|-----------|
| **P0** | 蛋仔聊天 | `POST chat/sessions`, `GET messages`, `POST asr/transcriptions`, `POST chat/completions` (SSE) — 需 LLM 集成 | 大 |
| **P0** | WebSocket | `wss://<host>/v1/api/car/ws` — 双向通道: 弹窗推送、远程跳转、心跳 | 中 |
| **P2** | 在线状态 → Redis | 替换 `_online_store` 进程内字典，支持多 worker | 小 |
| **P2** | 速率限制 → Redis | 替换进程内 `_rate_limit_store`，支持水平扩展 | 小 |
| **P2** | 文件存储 → OSS/S3 | 替换本地 `/uploads/` 路径为云存储预签名 URL | 中 |
| **P2** | 周报 AI 摘要 | 调用 LLM 生成每周学习行为文字摘要 | 中 |

---

## 八、总评

| 维度 | 评级 | 说明 |
|------|------|------|
| **架构设计** | ⭐⭐⭐⭐⭐ | 三层分离 + 模块化路由，依赖方向清晰，同类项目上乘 |
| **API 完成度** | ⭐⭐⭐⭐ | 家长端 100%，车机端 83%，剩余聊天/WebSocket |
| **代码质量** | ⭐⭐⭐⭐ | 安全实践到位，错误处理一致，异步全覆盖 |
| **数据库设计** | ⭐⭐⭐⭐⭐ | 21 表完整，约束/索引/审计到位，JSONB 灵活运用 |
| **测试覆盖** | ⭐⭐⭐⭐ | 95 条集成测试覆盖全部模块，DB 隔离策略正确 |
| **可部署性** | ⭐⭐⭐⭐ | Docker/Compose 就绪，服务器已运行，文档完整 |
| **安全性** | ⭐⭐⭐⭐⭐ | JWT + refresh rotation + replay detection + pepper hashing |

**结论**：后端核心功能全部可用，架构干净可维护，代码质量扎实。Phase 4 的聊天/WebSocket 是剩余的主要功能缺口，Redis/OSS 迁移是运维增强项，不影响当前系统运行。
