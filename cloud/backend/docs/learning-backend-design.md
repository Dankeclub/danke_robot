# 学习乐园后端实现说明

- **状态**：草案，配合《车机学习与互动 API 设计》使用；等待用户批准后才允许开发
- **读者**：产品、后端、运维、测试、数据与家长端开发人员
- **对应车机 API 前缀**：`/v1/api/car`
- **业务时区**：`Asia/Shanghai`

> 本文描述服务端内部职责、数据边界和可配置项；它不替代车机 API 文档，也不要求车机了解数据库或任务生成细节。REST 契约以 `docs/api/car-api-design.md` 和 `docs/api/car-openapi.yaml` 为准。

---

## 1. 目标与范围

### 1.1 目标

为固定绑定到一个孩子的车机提供：

1. 六类学习内容与今日任务；
2. 家长可调整、孩子不可调整的学习配置；
3. 严格最小重复时间下的不可变内容批次；
4. 科学、数学、英语、诗词、音乐、益智六类学习完成判定；
5. ASR 后的儿童安全聊天；
6. 轻量家长消息、孩子预设文字/语音回复；
7. REST、SSE、WebSocket 与离线可补传的学习数据；
8. 可追踪、可观测、可清理的儿童数据处理链路。

### 1.2 明确不做

第一期不做：

- 问答百宝箱；
- 家长端自由文字与孩子自由文字双向聊天；
- 家长消息已读/未读、撤回、确认、未读数；
- 孩子回复家长语音的 ASR、转写或文字展示；
- 英语跟读录音、发音评分；
- AI 自动调整学习难度；
- 排名、考试防作弊、高价值积分或奖励；
- 按星期、节假日、时段的复杂任务编排；
- 离线作业、拍照打卡、家长审批任务。

---

## 2. 推荐技术架构

### 2.1 运行栈

按项目约束采用：

- Python 3.11+；
- FastAPI，异步路由；
- SQLAlchemy Async ORM；
- PostgreSQL + psycopg3；
- Redis：限流、幂等短期缓存、WebSocket 会话/发布订阅、短期锁；
- S3 兼容对象存储：学习素材、私有录音；
- aiohttp：调用 ASR、LLM、安全审核等外部服务；
- APScheduler：清理、补偿、任务预生成等异步定时工作；
- `asyncio.TaskGroup`：并行执行不互相依赖的 I/O；
- OpenTelemetry / 结构化日志：请求与事件全链路追踪。

### 2.2 服务边界

建议先采用模块化单体，不急于拆成独立微服务：

```text
API Gateway / FastAPI
├── auth               令牌校验、设备/孩子解析
├── learning           会话、批次、内容选择、完成聚合
├── task               今日任务与配置快照
├── telemetry          学习事件接收与幂等处理
├── files              上传初始化、确认、私有访问、清理
├── chat               ASR、会话、LLM、安全审核、SSE
├── parent_messages    消息读取、预设/语音回复
└── realtime           WebSocket 连接、事件推送
```

拆分条件：单个模块的吞吐、故障隔离、团队边界或外部依赖明显超过模块化单体可承受范围时，再将 `chat`、`telemetry`、`realtime` 优先独立。

### 2.3 关键外部依赖

```text
PostgreSQL   权威业务数据、快照、事件去重记录
Redis        短期幂等、分布式锁、速率限制、WS Pub/Sub
对象存储      录音与内容媒体
ASR 服务      仅聊天语音识别
LLM 服务      蛋仔文字回答
安全审核      聊天输入、模型输出儿童安全检查
CDN          公共学习图片/音频分发（可选）
```

任何外部依赖不可用时，核心学习数据不能丢失；应返回可恢复错误、保存可重试状态，并记录 `request_id`。

### 2.4 后端模块与车机 API 对应关系

| 后端模块 | 负责接口/协议 | 主要责任 |
| --- | --- | --- |
| `auth` | `/v1/api/car/auth/login`、`/auth/token/refresh`、`/auth/logout`、WS 首包鉴权 | 手机号登录、设备绑定校验、JWT/refresh token、权限 scope |
| `learning` | `/learning/park`、`/learning/{module}/sessions`、`/learning/{module}/sessions/{session_id}/batches` | 学习首页、会话、批次、内容选择、配置快照 |
| `task` | `/today-tasks`、`/today-tasks/{task_id}`、`/today-tasks/{task_id}/claim` | 今日任务生成、领取、过期、任务快照 |
| `telemetry` | `/telemetry/events:batch`、`/telemetry/sessions/{session_id}/complete`、`/summary` | 事件幂等、完成判定、正确率、错题、时长聚合 |
| `files` | `/files/uploads`、`/files/uploads/{upload_id}/complete`、`/files/{file_id}/access` | 预签名上传、文件确认、私有访问、清理 |
| `chat` | `/asr/transcriptions`、`/chat/sessions`、`/chat/sessions/{session_id}/messages`、`/chat/completions` | ASR、每日会话、历史校验、安全审核、SSE |
| `parent_messages` | `/parent-messages`、`/parent-messages/{message_id}/replies` | 家长消息拉取、预设回复、语音回复 |
| `realtime` | `/ws` | 弹窗、页面跳转、家长消息刷新、今日任务刷新 |

