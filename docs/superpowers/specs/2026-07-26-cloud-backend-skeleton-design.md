# 云后端骨架设计规格

- **状态**：已批准（经 Doctor Bill review + 修正，2026-07-26）
- **日期**：2026-07-26
- **范围**：FastAPI 应用骨架 + 车端认证 + 家长端认证 + 行为事件上报 + 小车登录页 + 部署配置 + ParentChild 联合主键修正 + ParentAccount phone nullable 修正
- **对应设计文档**：`cloud/backend/docs/learning-backend-design.md`、`car-api-design.md`、`parent-api-design.md`、各 OpenAPI YAML

---

## 1. 背景与目标

### 1.1 当前状态

Phase 1（统一身份）已完成 5 张数据库表的模型层和 Alembic 迁移，16 个测试通过。但缺少 FastAPI 应用实例、API 路由、认证和任何业务逻辑。

小车前端（`car/screen/`）已完成 15 个 Vue 页面的 UI 和交互，但没有任何网络层，所有数据为硬编码。家长端小程序（`parent/`）已完成 15 个页面的 UI，等待后端 API 对接。

### 1.2 本轮目标

1. 搭建最小可运行后端骨架
2. 车端可完成：**手机号登录 → JWT → 上报行为事件**
3. 家长端可完成：**微信一键登录 → JWT → 后续接口可用**
4. 小车前端可完成：**开机 → 登录页 → 拿 token → 进首页**

### 1.3 明确不做（本轮）

- 学习模块、任务、聊天、文件、家长消息、WebSocket 实时推送
- Redis、S3、ASR、LLM 等外部依赖接入
- 单家庭→多家庭模型迁移（标记 TODO，后续做）
- 小车 15 个功能页面接入真实 API（只做登录页 + 网络层）

---

## 2. 前置修正

### 2.1 ParentChild：联合主键

当前 `ParentChild` 继承 `AuditMixin` 使用自增 UUID 做主键，用 `UniqueConstraint("parent_id", "child_id")` 保证业务唯一性。修正为用 `(parent_id, child_id)` 做联合主键，移除 UUID id，保留 created_at/updated_at 审计字段（不加 AuditMixin，手写两个时间列）。

**迁移策略**：现有迁移是 2026-07-25 创建，项目未部署，直接改最后一个迁移并重建数据库。

**影响文件**：
- `app/models/parent_child.py` — 联合主键
- `tests/test_parent_child.py` — 调整测试
- Alembic 迁移链 — 重建

### 2.2 ParentAccount：手机号字段改为可空

当前 `ParentAccount` 的 `phone_e164`、`phone_hash`、`phone_masked` 均为 `nullable=False`，`phone_hash` 含 `unique=True`。但 §5.2 微信登录流程要求支持"尚无手机号"的新用户——微信 `wx.login()` 成功后创建 `ParentAccount(status=pending_bind)`，手机号后续绑定。

**修正方案**：
1. `phone_e164`、`phone_hash`、`phone_masked` 改为 `nullable=True`
2. `phone_hash` 的唯一约束改为 **conditional unique index**：`CREATE UNIQUE INDEX ... ON parent_account(phone_hash) WHERE phone_hash IS NOT NULL`
3. ORM 层面通过 DDL event 注册该索引（与 `DeviceBinding` 现有 partial unique index 模式一致，参考 `app/models/device_binding.py:73-80`）

**迁移策略**：新增一个 Alembic 迁移 `alter_parent_account_phone_nullable` 做这三项变更。

**影响文件**：
- `app/models/parent.py` — nullable + DDL event
- 新增 Alembic 迁移

---

## 3. 应用架构

### 3.1 目录结构

