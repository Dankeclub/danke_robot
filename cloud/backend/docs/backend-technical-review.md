# 蛋壳后端技术文档

> 生成日期: 2026-08-02 | 分支: `feature/parent-reports` | 89 测试通过

---

## 一、系统架构

```
cloud/backend/
├── app/
│   ├── main.py                  # FastAPI 工厂，启动/关闭生命周期
│   ├── config.py                # Settings (pydantic-settings, env 加载)
│   ├── db.py                    # AsyncEngine + Session 工厂 (asyncpg)
│   ├── router.py                # 顶层路由聚合
│   │
│   ├── models/                  # ORM 模型层 (15 文件, 21 表)
│   │   ├── base.py              # DeclarativeBase + AuditMixin
│   │   ├── parent.py            # ParentAccount
│   │   ├── child.py             # Child
│   │   ├── family.py            # Family
│   │   ├── parent_child.py      # ParentChild (M2M)
│   │   ├── device_binding.py    # DeviceBinding
│   │   ├── learning.py          # LearningSession, LearningBatch, BatchItem
│   │   ├── task.py              # DailyTask
│   │   ├── answer.py            # AnswerRecord, WrongAnswer
│   │   ├── config.py            # LearningModuleConfig, ConfigAudit, LearningGoal
│   │   ├── content.py           # ScienceArticle, MathQuestion, EnglishWord, PoemContent, MusicTrack, QuizQuestion
│   │   ├── behavior.py          # BehaviorEvent *NEW*
│   │   ├── message.py           # ParentMessage *NEW*
│   │   ├── navigation.py        # NavigationInstruction *NEW*
│   │   ├── notification.py      # Notification, NotificationSettings *NEW*
│   │   └── file_upload.py       # FileUpload *NEW*
│   │
│   ├── auth/                    # 认证模块
│   │   ├── router_car.py        # 车机: POST /auth/login (手机号), /refresh, /logout
│   │   ├── router_parent.py     # 家长: POST /auth/wechat/login, /phone/bind, /refresh, /logout
│   │   ├── dependencies.py      # get_current_device, get_current_parent (JWT 提取)
│   │   ├── security.py          # JWT 签发/校验, refresh token rotation, 速率限制
│   │   └── schemas.py           # 认证相关 Pydantic 模型
│   │
│   ├── car/                     # 小车端 API (2 模块)
│   │   ├── learning/            # GET /learning/park, POST /learning/{m}/sessions, POST /learning/{m}/sessions/{id}/batches
│   │   └── task/                # GET /today-tasks, GET /today-tasks/{id}, POST /today-tasks/{id}/claim
│   │
│   ├── parent/                  # 家长端 API (15 模块)
│   │   ├── behavior/            # GET behavior/{focus,posture,location,insights} *NEW*
│   │   ├── children/            # CRUD 孩子管理
│   │   ├── config/              # GET/PUT 学习配置 + 审计历史
│   │   ├── dashboard/           # GET 今日大盘
│   │   ├── device/              # 设备绑定/改名/解绑
│   │   ├── dispatch/            # 今日任务列表/详情 + 派发任务
│   │   ├── files/               # POST uploads, POST complete, GET access *NEW*
│   │   ├── goal/                # GET/PUT 学习目标
│   │   ├── messages/            # 家长消息 CRUD *NEW*
│   │   ├── navigation/          # POST 远程跳转指令 *NEW*
│   │   ├── notifications/       # 通知设置 + 通知中心 *NEW*
│   │   ├── online/              # GET 在线状态 *NEW*
│   │   ├── reports/             # 学习进度/会话/错题/周报
│   │   ├── usage/               # GET 使用时长系列 + 模块分布 *NEW*
│   │   └── service.py           # verify_parent_access, today_shanghai, datetime_range_shanghai
│   │
│   ├── telemetry/               # 遥测事件摄入
│   │   ├── router.py            # POST events:batch, POST sessions/{id}/complete, GET sessions/{id}/summary
│   │   ├── service.py           # 幂等插入, 答题判定, 错题追踪, 会话完成
│   │   └── schemas.py
│   │
│   ├── middleware/               # CORS, X-Request-ID, 全局异常处理
│   └── schemas/                 # APIResponse, ok(), error()
│
├── alembic/                     # 数据库迁移 (18 版本)
├── tests/                       # 集成测试 (17 文件, 89 cases)
├── scripts/                     # 种子数据
│   ├── seed_learning_data.py    # 学习内容 + 配置种子
│   ├── seed_behavior_data.py    # 14 天行为事件种子 *NEW*
│   └── seed_full_demo.py        # 一键全量演示数据 *NEW*
├── docs/
│   ├── parent-api-design.md     # 家长端 API 设计
│   ├── car-api-design.md        # 小车端 API 设计
│   ├── deployment.md            # 部署指南 *NEW*
│   ├── parent-openapi.yaml      # 家长端 OpenAPI 规范
│   └── car-openapi.yaml         # 小车端 OpenAPI 规范
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

### 层级划分

每个功能模块严格遵循三层分离：

```
router.py   →  HTTP 层：路由、参数提取、JWT 依赖注入、HTTP 状态码
service.py  →  业务层：SQLAlchemy 查询、聚合计算、权限校验
schemas.py  →  数据层：Pydantic 入参/出参模型、枚举常量
```

**交叉依赖规则：**
- `router` → `service` + `schemas` + `auth/dependencies` + `db`
- `service` → `models` + `parent/service`（共享工具）
- `schemas` → 纯 Pydantic，无外部依赖
- `models` → `base`（AuditMixin）
- 路由之间互不引用，通过 `app/router.py` 统一注册

---

## 二、API 完整度

### 家长端 (47 条路由)

| # | 接口组 | 端点 | 状态 |
|---|--------|------|------|
| 1 | 认证 | POST auth/wechat/login, POST auth/phone/bind, POST auth/token/refresh, POST auth/logout | ✅ |
| 2 | 孩子管理 | GET/POST children, GET/PUT/DELETE children/{id} | ✅ |
| 3 | 设备管理 | GET/PUT/DELETE children/{id}/device, POST children/{id}/device/bind | ✅ |
| 4 | 学习配置 | GET/PUT children/{id}/learning/config, GET config/audit | ✅ |
| 5 | 学习目标 | GET/PUT children/{id}/learning/goal | ✅ |
| 6 | 今日大盘 | GET children/{id}/dashboard/today | ✅ |
| 7 | 今日任务 | GET children/{id}/today-tasks, GET today-tasks/{id} | ✅ |
| 8 | 派发任务 | GET/POST children/{id}/dispatched-tasks | ✅ |
| 9 | 学习进度 | GET children/{id}/learning/progress | ✅ |
| 10 | 学习会话 | GET children/{id}/learning/sessions, GET sessions/{id} | ✅ |
| 11 | 错题本 | GET children/{id}/learning/wrong-answers | ✅ |
| 12 | 周报 | GET children/{id}/reports/weekly, GET reports/weekly/{key} | ✅ (已接入行为数据) |
| 13 | 专注度 | GET children/{id}/behavior/focus | ✅ *NEW* |
| 14 | 坐姿 | GET children/{id}/behavior/posture | ✅ *NEW* |
| 15 | 位置 | GET children/{id}/behavior/location | ✅ *NEW* |
| 16 | 行为洞察 | GET children/{id}/behavior/insights | ✅ *NEW* |
| 17 | 使用时长 | GET children/{id}/usage, GET usage/modules | ✅ *NEW* |
| 18 | 在线状态 | GET children/{id}/online-status | ✅ *NEW* |
| 19 | 家长消息 | GET/POST children/{id}/messages, DELETE messages/{id} | ✅ *NEW* |
| 20 | 远程遥控 | POST children/{id}/navigations | ✅ *NEW* |
| 21 | 通知设置 | GET/PUT children/{id}/notification-settings | ✅ *NEW* |
| 22 | 通知中心 | GET notifications, PUT notifications/{id}/read | ✅ *NEW* |
| 23 | 文件服务 | POST files/uploads, POST uploads/{id}/complete, GET files/{id}/access | ✅ *NEW* |

**家长端: 23/23 接口组, 100% 完成**

### 小车端 (11 条 REST 路由)

| # | 接口组 | 端点 | 状态 |
|---|--------|------|------|
| 1 | 认证 | POST auth/login, POST auth/refresh, POST auth/logout | ✅ |
| 2 | 学习乐园 | GET learning/park | ✅ |
| 3 | 学习会话 | POST learning/{module}/sessions (6 模块) | ✅ |
| 4 | 内容批次 | POST learning/{module}/sessions/{id}/batches (6 模块) | ✅ |
| 5 | 今日任务 | GET today-tasks, GET today-tasks/{id}, POST today-tasks/{id}/claim | ✅ |
| 6 | 遥测上报 | POST telemetry/events:batch | ✅ |
| 7 | 会话完成 | POST telemetry/sessions/{id}/complete | ✅ |
| 8 | 会话汇总 | GET telemetry/sessions/{id}/summary | ✅ |
| 9 | 文件服务 | POST files/uploads, POST uploads/{id}/complete, GET files/{id}/access | ❌ |
| 10 | 蛋仔聊天 | POST chat/sessions, GET chat/sessions/{id}/messages, POST asr/transcriptions, POST chat/completions (SSE) | ❌ |
| 11 | 家长消息 | GET parent-messages, POST parent-messages/{id}/replies | ❌ |
| 12 | WebSocket | wss://<host>/v1/api/car/ws | ❌ |

**小车端: 8/12 接口组, 67% 完成**

---

## 三、已知 Bug

| # | 严重度 | 位置 | 问题 | 影响 |
|---|--------|------|------|------|
| B1 | 🔴 严重 | `telemetry/service.py:261-275` | `_session_summary_dict()` 返回硬编码零值，从未调用 `_get_session_answer_stats()`。`GET /telemetry/sessions/{id}/summary` 返回的 accuracy/correct/wrong 始终为 0 | 小车端会话汇总接口无实际数据 |
| B2 | 🟡 中等 | `car/task/service.py:41-42` | `expires_at` 使用 `datetime.now(UTC)` 而非上海时区，设计文档规定"次日 00:00:00+08:00" | 任务过期时间偏差 8 小时 |
| B3 | 🟡 中等 | `car/learning/service.py:219` | `issued_at=datetime.now(UTC)` 使用 UTC，与设计文档的上海时区约定不一致 | 批次时间戳偏差 |
| B4 | 🟢 低 | `car/learning/router.py:39` | `create_session` 未校验 `source` 枚举值，非法值会穿透到数据库触发 CheckConstraint 异常 | 错误信息不友好 |
| B5 | 🟢 低 | `parent/online/service.py` | 在线状态存储在进程内存中，重启丢失，多 worker 不一致 | Phase 4 待迁移 Redis |

---

## 四、数据库表清单 (21 张)

| 表名 | 用途 | 关键字段 |
|------|------|---------|
| parent_account | 家长账号 | wx_openid, phone_hash, status |
| family | 家庭 | name |
| child | 孩子档案 | family_id, nickname, gender, birth_date |
| parent_child | 家长-孩子绑定 | parent_id, child_id, status, is_default |
| device_binding | 设备绑定 | device_id, child_id, bind_status, device_type |
| refresh_token | 刷新令牌 | token_hash, revoked_at, rotated_from_id |
| learning_module_config | 学习模块配置 | child_id, module, enabled, difficulty, batch_size |
| learning_goal | 每日学习目标 | child_id, daily_goal_minutes, module_goals(JSONB) |
| config_audit | 配置变更审计 | child_id, module, old_values, new_values |
| daily_task | 每日任务 | child_id, business_date, module, status, progress |
| learning_session | 学习会话 | child_id, module, source, status, config_snapshot |
| learning_batch | 内容批次 | session_id, module, sequence_no |
| batch_item | 批次内容项 | batch_id, content_type, content_snapshot |
| answer_record | 答题记录 | session_id, batch_item_id, selected_option_id, is_correct |
| wrong_answer | 错题聚合 | child_id, question_id, wrong_count |
| learning_event | 遥测事件 | device_id, event_id, event_type, payload |
| science_article | 科学文章 | difficulty, title, content |
| math_question | 数学题 | difficulty, question, option_a~d, correct_option_id |
| english_word | 英语单词 | difficulty, chinese, english, phonetic |
| poem_content | 诗词 | difficulty, title, content_text |
| music_track | 音乐 | category, name, duration_ms |
| quiz_question | 趣味问答 | difficulty, question, option_a~d, correct_option_id |
| behavior_event ⭐ | 行为事件 | child_id, event_type, score, payload |
| parent_message ⭐ | 家长消息 | child_id, parent_id, direction, msg_type, content |
| navigation_instruction ⭐ | 远程跳转 | child_id, parent_id, destination, route_key |
| notification_settings ⭐ | 通知设置 | child_id, settings(JSONB), dnd_enabled |
| notification ⭐ | 通知记录 | parent_id, child_id, notif_type, is_read |
| file_upload ⭐ | 文件上传 | parent_id, purpose, storage_path, status |

⭐ = Phase 3 新增

---

## 五、种子数据

| 脚本 | 创建数据 |
|------|---------|
| `seed_full_demo.py` | 1 家长 + 1 家庭 + 1 孩子 + 1 设备 + 6 模块配置 + 学习目标 + 7 天 × 6 模块任务 + 5 天 × 3 模块学习会话/批次/答题 + 14 天行为事件 |
| `seed_learning_data.py` | 5 科学文章 + 8 数学题 + 8 英语单词 + 5 诗词 + 7 音乐 + 7 问答 |
| `seed_behavior_data.py` | 每孩子 14 天行为事件 (focus/posture/location) |

---

## 六、部署

### 本地开发

```bash
cd cloud/backend
docker compose up -d db               # 启动 PostgreSQL
alembic upgrade head                  # 建表
python scripts/seed_full_demo.py      # 灌数据
uvicorn app.main:app --reload         # 启动
```

### 服务器 (88bill99.top)

```bash
docker compose up -d                  # PostgreSQL + Backend
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/seed_full_demo.py
# Nginx 反代 127.0.0.1:8000 → 443
```

详见 `cloud/backend/docs/deployment.md`

---

## 七、待完成 (Phase 4)

### P0 — 小车端缺失接口
1. **文件服务** — `POST /v1/api/car/files/uploads`, `POST .../complete`, `GET .../{id}/access`
2. **家长消息(车机端)** — `GET /v1/api/car/parent-messages`, `POST .../{id}/replies`
3. **蛋仔聊天** — `POST /v1/api/car/chat/sessions`, `GET .../messages`, `POST /v1/api/car/asr/transcriptions`, `POST /v1/api/car/chat/completions` (SSE)
4. **WebSocket** — `wss://<host>/v1/api/car/ws` (双向通道, 弹窗, 跳转, 心跳)

### P1 — Bug 修复
5. **B1** — `_session_summary_dict()` 接入 `_get_session_answer_stats()`
6. **B2** — 车机 task 过期时间改用上海时区
7. **B3** — 车机批次 issued_at 改用上海时区
8. **B4** — `create_session` 加 source 枚举校验

### P2 — 增强
9. 在线状态从内存迁移 Redis
10. 速率限制从内存迁移 Redis
11. 文件服务从本地磁盘迁移 OSS/S3
12. 周报 AI 摘要 (LLM 生成)