研发拆任务时按上表划分包/目录、路由和服务类，避免一个路由直接跨多个领域写数据库。

---

## 3. 身份、设备绑定与权限

### 3.1 绑定关系

```text
车机 device
  → 固定绑定 child
  → child 属于 family
```

车机令牌只拥有当前设备和孩子所需的范围，例如：

```text
car.learning.read
car.learning.write
car.chat
car.messages
car.files
car.realtime
```

### 3.2 手机号登录、OAuth2/JWT 与绑定校验

车机第一期按 API 文档采用轻量登录：登录页只填写家长手机号。后端根据手机号查找已绑定的家庭与默认孩子，再结合设备信息完成车机登录并签发 JWT。

```text
POST /v1/api/car/auth/login(phone, device)
→ 查找 parent_phone
→ 找到 family 和默认 child
→ 校验或创建 device_binding
→ 写入 refresh_token 记录
→ 返回 access_token + refresh_token + child_profile
```

建议登录相关表：

```text
parent_account
- id
- phone_e164 / phone_hash
- phone_masked
- status

family_child
- family_id
- child_id
- is_default_for_car

device_binding
- device_id
- child_id
- family_id
- status
- first_bound_at
- last_login_at
- app_version

refresh_token
- id
- token_hash
- device_id
- child_id
- family_id
- expires_at
- revoked_at
- rotated_from_id
```

建议：

| 项 | 推荐初值 |
| --- | --- |
| access token 有效期 | 120 分钟，与车机 API 示例 `expires_in=7200` 对齐 |
| refresh token 有效期 | 30 天 |
| refresh token | 轮换并可撤销，只存 hash |
| JWT 算法 | ES256 或 RS256 |
| audience | `children-car-api` |
| issuer | 后端环境固定值，如 `children-api-prod` |

JWT 仅放不敏感、必要的声明；`child_id`、`family_id` 优先通过服务端绑定表解析，避免暴露或造成令牌长期耦合。

手机号直登的安全边界：

- 仅允许已存在绑定关系的手机号登录，未绑定返回 `phone_not_bound`。
- 必须限制手机号登录频率，防止撞库和枚举。
- 必须校验 `device_id`、设备状态和绑定状态；生产环境建议打开设备白名单或首次绑定审批。
- 所有登录日志只记录脱敏手机号和脱敏设备 ID。
- 若后续上正式公网，建议升级为“手机号 + 验证码”或“家长端扫码授权”；车机 API 路径可保持不变，只扩展登录流程。

### 3.3 权限校验原则

- 所有车机路由统一从令牌解析孩子，不允许请求体或 URL 指定孩子。
- 资源查询必须额外验证资源属于当前孩子/设备。
- 家长端接口与车机端分离；家长可管理多个孩子，因此家长端可携带受权限约束的 `child_id`。
- 访问私有文件时检查 `file_id` 的归属和用途。

---

## 4. 学习配置与今日任务

### 4.1 默认配置与家长配置

每个孩子每个模块都有一份“当前有效配置”。首次绑定时从系统默认配置复制；家长可以修改：

```text
enabled
difficulty 或 category
batch_size
min_repeat_interval_seconds
```

孩子只能读取配置快照，不能修改。

建议配置表核心字段：

```text
child_learning_config
- id
- child_id
- module
- enabled
- difficulty (nullable)
- category (nullable)
- batch_size
- min_repeat_interval_seconds
- config_version
- updated_at
- updated_by_parent_id
```

唯一约束：

```text
UNIQUE(child_id, module)
```

### 4.1.1 模块配置枚举与建议默认值

以下是服务端种子配置和家长端配置页都必须使用的稳定枚举。车机 API 只读取这些配置的快照，不允许孩子端修改。

