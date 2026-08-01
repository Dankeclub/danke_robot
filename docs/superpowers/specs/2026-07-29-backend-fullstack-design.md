# 蛋壳机器人后端全栈开发方案

> **状态**：已批准
> **日期**：2026-07-29
> **作者**：贝尔 / Doctor Bill

## 一、贝尔的架构审查

### 确认可行

| 项目 | 判断 |
|------|------|
| 模块化单体 | 正确选择。车端和家长端共享同一批数据表（Child、Family、DeviceBinding、LearningEvent），拆成微服务会增加不必要的复杂度。 |
| `/v1/api/car` + `/v1/api/parent` 双前缀 | URL 层面清晰区分两端，代码通过 `app/car/` 和 `app/parent/` 分离。 |
| auth 放顶层 `app/auth/` | 车端和家长端共用同一套 JWT 签发/验证，不归属任何一端。 |
| telemetry 放顶层 `app/telemetry/` | 车端写入事件，家长端读取事件（看板/报告），共享数据层。 |

### 风险缓解

| 风险 | 缓解 |
|------|------|
| `app/models/` 会膨胀到 20+ 个模型 | 按领域拆分文件（learning.py, task.py, config.py, content.py, answer.py） |
| 无内容数据 | 种子脚本插入少量测试数据（每模块 5-10 条） |
| 现有接口与 OpenAPI YAML 不一致 | Phase 1.7 / 2.5 修正对齐 |

## 二、目录结构（最终形态）

```
cloud/backend/app/
├── main.py, router.py, config.py, db.py
├── models/           # 共享数据模型（按领域拆分）
│   ├── base.py, family.py, child.py, parent.py, parent_child.py, device_binding.py
│   ├── learning.py   # LearningSession, LearningBatch, BatchItem [新建]
│   ├── task.py       # DailyTask [新建]
│   ├── config.py     # LearningModuleConfig, ConfigAudit [新建]
│   ├── content.py    # 6个内容表 [新建]
│   └── answer.py     # AnswerRecord, WrongAnswer [新建]
├── auth/             # 认证（已建）
├── telemetry/        # 遥测（共享，扩展）
├── car/              # 车端业务 [新建]
│   ├── learning/     # 学习乐园
│   └── task/         # 今日任务
├── parent/           # 家长端业务 [新建]
│   ├── children/     # 孩子管理
│   ├── device/       # 设备管理
│   ├── config/       # 学习配置
│   └── dashboard/    # 今日大盘
├── schemas/          # 统一响应（已建）
└── middleware/        # 中间件（已建）
```

## 三、分阶段计划

### Phase 1: 车端学习链路

**分支**: `feature/car-learning-chain`
**目标**: 车机完成「学习乐园首页 -> 拿任务 -> 开始学习 -> 拿题目 -> 上报答案 -> 完成判定」

| # | 任务 | 新建模型 |
|---|------|---------|
| 1.1 | 学习配置+内容模型+种子数据 | LearningModuleConfig, 6个内容表 |
| 1.2 | 学习会话+批次模型 | LearningSession, LearningBatch, BatchItem |
| 1.3 | 今日任务模型 | DailyTask |
| 1.4 | 车端 learning router + service | - |
| 1.5 | 车端 task router + service | - |
| 1.6 | 扩展 telemetry（答案判定+完成+汇总） | AnswerRecord, WrongAnswer |
| 1.7 | 修正 car auth 接口对齐 OpenAPI | - |
| 1.8 | 集成测试 + 验证 | - |

### Phase 2: 家长端核心

**分支**: `feature/parent-backend-core`
**目标**: 家长完成「查看孩子 -> 调整配置 -> 查看学习情况」

| # | 任务 |
|---|------|
| 2.1 | 孩子管理 API |
| 2.2 | 设备管理 API |
| 2.3 | 学习配置读写 API |
| 2.4 | 今日大盘 API |
| 2.5 | 修正 parent auth 接口对齐 OpenAPI |
| 2.6 | 集成测试 + 验证 |

### Phase 3: 高级功能（后续按需拆分）

聊天、家长消息、文件服务、行为分析、报告、通知、WebSocket

## 四、会话续接 Prompt

Phase 1:
```
继续 danke_robot 项目的 Phase 1 车端学习链路开发。
分支: feature/car-learning-chain
设计文档: docs/superpowers/specs/2026-07-29-backend-fullstack-design.md
进度文件: .superpowers/sdd/2026-07-29-backend-fullstack/progress.md
请先读取进度文件了解当前状态，然后继续开发。
```

Phase 2:
```
继续 danke_robot 项目的 Phase 2 家长端核心开发。
分支: feature/parent-backend-core
设计文档: docs/superpowers/specs/2026-07-29-backend-fullstack-design.md
进度文件: .superpowers/sdd/2026-07-29-backend-fullstack/progress.md
请先读取进度文件了解当前状态，然后继续开发。
```