```
cloud/backend/app/
├── __init__.py
├── main.py                    # NEW: FastAPI app factory + lifespan
├── router.py                  # NEW: 顶层路由聚合
│       # include_router(car_router, prefix="/v1/api/car")
│       # include_router(parent_router, prefix="/v1/api/parent")
│       # telemetry 路由挂在 car_router 下
├── config.py                  # EXTEND: JWT、微信 相关配置
├── db.py                      # (不变)
├── middleware/                # NEW
│   ├── __init__.py
│   ├── cors.py                #   CORS 配置
│   ├── request_id.py          #   X-Request-ID 注入
│   └── error_handler.py       #   全局异常 → 统一 JSON 响应
├── schemas/                   # NEW
│   ├── __init__.py
│   └── common.py              #   {code, msg, data} 响应包裹
├── auth/                      # NEW
│   ├── __init__.py
│   ├── models.py              #   RefreshToken 模型
│   ├── schemas.py             #   请求/响应 pydantic
│   ├── security.py            #   JWT 签发/验证/token 轮换
│   ├── dependencies.py        #   get_current_device 依赖
│   ├── router_car.py          #   车端手机号登录/刷新/登出
│   └── router_parent.py       #   家长微信登录/刷新/登出
├── telemetry/                 # NEW
│   ├── __init__.py
│   ├── models.py              #   LearningEvent 模型
│   ├── schemas.py             #   事件上报请求/响应
│   ├── service.py             #   事件幂等写入
│   └── router.py              #   POST /telemetry/events:batch
└── models/                    # EXTEND: __init__.py 需 import 新模型
                                #   RefreshToken、LearningEvent
                                #   确保 Alembic env.py 的 Base.metadata 能发现所有模型
```

### 3.2 技术选型

| 组件 | 选择 | 依据 |
|------|------|------|
| JWT 库 | `PyJWT` | 轻量、纯 Python、活跃维护。python-jose 已停更 |
| 密码哈希 | `hashlib` (sha256) | 手机号 hash 查重，不需要 bcrypt |
| Token 算法 | HS256 | 单体应用，无需非对称。后续切 RS256/ES256 只需改配置 |
| 微信 HTTP 调用 | `httpx` | 骨架阶段唯一外部 HTTP 依赖；需从 dev 提升为 production 依赖 |
| 小车前端 | Vue 3（沿用现有） | 只需新增登录页 + 网络层 |

### 3.3 统一响应格式

所有 API 返回：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {}
}
```

HTTP 状态码语义：`200` 成功、`401` 未认证、`404` 不存在、`409` 冲突、`422` 校验失败、`500` 内部错误。

---

## 4. API 路由

### 4.1 车端路由（前缀 `/v1/api/car`）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/login` | 手机号登录 |
| POST | `/auth/refresh` | 刷新 token |
| POST | `/auth/logout` | 登出（撤销 refresh token） |
| POST | `/telemetry/events:batch` | 批量上报行为事件 |

### 4.2 家长端路由（前缀 `/v1/api/parent`）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/wechat/login` | 微信 code 换 token |
| POST | `/auth/phone/bind` | 绑定手机号 |
| POST | `/auth/refresh` | 刷新 token |
| POST | `/auth/logout` | 登出 |

### 4.3 通用

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |

---

## 5. Auth 模块设计

### 5.1 车端手机号登录流程

```text
POST /v1/api/car/auth/login
Body: { phone: "+8613800138000", device_id: "SN-001",
        device_name: "小蛋机器人", device_type: "car", app_version: "1.0.0" }

1. phone hash → 查 parent_account.phone_hash
2. 未找到 → 返回 phone_not_bound (404)
3. 找到 parent → 通过 ParentChild + Child 找到默认孩子（`is_default=True`）
   - **骨架限制**：一个家长多个孩子时，只取 `is_default=True` 的孩子，无法在车机上切换
   - 后续通过车机端孩子选择器或扫码绑定设备解决；代码中标记 `# TODO: support multi-child selection on car login`
4. 查/创建设备绑定 DeviceBinding
5. 签发 access_token (2h) + refresh_token (30d)
6. 存 refresh_token hash
7. 返回 { access_token, refresh_token, expires_in, child_profile }
```

### 5.2 家长端微信登录流程

```text
POST /v1/api/parent/auth/wechat/login
Body: { code: "wx_login_code_from_wx.login()" }

1. httpx 调微信 https://api.weixin.qq.com/sns/jscode2session
   ?appid={WX_APPID}&secret={WX_SECRET}&js_code={code}&grant_type=authorization_code
2. 取 openid + unionid（如有）
3. 查 ParentAccount.wx_openid
4. 如果未找到：新建 ParentAccount（status=pending_bind，尚无手机号）
   返回 { access_token, refresh_token, is_new_user: true, need_bind_phone: true }
5. 如果找到且已绑定手机号：
   返回 { access_token, refresh_token, profile }
6. 找到但未绑定手机号：
   返回 { access_token, ..., need_bind_phone: true }