| 模块 | 字段 | 稳定枚举值 | 中文标签 | 建议默认 |
| --- | --- | --- | --- | --- |
| 科学探索 `science` | `difficulty` | `beginner` / `intermediate` / `advanced` | 初级 / 中级 / 高级 | `beginner` |
| 数学妙算 `math` | `difficulty` | `within_10_add_subtract` / `within_10_multiply_divide` / `two_digit_add_subtract` / `two_digit_multiply_divide` / `three_digit_four_operations` / `mixed_four_operations` | 十以内加减法 / 十以内乘除法 / 两位数加减法 / 两位数乘除法 / 三位数加减乘除法 / 四则混合运算 | `within_10_add_subtract` |
| 英语乐园 `english` | `difficulty` | `grade_3` / `grade_4` / `grade_5` / `grade_6` | 三年级 / 四年级 / 五年级 / 六年级 | `grade_3` |
| 诗词儿歌 `poems` | `difficulty` | `enlightenment` / `beginner` / `intermediate` / `advanced` | 启蒙 / 初级 / 中级 / 高级 | `enlightenment` |
| 音乐律动 `music` | `category` | `children_song` / `popular_music` / `classical_music` / `classic_music` / `patriotic_music` / `mixed` | 儿歌 / 流行 / 古典 / 经典 / 爱国 / 混合 | `children_song` |
| 益智问答 `quiz` | `difficulty` | `beginner` / `intermediate` / `advanced` | 初级 / 中级 / 高级 | `beginner` |

建议默认题量与最小重复时间：

| 模块 | 默认 `batch_size` | 默认 `min_repeat_interval_seconds` |
| --- | ---: | ---: |
| `science` | 3 | 604800 |
| `math` | 10 | 604800 |
| `english` | 8 | 604800 |
| `poems` | 2 | 604800 |
| `music` | 5 | 604800 |
| `quiz` | 10 | 604800 |

这些值作为系统种子配置，可由运营或家长端配置覆盖；接口和代码不要把它们写死在前端。

### 4.2 快照规则

家长修改不会改变已产生的数据：

```text
当前有效配置改变
→ 新建自由学习会话使用新配置
→ 尚未生成的新今日任务使用新配置
→ 已生成今日任务保留旧快照
→ 已创建内容批次永久保留旧快照
```

今日任务和学习会话分别持有 `config_version` 与结构化 `config_snapshot`，以便历史统计可解释、内容可复现。

### 4.3 今日任务生成

每天按后端 `Asia/Shanghai` 的业务日期生成。实现可选择“首次请求按需生成 + 唯一约束”或“定时预生成 + 请求兜底”，对车机 API 无影响。

轻量一期建议：

```text
GET 今日任务时 ensure_daily_tasks(child, business_date)
```

用数据库唯一约束防止重复：

```text
UNIQUE(child_id, business_date, module)
```

每个 `enabled=true` 模块生成一个任务；全部关闭则当天没有今日任务，模块仍可自由学习。

### 4.4 状态与过期

```text
assigned → claimed → in_progress → completed
                         └──────→ expired
```

- `claim` 是状态变更，不创建批次。
- 创建第一个任务会话/批次时转为 `in_progress`。
- 每日次日 `00:00:00+08:00`，未完成任务过期。
- 过期后不允许继续推进任务；已上报的部分学习数据保留。
- 过期后的自由学习允许新建会话。

定时任务负责批量标记过期；所有写接口也必须在事务内二次检查，不能只依赖定时任务。

### 4.5 家长端配置修改的后端规则

家长端配置 API 不出现在车机 API 文档中，但后端需要支持配置写入能力。建议内部规则如下：

1. 家长只能修改自己家庭下孩子的配置；
2. 修改字段限制为 `enabled`、`difficulty/category`、`batch_size`、`min_repeat_interval_seconds`；
3. 每次修改 `config_version + 1`，并写配置审计记录；
4. 已生成今日任务、已创建会话和已创建批次不回写新配置；
5. 新自由学习会话和新生成今日任务读取当前有效配置；
6. `batch_size`、`min_repeat_interval_seconds` 必须受服务端上下限约束，避免家长配置导致内容池长期不可用。

建议保留配置审计表：

```text
child_learning_config_audit
- id
- child_id
- module
- old_config
- new_config
- changed_by_parent_id
- changed_at
- reason (nullable)
```

---

## 5. 内容选择、最小重复时间与幂等

### 5.1 不可变批次

内容不是在“领取任务”时下发，而是在会话内创建批次时选取。

```text
事务成功创建 batch
→ 选中的内容立即视为 issued
→ 写入 issued_at
→ 最小重复时间开始计算
```

车机刷新、重试或重启必须恢复同一个批次，不重新抽题。

建议表：

