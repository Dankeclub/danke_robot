# 蛋壳/Danke — AI 陪伴机器人系统

基于端云协同的多模态儿童行为感知与移动早教智能体系统。

```text
┌──────────────────────────────────────────────────────────────────┐
│                         ☁️  云端 (cloud/)                         │
│                                                                  │
│   ┌─────────────┐              ┌──────────────────────┐         │
│   │  backend/   │              │  streaming/          │         │
│   │  业务 API   │◀── REST ────▶│  ZLMediaKit + Nginx  │         │
│   │  FastAPI    │              │  RTMP→HTTP-FLV       │         │
│   └──────┬──────┘              └──────────┬───────────┘         │
│          │  ▲                              ▲                     │
│          │  │ WebSocket / REST              │ RTMP 推流           │
│          │  │                              │                     │
├──────────┼──┼──────────────────────────────┼─────────────────────┤
│          │  │        📱 家长端               │                    │
│          │  │    parent/                    │                    │
│          │  │    ┌──────────────────┐       │                    │
│          │  └───▶│  微信小程序       │       │                    │
│          │       │  · 实时视频       │◀──────┘                    │
│          │       │  · 行为看板       │                            │
│          │       │  · AI 周报       │                            │
│          │       │  · 设备管理       │                            │
│          │       └──────────────────┘                            │
│          │                                                        │
├──────────┼───────────────────────────────────────────────────────┤
│          │          🚗 小车端 · 边缘端 (car/)                     │
│          │                                                        │
│   ┌──────┴──────────────────────────────────────────────────┐    │
│   │  🖥️  screen/         车载触摸屏 (1024×600) · Vue 3     │    │
│   │                      6 种学习模式交互界面                │    │
│   ├─────────────────────────────────────────────────────────┤    │
│   │  🧠 behavioral/      行为检测 · SC171 NPU               │    │
│   │  运行在：SC171 V3 (8×Cortex@2.7GHz, 13 TOPS NPU)       │    │
│   │  MediaPipe + YOLOv8  端侧推理闭环                       │    │
│   ├─────────────────────────────────────────────────────────┤    │
│   │  👁️  vision/          视觉感知 · 树莓派                 │    │
│   │  YOLOv8 人体检测 + 姿态识别                             │    │
│   ├─────────────────────────────────────────────────────────┤    │
│   │  🔧 motion-control/  运动控制 · 麦轮底盘                │    │
│   │  ├── v1.0/           WebSocket 远程控制                 │    │
│   │  └── v2.0/           改进版                             │    │
│   └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📂 目录结构

```
danke_project/
│
├── car/                         # 🚗 小车端 · 边缘端 (SC171 + 树莓派)
│   ├── screen/                  #   🖥️  车载触摸屏 Vue 3 应用 (1024×600)
│   ├── behavioral/              #   🧠  行为检测 (SC171 NPU · 端侧推理)
│   ├── vision/                  #   👁️  视觉感知 (树莓派 · YOLOv8)
│   └── motion-control/          #   🔧  运动控制 (麦轮底盘)
│       ├── v1.0/                #       版本 1.0
│       └── v2.0/                #       版本 2.0
│
├── cloud/                       # ☁️ 云端服务 (88bill99.top)
│   ├── backend/                 #   业务后端 API (FastAPI + SQLAlchemy)
│   │   └── docs/                #     API 设计文档 (OpenAPI)
│   └── streaming/               #   📡 推流配置 (ZLMediaKit + Nginx)
│
├── parent/                      # 👨‍👩‍👧 家长端 · 微信小程序
│
├── docs/                        # 📄 项目文档
│   ├── design/                  #   设计方案 + PRD
│   └── archive/                 #   历史版本归档
│
└── README.md                    # 📋 本文件
```

---

## 🔄 系统间数据流

```text
┌────────────┐                          ┌────────────┐
│  摄像头     │── RTSP/帧 ──▶  behavioral │── 行为标签 ▶──┐
│  + 麦克风   │                (SC171)    │               │
└────────────┘                          │               │
                                        │   motion-    │     ┌──────────┐