```

### 5.3 绑定手机号流程

```text
POST /v1/api/parent/auth/phone/bind
Authorization: Bearer <access_token>（微信登录后拿到的）
Body: { encrypted_phone: "wx.getPhoneNumber() 返回的加密数据" }

或者第一期简化：直接传明文 phone，后端 hash 存储
Body: { phone: "+8613800138000" }

1. 校验 phone 是否已被其他账号绑定 → 409 phone_already_bound
2. 更新当前 ParentAccount.phone_e164 / phone_hash / phone_masked
3. 更新 status → active
4. 返回 { profile }
```

### 5.4 Token 设计

| 参数 | 值 |
|------|-----|
| access_token TTL | 7200s (2h) |
| refresh_token TTL | 2592000s (30d) |
| 算法 | HS256 |
| JWT payload | `{ sub, child_id, family_id, scope, iat, exp, jti }` |
| 车端 scope | `car.learning.read car.learning.write car.chat car.messages car.files car.realtime` |
| 家长端 scope | `parent.read parent.write parent.manage` |

### 5.5 Refresh Token 轮换

- 每次 refresh 后旧 token 标记 revoked，签发新 token
- `rotated_from_id` 链可追溯
- 检测到重放（已 revoked token 被再次使用）→ 撤销整条链

### 5.6 RefreshToken 模型

```text
refresh_token
├── id: UUID PK
├── token_hash: text NOT NULL UNIQUE
├── parent_id: UUID FK (nullable，家长端填写)
├── device_id: text FK (nullable，车端填写)
├── child_id: UUID FK (nullable)
├── family_id: UUID FK (nullable)
├── expires_at: timestamptz NOT NULL
├── revoked_at: timestamptz
├── rotated_from_id: UUID FK self-ref
├── created_at: timestamptz
└── updated_at: timestamptz
```

> 注意：parent_id 和 device_id 二选一非空，由应用层保证。车端登录填 device_id，家长登录填 parent_id。

### 5.7 安全措施

- 手机号 hash 查询，不存明文
- refresh_token 只存 hash（SHA-256）
- 手机号登录限流：同一 IP 每分钟最多 5 次
- **限流实现说明（骨架阶段）**：使用内存字典计数，**仅支持单 worker**。多 worker 部署时内存限流会失效（每个 worker 独立计数）。Docker Compose 中显式设置 `--workers 1`，代码中加 `# TODO: Replace with Redis-based rate limiter (lua script / sliding window) when multi-worker is needed`。后续 Redis 接入后替换。
- 微信 code 不可重放（微信侧保证）
- 未绑定手机号返回 `phone_not_bound`（不暴露是否存在）

---

## 6. Telemetry 模块设计

### 6.1 事件上报

```text
POST /v1/api/car/telemetry/events:batch
Authorization: Bearer <access_token>（车端 token，device_id 从 JWT 解析）
Body: {
  events: [
    {
      event_id: "evt-uuid-1",
      event_type: "learning.session.start",
      module: "math",
      timestamp: "2026-07-26T10:30:00+08:00",
      payload: { session_id: "...", ... }
    }
  ]
}
```

### 6.2 幂等机制

- `event_id` 由车端生成（UUID v4）
- `LearningEvent` 表对 `(device_id, event_id)` 建唯一索引
- 重复 event_id 返回 `200` + 原 event（不报错）

### 6.3 LearningEvent 模型

```text
learning_event
├── id: UUID PK
├── device_id: text NOT NULL (FK → device_binding.device_id)
├── child_id: UUID NOT NULL (FK → child.id)
├── event_id: text NOT NULL（车端生成的幂等 ID）
├── event_type: text NOT NULL
├── module: text（六模块枚举，nullable）
├── timestamp: timestamptz NOT NULL（事件发生时间）
├── payload: jsonb NOT NULL DEFAULT '{}'
├── received_at: timestamptz NOT NULL（服务端接收时间）
├── created_at: timestamptz
└── UNIQUE(device_id, event_id)
```

---

## 7. 小车前端新增

### 7.1 登录页 `LoginView.vue`

- 手机号输入框（大字，触屏友好）
- 数字键盘（Grid 3×4，沿用现有涂鸦手绘风）
- 提交按钮（复用 SceneCard / btn-sketch 风格）
- 错误状态（手机号格式错误、phone_not_bound 等）
- 登录成功后自动跳转 HomeView