```text
learning_batch
- id
- session_id
- module
- sequence_no
- config_snapshot
- issued_at
- status

learning_batch_item
- id
- batch_id
- content_id
- content_snapshot JSONB
- item_order
```

`content_snapshot` 是正确性计算和历史展示的唯一依据，题库内容后续修改不影响已学习历史。

### 5.2 严格全量原则

选择内容时过滤：

```text
候选内容未在 min_repeat_interval_seconds 内对同一孩子成功 issued
```

如果可用数量小于 `batch_size`：

- 不返回部分内容；
- 不缩短重复时间；
- 不回退难度；
- 返回 `content_pool_exhausted`；
- 记录库存监控告警。

任务生成阶段可预检查库存，尽量在孩子看到任务前发现问题；创建批次时仍须最终检查，因为并发或内容状态可能变化。

### 5.2.1 六类内容池最低字段

内容管理后台或导入脚本至少要保证以下字段齐全，批次下发时再写入 `content_snapshot`。

| 模块 | 内容表建议 | 必备字段 |
| --- | --- | --- |
| `science` | `science_article` | `id`、`difficulty`、`image_file_id/url`、`title`、`content`、`status` |
| `math` | `math_question` | `id`、`difficulty`、`question`、四个选项、`correct_option_id`、`status` |
| `english` | `english_word` | `id`、`difficulty`、`chinese`、`english`、`phonetic`、`example_sentence`、`audio_file_id/url`、`status` |
| `poems` | `poem_content` | `id`、`difficulty`、`title`、`author`、`dynasty`、`content_text/lines`、`audio_file_id/url`、`follow_reading_required`、`status` |
| `music` | `music_track` | `id`、`category`、`name`、`audio_file_id/url`、`audio_srt_file_id/url`、`duration_ms`、`status` |
| `quiz` | `quiz_question` | `id`、`difficulty`、`question`、四个选项、`correct_option_id`、`status` |

内容选择只从 `status=published` 的内容池中选择。题库/素材更新不得修改历史批次；历史展示和正确性计算只看批次快照。

### 5.3 幂等与并发

- 所有会创建资源或写数据的接口接受 `Idempotency-Key`。
- 幂等记录至少保存 `24` 小时；同键、同请求体返回首次结果；同键、不同请求体返回冲突。
- 创建批次时使用事务 + 行锁或 advisory lock，避免同一会话并发生成两个批次。
- 数据库唯一约束比 Redis 锁更权威；Redis 锁仅用于降低竞争。
- 失败事务不得写入 issued 记录。

### 5.4 关键 API 的事务边界

| API 行为 | 事务内必须完成 | 事务外可异步完成 |
| --- | --- | --- |
| 手机号登录 | 校验手机号绑定、校验设备、写 refresh token hash、更新 `last_login_at` | 登录审计、风控统计 |
| 获取今日任务 | `ensure_daily_tasks` 使用唯一约束生成缺失任务并返回 | 库存预警、任务生成指标 |
| 领取任务 | 检查归属、未过期、状态可领取；写 `claimed_at` | 推送任务刷新 WS |
| 创建学习会话 | 检查任务/导航指令；写 `learning_session` 和配置快照 | 统计活跃会话 |
| 创建批次 | 锁定会话；选内容；写 `learning_batch`、`learning_batch_item`、`content_issue_history` | 内容池指标、缓存预热 |
| 遥测批量上报 | 按 `event_id` 去重；写原始事件；同步投影关键答题记录 | 重算汇总、错题投影、告警 |
| 完成判定 | 读取事件投影和批次快照；更新 session/task 状态 | 推送任务刷新 WS |
| 文件 complete | 校验对象存在、大小、hash、用途；写 `file_object` | 病毒扫描/音频分析（若后续需要） |
| Chat Completions | 校验历史、写用户消息 accepted/streaming 状态 | LLM 流生成、安全审核、最终消息落库 |

原则：孩子学习结果相关的权威数据必须先落库再返回；外部慢依赖不要长时间占用数据库事务。

---

## 6. 六个模块的服务端完成判定

客户端上报的是“发生过什么”；服务端根据会话、批次快照、配置阈值给出“是否完成”。正确率不作为数学/益智的正常完成门槛。

### 6.1 科学探索

完成条件：每篇文章的累计**有效阅读时长**达到配置的 `min_active_read_seconds`。

有效阅读只在以下条件同时满足时累计：

```text
页面可见
应用处于前台
设备未休眠
文章处于当前展示状态
```

`accuracy`、`correct_count`、`wrong_count` 均为 `null`。

### 6.2 数学妙算与益智问答

