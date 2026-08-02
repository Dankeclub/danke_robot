# 蛋壳后端部署指南

> 目标服务器：`88bill99.top`（SSH 端口 `30000`，用户 `ljf`）
> 适用场景：开发环境本地部署 + 生产环境服务器部署

---

## 一、快速开始（本地开发）

### 1.1 前提条件

- Docker Desktop（Windows/Mac）或 Docker Engine（Linux）
- Python 3.12+
- Git

### 1.2 启动 PostgreSQL

```bash
cd cloud/backend
docker compose up -d db
```

等待数据库就绪（healthcheck 通过）：

```bash
docker compose ps
# db 状态应为 "healthy"
```

### 1.3 创建数据库表

```bash
cd cloud/backend
alembic upgrade head
```

### 1.4 灌入种子数据

```bash
# 一键全量种子（推荐：家庭→孩子→设备→配置→内容→任务→会话→答题→行为事件）
python scripts/seed_full_demo.py

# 或分步执行
python scripts/seed_learning_data.py   # 学习内容 + 配置
python scripts/seed_behavior_data.py   # 14 天行为事件
```

### 1.5 启动后端

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

验证：浏览器打开 `http://localhost:8000/health`

返回 `{"code": 0, "msg": "ok", "data": {"status": "healthy"}}` 即成功。

### 1.6 运行测试

```bash
# 全部测试
python -m pytest tests/ -v

# 特定模块
python -m pytest tests/test_parent_goal.py -v
python -m pytest tests/test_parent_reports.py -v
```

---

## 二、生产部署（88bill99.top）

### 2.1 服务器登录

```bash
ssh ljf@88bill99.top -p 30000
```

### 2.2 克隆代码

```bash
cd ~
git clone <仓库地址> danke_robot
cd danke_robot/cloud/backend
```

### 2.3 配置环境变量

```bash
cp .env.example .env
nano .env
```

关键配置项：

```ini
APP_ENV=prod
DATABASE_URL=postgresql+asyncpg://parent:parent@db:5432/parent_db
JWT_SECRET=<生成一个强随机字符串>
WX_APPID=<微信小程序 AppID>
WX_SECRET=<微信小程序 AppSecret>
PHONE_PEPPER=<自定义 pepper，不要用默认值>
TOKEN_PEPPER=<自定义 pepper，不要用默认值>
```

生成 JWT_SECRET：

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2.4 启动服务

```bash
docker compose up -d
```

查看日志确认启动成功：

```bash
docker compose logs backend --tail 20
```

### 2.5 运行数据库迁移

```bash
docker compose exec backend alembic upgrade head
```

### 2.6 灌入种子数据

```bash
docker compose exec backend python scripts/seed_full_demo.py
```

### 2.7 Nginx 反向代理

在服务器已有的 Nginx 配置中添加（`/etc/nginx/sites-enabled/danke`）：

```nginx
# 后端 API
location /v1/ {
    proxy_pass http://127.0.0.1:8000/v1/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
    proxy_read_timeout 60s;
}

# 健康检查
location /health {
    proxy_pass http://127.0.0.1:8000/health;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
}
```

重载 Nginx：

```bash
sudo nginx -t && sudo nginx -s reload
```

### 2.8 验证

```bash
# 健康检查
curl https://88bill99.top/health

# API 测试（需先获取 JWT）
curl https://88bill99.top/v1/api/parent/children \
  -H "Authorization: Bearer <access_token>"
```

---

## 三、Docker Compose 服务说明

```yaml
services:
  db:       # PostgreSQL 16，端口 5432
  backend:  # FastAPI + uvicorn，端口 8000，单 worker
```

- 数据持久化：PostgreSQL 数据卷 `pgdata`
- 健康检查：`pg_isready -U parent -d parent_db`，每 5 秒一次
- 后端依赖 db 健康检查通过后才启动

---

## 四、常用运维命令

```bash
cd ~/danke_robot/cloud/backend

# 查看服务状态
docker compose ps

# 查看日志（实时）
docker compose logs -f backend

# 重启后端
docker compose restart backend

# 重启全部
docker compose restart

# 停止
docker compose down

# 更新代码后重新构建
git pull
docker compose build backend
docker compose up -d
alembic upgrade head
```

---

## 五、故障排查

| 现象 | 可能原因 | 处理 |
|------|---------|------|
| `docker compose up -d` 失败 | 端口 5432 或 8000 被占用 | `lsof -i :5432` 查看，修改 docker-compose.yml 端口映射 |
| 后端启动后立刻退出 | 数据库连接失败 | 检查 DATABASE_URL 中 host 是否为 `db`（容器内 DNS） |
| `alembic upgrade head` 报错 | 数据库未就绪 | 等待 `docker compose ps db` 显示 healthy |
| API 返回 503 | 微信未配置 | 确认 .env 中 WX_APPID 和 WX_SECRET 已填写 |
| API 返回 500 | 查看日志 | `docker compose logs backend --tail 50` |
| 前端跨域报错 | CORS 未限制 | 开发环境已放开 `*`，生产需在 cors.py 中配置具体域名 |

---

## 六、目录说明

```
cloud/backend/
├── app/                    # 应用代码
│   ├── auth/               # 认证（JWT 签发/校验/刷新）
│   ├── car/                # 小车端 API
│   ├── models/             # ORM 模型（15 张表）
│   ├── parent/             # 家长端 API（15 个模块）
│   │   ├── behavior/       # 行为分析
│   │   ├── children/       # 孩子管理
│   │   ├── config/         # 学习配置
│   │   ├── dashboard/      # 今日大盘
│   │   ├── device/         # 设备管理
│   │   ├── dispatch/       # 任务派发
│   │   ├── files/          # 文件服务
│   │   ├── goal/           # 学习目标
│   │   ├── messages/       # 家长消息
│   │   ├── navigation/     # 远程遥控
│   │   ├── notifications/  # 通知设置+中心
│   │   ├── online/         # 在线状态
│   │   ├── reports/        # 学习报告
│   │   └── usage/          # 使用时长
│   ├── middleware/          # CORS / 错误处理 / Request ID
│   ├── schemas/            # 公共响应封装
│   └── telemetry/          # 遥测事件
├── alembic/                # 数据库迁移（18 个版本）
├── scripts/                # 种子数据脚本
├── tests/                  # 集成测试
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```