### 7.2 网络层 `utils/api.js`

- `fetch` 封装，自动注入 `Authorization: Bearer <token>`
- Token 管理：登录后存入 `localStorage`
- 自动刷新：401 时用 refresh_token 换新 access_token
- 刷新失败 → 清除 token → 跳登录页

### 7.3 路由守卫

- `router.beforeEach`：没有 token → 跳 `/login`
- `/login` 路由：已有 token → 直接跳 `/`
- `/` 路由变为需要登录的受保护页面

### 7.4 不影响现有代码

- 仅新增 `LoginView.vue` + `utils/api.js`
- 路由文件加一条 `/login` 路由 + 一个 beforeEach 守卫
- 15 个功能页面不动，仍用硬编码数据

---

## 8. 部署配置

### 8.1 Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

需配套创建 `.dockerignore`，排除 `.env`、`__pycache__`、`.pytest_cache`、`.git`、`node_modules` 等。

### 8.2 docker-compose.yml

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: parent
      POSTGRES_PASSWORD: parent
      POSTGRES_DB: parent_db
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]

  backend:
    build: .
    ports: ["8000:8000"]
    depends_on: [db]
    env_file: .env

volumes:
  pgdata:
```

---

## 9. 配置扩展

`config.py` 新增：

```python
# JWT
JWT_SECRET: SecretStr           # 签名密钥（.env 注入，SecretStr 防日志泄漏）
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_TTL_SECONDS: int = 7200
REFRESH_TOKEN_TTL_SECONDS: int = 2592000

# 微信
WX_APPID: str = ""              # 小程序 AppID
WX_SECRET: SecretStr = ""       # 小程序 Secret（SecretStr 防日志泄漏）

# 限流
PHONE_LOGIN_RATE_LIMIT: int = 5

# 业务
BUSINESS_TIMEZONE: str = "Asia/Shanghai"
```

---

## 10. 测试计划

- Pytest + httpx.AsyncClient 做 API 集成测试
- 新增 `conftest.py` 夹具：`async_client`（FastAPI TestClient）、`auth_headers`
- 测试文件：
  - `tests/test_auth_car_api.py` — 车端登录/刷新/登出
  - `tests/test_auth_parent_api.py` — 家长微信登录/绑定/刷新/登出
  - `tests/test_telemetry_api.py` — 事件批量上报 + 幂等

---

## 11. 迁移清单

本次需新建的 Alembic 迁移（共 4 个）：

1. `fix_parent_child_pk` — ParentChild 联合主键修正
2. `alter_parent_account_phone_nullable` — ParentAccount phone 字段改 nullable + conditional unique index
3. `create_refresh_token` — RefreshToken 表
4. `create_learning_event` — LearningEvent 表

---

## 12. 开发顺序

```
1. ParentChild 联合主键修正 + ParentAccount phone nullable + 测试修订
2. config.py 扩展（JWT、微信、限流）+ pyproject.toml 加 httpx 到 dependencies
3. 应用骨架（main.py + middleware + schemas/common.py）
4. Auth 模块（models → security → dependencies → router_car → router_parent）
5. Telemetry 模块（models → service → router）
6. 小车登录页 + 网络层 + 路由守卫
7. 部署配置（Dockerfile + docker-compose）
8. 集成测试
```

---

## 13. 待确认 / 后续标记

| 项目 | 处理 |
|------|------|
| 单家庭→多家庭 | 标记 TODO，Child.family_id 暂不变 |
| 小车 15 个页面接入 API | 后续按模块逐个接 |
| 家长端查询 API（孩子摘要等） | 下一轮 |
| device_binding 缺少 family_id | 骨架不阻塞，后续加 |
| Redis / S3 / ASR / LLM | 对应模块实现时接入 |
| Context7 安装 | 正式开发前建议装 |
| doctor-bill-software 安装 | 正式开发测试流程需要 |

---

## 14. 审批记录

- 2026-07-26：用户批准范围（车端 + 家长端认证、telemetry、小车登录页、ParentChild 联合主键修正）
- 2026-07-26：Doctor Bill review 发现 2 个 Critical 问题（C1: ParentAccount phone nullable 与微信登录冲突，C2: 多 worker 限流失效）及若干 Medium/Low 问题，已全部修正入 spec