- 每题四个选项；车机显示 `correct_option_id` 以支持即时学习反馈。
- 上报只接收 `selected_option_id`，忽略客户端的 `is_correct`。
- 服务端从批次题目快照比较答案，生成答题记录和错题记录。
- 选择后锁定；全部题目都有有效答案即完成。
- 答错仍计作已完成，正确率仅用于学习质量统计。

风险：客户端可从下发内容读取正确答案，所以此模式不适合考试、排名、现金/高价值奖励。

### 6.3 英语乐园

每个单词完成条件：

```text
有效学习时长 ≥ min_active_study_seconds
AND
原音唯一播放比例 ≥ required_audio_playback_ratio
```

第一期不做英语录音、ASR 或发音评分。

### 6.4 诗词儿歌

每首诗要求：

```text
有效阅读时长 ≥ min_active_read_seconds
AND
原音唯一播放比例 ≥ required_audio_playback_ratio
AND（仅当 follow_reading_required=true）
已关联有效录音文件
AND
录音时长 ≥ min_recording_duration_seconds
```

诗词录音关系需保存：

```text
file_id
poem_id
session_id
batch_id
task_id (nullable)
duration_ms
recorded_at
```

不做语音评分；只验证上传成功、文件用途、归属、时长和会话关系。

### 6.5 音乐律动

完成依据为唯一有效播放区间覆盖率：

```text
merge(played_ranges) / duration_ms >= required_playback_ratio
```

- 拖动产生的跳跃不直接算播放。
- 相同区间重复播放不能重复累计。
- `accuracy` 为 `null`。

### 6.6 阈值不写死

下面字段应存为模块配置或版本化策略：

```text
min_active_read_seconds
min_active_study_seconds
required_audio_playback_ratio
follow_reading_required
min_recording_duration_seconds
required_playback_ratio
```

历史会话使用创建时快照，避免调高阈值后让旧会话无法完成。

---

## 7. 学习事件、正确率与错题

### 7.1 事件接收

车机通过一个批量接口上传事件。每条事件持有 `event_id`，在数据库建立唯一约束：

```text
UNIQUE(child_id, event_id)
```

事件表至少包括：

```text
learning_event
- id
- child_id
- event_id
- session_id
- batch_id
- module
- event_type
- payload JSONB
- client_occurred_at
- received_at
- processing_status
```

### 7.2 事件处理

在一次批量请求内：

1. 校验令牌、会话、批次、模块和内容归属；
2. 使用 `event_id` 去重；
3. 校验事件字段、时长和时间窗口；
4. 落原始事件；
5. 更新投影数据：答题、阅读、播放区间、录音关联；
6. 重新计算受影响内容/批次的完成情况；
7. 需要时更新今日任务状态。

批量处理允许部分事件成功、部分被拒绝；返回每项结果，前端仅重试可重试失败。

### 7.3 答题与错题

建议答题记录：

```text
answer_record
- session_id
- batch_item_id
- question_snapshot_id
- selected_option_id
- correct_option_id
- is_correct
- answer_duration_ms
- answered_at
```

建议错题记录由答题记录投影产生：

```text
wrong_answer
- child_id
- answer_record_id
- question_snapshot
- selected_option_id
- correct_option_id
- first_wrong_at
- last_wrong_at
```

车机不单独上传“错题”，只上传答案；服务端保证错题和正确率口径一致。

### 7.4 时间与离线数据

车机时钟并非权威。事件应提交：

```text
occurred_at
answer_duration_ms / active_duration_ms
played_ranges_ms
```

服务端还记录 `received_at`，并做合理性校验：

- 时长不能为负或超过配置上限；
- 会话结束/过期后的事件不能推进任务完成；
- 允许短期离线补传已发生的有效学习事件；
- 异常大的时间差记录审计并拒绝或截断。

建议默认允许离线补传窗口 `24` 小时；最终需根据设备网络特征调整。

---

## 8. 文件服务与数据生命周期

### 8.1 上传流程

```text
init upload
→ 返回短期预签名 PUT URL
→ 车机直传对象存储
→ complete
→ 服务端校验对象存在、大小、hash、MIME 和用途
→ 创建 file_id
```

业务记录只保存 `file_id`，不保存临时上传 URL。

### 8.2 文件用途与访问