┌────────────┐     WebSocket            │   control    │     │  cloud/  │
│  parent/   │◀──────────┼──────────────│   (麦轮)     │     │  backend │
│  家长端     │                          │              │     │          │
│            │                          │   screen/    │     │  ┌─行为DB│
│  实时视频  │◀── HTTP-FLV ──────────── │   (Vue)      │     │  ├─用户DB│
│  看板/报告 │                          │              │     │  └─设备DB│
└─────┬──────┘                          └──────────────┘     └────┬─────┘
      │                                                          │
      └───────── REST API ───────────────────────────────────────┘
            (孩子信息、行为记录、学习报告、AI 对话)
```

---

## 🔗 各模块关系一览

| 从 → 到 | 通道 | 说明 |
|----------|------|------|
| 摄像头 → `car/behavioral` | RTSP 视频流 | 行为检测模块抽帧推理 |
| `car/behavioral` → `cloud/backend` | WebSocket | 上传行为标签+置信度 |
| `car/behavioral` → `car/screen` | 本地 | 行为事件驱动 UI 反馈 |
| `car/behavioral` → `car/motion-control` | 本地 | 行为触发跟随/提醒 |
| `car/screen` → `cloud/streaming` | RTMP | go2rtc/ffmpeg 推流 |
| `cloud/streaming` → `parent/` | HTTP-FLV | 小程序实时视频 |
| `parent/` → `cloud/backend` | REST API | 数据查询、AI 对话 |
| `car/motion-control` → `cloud/backend` | WebSocket | 远程控制指令转发 |

---

## 🚀 快速开始

### 小车屏幕 (`car/screen/`)

```bash
cd car/screen
npm install
npm run dev          # 开发 → http://localhost:5173
```

### 行为检测 (`car/behavioral/`)

```bash
cd car/behavioral
pip install -r requirements.txt
python -m behavioral.main
```

> **注意：** 需要 MediaPipe 模型文件（`models/` 目录下）和 YOLOv8 模型。

### 后端 (`cloud/backend/`)

```bash
cd cloud/backend
pip install -e .
alembic upgrade head
uvicorn app:app --reload
```

### 家长端 (`parent/`)

用微信开发者工具打开 `parent/` 目录，配置 AppID 后即可预览。

---

## 🚫 .gitignore 说明

| 文件 | 作用范围 |
|------|----------|
| `.gitignore` (项目根) | 全局：Python/Node 虚拟环境、IDE 配置 (`.vscode/` `.idea/`)、密钥 (`.env`)、日志 (`*.log`)、`.claude/`、`.superpowers/`、`dist/` |
| `car/behavioral/.gitignore` | 行为检测模块：`*.pt` `*.task` `models/` 不入库（模型文件过大，需自行下载） |
| `cloud/backend/.gitignore` | 后端模块：Python 常规忽略项 |

> ⚠️ **注意**：`car/behavioral/.gitignore` 排除了 `*.pt` 和 `models/`，YOLOv8 和 MediaPipe 模型文件不会被 git 跟踪。如果需要在版本库中保留模型，请修改该文件。

---

## 🏷️ 命名规范

| 前缀 | 含义 |
|------|------|
| `car/` | 运行在小车硬件上（SC171 + 树莓派） |
| `cloud/` | 运行在云服务器上 |
| `parent/` | 家长使用的微信小程序 |
| `docs/` | 不运行的文档/设计稿 |

---

## 📝 设计文档索引

| 文档 | 位置 |
|------|------|
| 家长端 PRD | `docs/design/AI陪伴机器人家长端小程序 PRD.md` |
| 行为分析专项 | `docs/design/行为分析专项.md` |
| 家长端 API | `cloud/backend/docs/parent-api-design.md` |
| 小车 API | `cloud/backend/docs/car-api-design.md` |
| 涂鸦天地设计 | `docs/design/doodle-world-design.md` |
| 前端架构 | `docs/design/frontend-architecture.md` |