| 用途 | 存储性质 | 是否 ASR | 访问主体 |
| --- | --- | --- | --- |
| `poem_recording` | 私有 | 否 | 当前孩子、家长/授权后台（若后续开放） |
| `chat_asr` | 私有、短期 | 是 | 后端 ASR 流程；不对家长开放 |
| `parent_message_voice_reply` | 私有 | **否** | 当前孩子、对应家庭家长 |
| 家长发来的音频/图片 | 私有 | 不要求 | 当前孩子、对应家庭家长 |
| 学习素材音频/图片 | 公共 CDN 或受控签名 | 否 | 授权车机 |

### 8.3 清理策略

- 聊天 ASR 原始音频仅用于识别，识别完成后尽快删除，最长保留 `CHAT_ASR_AUDIO_RETENTION_HOURS`。
- 上传初始化未完成的临时对象按 `FILE_UPLOAD_EXPIRE_MINUTES` 清理。
- 文件清理必须先查业务引用，避免删除仍被诗词录音或家长消息使用的文件。
- 删除任务应有审计日志、失败重试与告警。

---

## 9. 蛋仔聊天：按日 Session、ASR 和安全流

### 9.1 每日会话

同一孩子每天一个聊天 Session：

```text
UNIQUE(child_id, business_date)
```

- 业务日期取 `Asia/Shanghai`。
- 每次车机请求发送当天完整 `messages`。
- 数据库消息为权威历史；后端只接受与存储历史完全一致的前缀加一条新的用户消息。
- 跨日 Session 关闭，新日创建新 Session；昨天内容不自动进入模型上下文。
- 当天历史量达到阈值时，后端可拒绝继续，或在后续版本做安全摘要；第一期不自行隐藏压缩逻辑，以保证可解释。

### 9.2 ASR 流程

```text
车机录音
→ file purpose=chat_asr
→ 文件确认
→ /asr/transcriptions
→ 返回最终文本
→ 孩子在输入框确认/修改
→ /chat/completions
```

ASR 失败只影响本次聊天输入，不影响其他学习功能。建议限制格式、时长、大小并对无声/过短文件返回可理解错误。

### 9.3 LLM 与儿童安全

内部链路：

```text
确认后的儿童文本
→ 输入安全检查
→ 构建受控系统上下文 + 数据库权威当天上下文
→ 调用模型流
→ 短句/语义片段缓冲
→ 输出安全检查
→ 发送 Chat Completions 风格 SSE chunk
→ 保存最终 assistant 消息
```

原则：

- 车机不选择模型、提示词、生成参数或安全策略。
- 不直接透传未审核 token。
- 若输入不合规，不调用模型并返回儿童友好提示。
- 若输出片段风险高，替换为安全回答或终止输出。
- 记录安全决策码，不把审核规则或命中内容发给车机。
- SSE 建立后使用 chunk 和 `[DONE]`；建立前使用普通 JSON 错误。

### 9.4 聊天取消与幂等

- 客户端断开后，服务端取消或在安全范围内结束上游生成，不能无限占用连接。
- 用户消息和回答状态可记为 `accepted`、`streaming`、`completed`、`cancelled`、`failed`、`incomplete`。
- 相同 `Idempotency-Key` 不重复创建同一条用户问题或重复调用模型。
- 前端刷新后通过消息列表得到最终持久化状态。

---

## 10. 家长消息（轻量模型）

### 10.1 原则

车机侧仅需获取最近消息和回复。没有：

```text
已读/未读
阅读回执
撤回状态机
过期状态机
未读计数
复杂 cursor 同步
语音转文字
```

家长消息类型：

```text
text
image
audio
task_card
```

孩子回复类型：

```text
preset_text
voice
```

### 10.2 数据关系

```text
parent_message
  └── parent_message_reply (0..n)
```

固定预设文案由服务端枚举校验：

```text
got_it
will_do_now
done
later
thank_you
```

孩子不能自由输入文字。语音回复不做 ASR，也不生成隐式转写文本。

### 10.3 WS 通知

消息发生变化时只推送：

```json
{ "type": "parent_message.refresh", "data": {} }
```

车机重新拉取最近消息。即使 WS 丢失，定时 REST 拉取也保证最终可见。

---

## 11. WebSocket 与实时事件

### 11.1 连接管理

车机连入 `/v1/api/car/ws` 后首包鉴权；服务端校验 JWT 并绑定连接到设备/孩子。

使用 Redis Pub/Sub 或 Streams 将业务事件从 API/任务进程投递给连接管理器。单设备多连接时可允许并存，但应有最大连接数和最旧连接淘汰策略。

### 11.2 事件范围

第一期支持：

```text
notification.popup
navigation.requested
parent_message.refresh
today_task.refresh
```

`navigation.requested` 支持车机本地直接跳转到白名单目标：六个学习页面、蛋仔对话页、家长消息页。服务端不得下发任意 URL、脚本或未登记路由。

学习类跳转可以携带本次自定义题量，但题量不能由车机决定。后端应先创建一条短期有效的跳转指令记录：

```text
navigation_request
- id
- child_id
- destination
- route_key
- module (nullable)
- custom_batch_size (nullable)
- source
- expires_at
- consumed_at (nullable)
- created_at
```

车机收到 WS 后只负责跳转；进入学习页后用 `source=ws_navigation` 和 `navigation_id` 创建学习会话。后端再次校验：

1. `navigation_id` 属于当前孩子；
2. 未过期、未失效；
3. `module` 与请求路径一致；
4. `custom_batch_size` 在允许范围内；
5. 难度或类别仍取当前有效配置，不接受车机传值。

校验通过后，学习会话的 `config_snapshot.batch_size` 使用本次 `custom_batch_size`；其余配置仍来自当前有效配置。若没有自定义题量，则使用普通有效配置的 `batch_size`。

WS 不承载详细家长消息正文、文件 URL 或复杂命令；REST 是最终权威。跳转事件中的标题和题量只用于展示或引导，最终学习内容仍由 REST 会话和批次接口返回。

### 11.3 心跳与补偿

- 建议 30 秒心跳、90 秒断线判定。
- 车机连接、重连、恢复前台后拉取任务和家长消息。
- 每 300 秒 REST 补拉。
- 对需要可靠触达的业务事件保留事件 ID 和 ACK 日志，但不将复杂重放作为第一期阻塞项。

---

## 12. 数据模型概要

建议最小表集合：

```text
parent_account
family_child
device_binding
refresh_token
child_learning_config
child_learning_config_audit
daily_learning_task
navigation_request
learning_session
learning_batch
learning_batch_item
content_issue_history
science_article
math_question
english_word
poem_content
music_track
quiz_question
learning_event
answer_record
wrong_answer
content_progress
file_object
file_upload
chat_session
chat_message
parent_message
parent_message_reply
idempotency_record
realtime_event_audit
```

关键约束：

```text
UNIQUE(parent_account.phone_hash)                       -- 手机号登录查询
UNIQUE(device_binding.device_id)                        -- 设备绑定唯一
UNIQUE(child_id, module)                                -- 每孩子每模块一份有效学习配置
UNIQUE(child_id, business_date, module)                 -- 今日任务
UNIQUE(child_id, business_date)                         -- 每日聊天 Session
UNIQUE(child_id, event_id)                              -- 学习事件去重
INDEX(child_id, expires_at)                             -- WS 跳转指令校验与清理
UNIQUE(scope, idempotency_key)                          -- HTTP 幂等
UNIQUE(session_id, sequence_no)                         -- 会话批次顺序
```

敏感内容（令牌、外部密钥、原始音频元数据）需要加密、脱敏日志和最小权限访问。

---

## 13. 定时任务与补偿任务

APScheduler 任务建议：

| 任务 | 建议频率 | 责任 |
| --- | --- | --- |
| 标记过期今日任务 | 每分钟或跨日批处理 | 保持 `expired` 状态 |
| 按需任务生成兜底检查 | 定时 + 请求路径 | 避免任务缺失 |
| 清理过期上传 | 每 10 分钟 | 删除未完成临时对象 |
| 清理聊天 ASR 音频 | 每 10 分钟 | 最短保留后删除 |
| 清理已过期签名记录/幂等记录 | 每小时 | 控制存储增长 |
| 事件投影重算/失败重试 | 每几分钟 | 保证遥测最终一致 |
| 内容池库存监控 | 每小时 | 预警 `content_pool_exhausted` |

定时任务必须可重入、幂等、可观测，不能依赖单实例内存状态。

---

## 14. 可观测性、审计与安全

### 14.1 日志与追踪

每个 HTTP 请求生成或透传 `X-Request-ID`；关联：

```text
request_id
idempotency_key
device_id（脱敏）
child internal id（不写入普通业务日志）
session_id / batch_id / task_id
chat_session_id
external provider request id
```

禁止在普通日志中输出：JWT、refresh token、完整儿童聊天内容、聊天原始音频 URL、家长语音 URL。

### 14.2 指标

至少监控：

```text
HTTP 成功率、P95/P99 延迟
SSE 首字节时间、生成完成率、安全拦截率
ASR 成功率与耗时
内容池不足次数
批次创建幂等命中率
学习事件拒绝/重复率
WS 在线连接数、断线率、推送失败率
对象存储上传确认失败率
任务过期量和完成率
```

### 14.3 限流建议

按设备/孩子/令牌联合限制：

```text
聊天发起频率
ASR 请求频率与每日音频总时长
文件上传并发与大小
学习事件批量大小与每分钟数量
WebSocket 并发连接数
```

具体阈值放配置，不固化在代码。

---

## 15. 关键配置变量

| 变量 | 推荐初值 | 说明 |
| --- | ---: | --- |
| `BUSINESS_TIMEZONE` | `Asia/Shanghai` | 任务与聊天业务日依据 |
| `AUTH_ACCESS_TOKEN_TTL_SECONDS` | `7200` | JWT 有效期，与车机 API `expires_in` 对齐 |
| `AUTH_REFRESH_TOKEN_TTL_SECONDS` | `2592000` | 刷新令牌有效期，30 天 |
| `AUTH_PHONE_LOGIN_RATE_LIMIT_PER_MINUTE` | `5` | 单手机号/设备登录限流建议 |
| `AUTH_DEVICE_BINDING_REQUIRED` | `true` | 是否强制设备绑定校验 |
| `SYSTEM_DEFAULT_MIN_REPEAT_INTERVAL_SECONDS` | `604800` | 默认最小重复时间，7 天 |
| `IDEMPOTENCY_TTL_HOURS` | `24` | 幂等记录保存时长 |
| `UNFINISHED_SESSION_RECOVERY_HOURS` | `24` | 未完成会话恢复窗口 |
| `PARENT_MESSAGE_LIST_LIMIT` | `50` | 车机一次拉取最近消息数 |
| `PARENT_MESSAGE_POLL_INTERVAL_SECONDS` | `300` | REST 补拉间隔 |
| `WS_HEARTBEAT_INTERVAL_SECONDS` | `30` | WS 心跳 |
| `WS_DISCONNECT_TIMEOUT_SECONDS` | `90` | WS 断线判定 |
| `CHAT_DAILY_MAX_MESSAGES` | `100` | 当日聊天消息上限 |
| `CHAT_DAILY_MAX_CONTEXT_CHARS` | `30000` | 当日模型上下文文本上限 |
| `CHAT_ASR_AUDIO_RETENTION_HOURS` | `24` | 聊天音频最长保留 |
| `FILE_UPLOAD_EXPIRE_MINUTES` | `30` | 上传 URL 与临时对象有效期 |
| `OFFLINE_EVENT_ACCEPT_WINDOW_HOURS` | `24` | 离线学习事件可补传窗口 |
| `MAX_WS_CONNECTIONS_PER_DEVICE` | `2` | 单车机 WS 上限 |

模块阈值（阅读、播放、录音等）应按 `module + config_version` 管理，而不是只有全局环境变量。

---

## 16. 已知风险与缓解

| 风险 | 原因 | 缓解 |
| --- | --- | --- |
| 正确答案可被篡改客户端读取 | 学习端下发 `correct_option_id` | 只用于学习反馈；不用于考试和高价值奖励 |
| 内容池不足导致任务不可用 | 严格最小重复时间 + 题库数量不足 | 预检查、库存监控、返回明确错误，不部分下发 |
| 午夜切换打断任务 | 任务严格按业务日过期 | 前端提前提醒；过期后保留学习数据，允许自由学习 |
| 聊天首字节变慢 | 输出需缓冲并审核 | 使用短句缓冲；监控首字节耗时；必要时优化审核链路 |
| 客户端伪造时长或历史 | 车机环境不完全可信 | 服务端快照、事件校验、权威聊天历史、范围校验 |
| 儿童音频敏感 | 原始录音涉及未成年人 | 私有存储、最短保留、鉴权访问、删除任务、日志脱敏 |
| WS 通知丢失 | 车机网络不稳定 | REST 作为权威，启动/重连/定时补拉 |
| 配置修改和已生成任务冲突 | 家长希望立即生效 | 明确“新任务/新会话生效，已有快照不变” |

---

## 17. 开发前仍需验证的工程项

以下不是产品需求未定，而是实现前需要在技术选型/联调中验证的项目：

1. 对象存储是否支持所需的预签名 PUT、私有下载 URL 与生命周期规则；
2. ASR 和 LLM 服务的并发、超时、未成年人安全能力与数据处理协议；
3. 车机浏览器/运行时对 SSE、WebSocket、音频格式和预签名上传的兼容性；
4. 现有前端是否能可靠获取页面可见性、后台状态和音频播放区间；
5. PostgreSQL JSONB、索引和遥测事件吞吐是否满足预计规模；
6. 家长端与车机端的文件授权关系、数据保留政策和隐私合规要求。
