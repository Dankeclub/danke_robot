# 车机学习与互动 API 设计

- **状态**：草案，等待需求方确认后才允许进入开发
- **适用对象**：儿童车机前端、车机网络层、后端 API 开发与测试人员
- **API 前缀**：`/v1/api/car`
- **业务时区**：`Asia/Shanghai`
- **范围**：学习乐园、今日任务、蛋仔聊天、家长消息、文件服务、WebSocket、学习过程数据上报
- **不在范围内**：问答百宝箱、家长管理端配置 API、后台任务生成与数据库实现

> 本文只写车机需要调用或消费的协议。默认配置、家长改配置、任务生成、内容去重、文件清理等服务端内部规则见《学习后端实现说明》。

---

## 1. 基本约定

### 1.1 鉴权与身份

车机登录页提交家长手机号，后端自动关联家长和孩子，随后签发 JWT 访问 API。整体仍按 OAuth2/JWT 的 Bearer Token 思路实现。

```http
Authorization: Bearer <access_token>
```

- 一台车机绑定一个孩子；后端由令牌和设备绑定关系确定孩子与家庭。
- 车机请求**不得**传 `user_id`、`child_id`、`family_id`。
- REST、SSE、WebSocket、文件访问均须鉴权。
- 需要防止重复写入的 POST 请求必须携带 `Idempotency-Key`（UUID 或等价随机唯一值）。

### 1.2 普通 JSON 响应包裹

除聊天 SSE 建立成功后的数据块外，所有接口都使用：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {}
}
```

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `code` | int | 业务状态码；`0` 为成功，非 `0` 为业务失败 |
| `msg` | string | 机器可识别消息；成功固定为 `ok`，失败使用稳定英文码 |
| `data` | object/null | 正文；没有正文时为 `null` |

HTTP 状态仍表达协议层错误：`400` 参数错误、`401` 未认证、`403` 无权限、`404` 不存在、`409` 状态冲突、`422` 校验失败、`429` 限流、`500` 内部错误、`503` 服务暂不可用。

所有响应应返回 `X-Request-ID`，便于问题追踪。

### 1.3 时间、ID、文件 URL

- 业务日期：`YYYY-MM-DD`，以后端 `Asia/Shanghai` 为准。
- 时间：ISO 8601 且带偏移量，如 `2026-07-16T15:20:38+08:00`。
- 所有资源 ID 为不透明字符串；前端不解析 ID 结构。
- `audio_url`、`image_url`、`playback_url` 可能为短期签名 URL；过期后重新请求相关资源或文件访问接口。

### 1.4 稳定枚举

前端逻辑只使用英文值，展示使用对应的 `*_label` 中文字段。

| 模块 | 枚举值 |
| --- | --- |
| 科学探索 `science` | `beginner`、`intermediate`、`advanced` |
| 数学妙算 `math` | `within_10_add_subtract`、`within_10_multiply_divide`、`two_digit_add_subtract`、`two_digit_multiply_divide`、`three_digit_four_operations`、`mixed_four_operations` |
| 英语乐园 `english` | `grade_3`、`grade_4`、`grade_5`、`grade_6` |
| 诗词儿歌 `poems` | `enlightenment`、`beginner`、`intermediate`、`advanced` |
| 音乐律动 `music` | `children_song`、`popular_music`、`classical_music`、`classic_music`、`patriotic_music`、`mixed` |
| 益智问答 `quiz` | `beginner`、`intermediate`、`advanced` |

---

## 1.5 前端页面与接口映射

> 研发落地时先按本表拆前端网络层。每个页面只依赖自己所在行的接口；WS 只负责通知和跳转，页面数据仍以 REST 返回为准。

| 前端页面/功能 | 主要接口 | 触发时机 | 页面拿到的数据 |
| --- | --- | --- | --- |
| 登录页 | `POST /v1/api/car/auth/login`、`POST /v1/api/car/auth/token/refresh`、`POST /v1/api/car/auth/logout` | 输入手机号登录、启动续期、退出登录 | JWT、孩子昵称头像、家长手机号脱敏信息 |
| 学习乐园首页 | `GET /v1/api/car/learning/park` | 进入学习乐园、前台恢复、配置刷新后 | 六个学习入口、难度/类别、题量、最小重复时间、可继续会话 |
| 今日任务页 | `GET /v1/api/car/today-tasks`、`GET /v1/api/car/today-tasks/{task_id}`、`POST /v1/api/car/today-tasks/{task_id}/claim` | 打开今日任务、点任务卡片、领取任务 | 任务状态、进度、到期时间、配置快照 |
| 科学探索页 | `POST /v1/api/car/learning/science/sessions`、`POST /v1/api/car/learning/science/sessions/{session_id}/batches`、生产侧上报接口 | 进入页面、刷新恢复、阅读过程 | 图片、标题、正文、难度、题量、最小重复时间 |
| 数学妙算页 | `POST /v1/api/car/learning/math/sessions`、`POST /v1/api/car/learning/math/sessions/{session_id}/batches`、生产侧上报接口 | 进入页面、答题过程 | 题目、四个选项、正确选项、难度、题量、最小重复时间 |
| 英语乐园页 | `POST /v1/api/car/learning/english/sessions`、`POST /v1/api/car/learning/english/sessions/{session_id}/batches`、生产侧上报接口 | 进入页面、单词学习/播放 | 中文、英文、音标、例句、音频、年级、题量、最小重复时间 |
| 诗词儿歌页 | `POST /v1/api/car/learning/poems/sessions`、`POST /v1/api/car/learning/poems/sessions/{session_id}/batches`、文件服务、生产侧上报接口 | 进入页面、跟读录音上传 | 标题、作者、朝代、正文、音频、难度、题量、最小重复时间 |
| 音乐律动页 | `POST /v1/api/car/learning/music/sessions`、`POST /v1/api/car/learning/music/sessions/{session_id}/batches`、生产侧上报接口 | 进入页面、播放过程 | 歌曲名、类别、音频、SRT、最小重复时间 |
| 益智问答页 | `POST /v1/api/car/learning/quiz/sessions`、`POST /v1/api/car/learning/quiz/sessions/{session_id}/batches`、生产侧上报接口 | 进入页面、答题过程 | 题目、四个选项、正确选项、难度、题量、最小重复时间 |
| 蛋仔对话页 | 文件服务、`POST /v1/api/car/asr/transcriptions`、`POST /v1/api/car/chat/sessions`、`GET /v1/api/car/chat/sessions/{session_id}/messages`、`POST /v1/api/car/chat/completions` | 录音、识别、孩子确认文本、SSE 回复 | 当天会话、当天消息、ASR 文本、流式回答 |
| 家长消息页 | `GET /v1/api/car/parent-messages`、`POST /v1/api/car/parent-messages/{message_id}/replies`、文件服务 | 打开消息页、收到刷新通知、回复消息 | 最近消息、消息内容、已有回复 |
| 全局 WS 通道 | `wss://<host>/v1/api/car/ws` | 登录后常连、重连 | 弹窗、页面跳转、家长消息刷新、今日任务刷新 |

---

# 2. 消费侧 API

## 2.0 登录与令牌

第一期登录按你的要求做轻量：车机登录页只填手机号。后端根据手机号自动找到绑定的家长和孩子，并签发 JWT。后续所有业务接口都不再传 `user_id`、`child_id`、`family_id`。

### 2.0.1 手机号登录

### `POST /v1/api/car/auth/login`

关联前端：**登录页**。

请求头：

```http
Content-Type: application/json
Idempotency-Key: 0cb36a87-9cb6-4971-94e4-5cf20e3f77ab
```

请求体：

```json
{
  "phone": "13800138000",
  "device": {
    "device_id": "car_device_001",
    "device_name": "儿童车机 A",
    "platform": "android_car",
    "app_version": "1.0.0"
  }
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `phone` | string | 是 | 家长手机号；后端用该手机号查找绑定家庭和默认孩子 |
| `device.device_id` | string | 是 | 车机设备唯一标识 |
| `device.device_name` | string | 否 | 设备展示名 |
| `device.platform` | string | 是 | 第一阶段建议固定 `android_car` |
| `device.app_version` | string | 是 | 车机 App 版本，便于灰度和问题定位 |

成功响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "token_type": "Bearer",
    "access_token": "eyJhbGciOi...",
    "expires_in": 7200,
    "refresh_token": "rt_01J...",
    "refresh_expires_in": 2592000,
    "child_profile": {
      "nickname": "小明",
      "avatar_url": "https://..."
    },
    "family_profile": {
      "parent_phone_masked": "138****8000",
      "relationship_label": "妈妈"
    }
  }
}
```

失败示例：

```json
{
  "code": 41001,
  "msg": "phone_not_bound",
  "data": {
    "phone_masked": "138****8000"
  }
}
```

### 2.0.2 刷新令牌

### `POST /v1/api/car/auth/token/refresh`

关联前端：**启动页/全局网络层**。Access Token 过期前或收到 `401` 后调用。

请求体：

```json
{
  "refresh_token": "rt_01J..."
}
```

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "token_type": "Bearer",
    "access_token": "eyJhbGciOi...",
    "expires_in": 7200,
    "refresh_token": "rt_01K...",
    "refresh_expires_in": 2592000
  }
}
```

### 2.0.3 退出登录

### `POST /v1/api/car/auth/logout`

关联前端：**设置页/退出登录按钮**。

请求体：

```json
{
  "refresh_token": "rt_01K..."
}
```

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": null
}
```

## 2.1 学习乐园首页

### `GET /v1/api/car/learning/park`

返回六个模块的入口展示信息、当前有效配置摘要和可恢复的会话提示。车机只展示配置，不能修改配置。

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "modules": [
      {
        "module": "science",
        "module_label": "科学探索",
        "enabled_for_today_task": true,
        "effective_config": {
          "difficulty": "beginner",
          "difficulty_label": "初级",
          "batch_size": 3,
          "min_repeat_interval_seconds": 604800,
          "config_version": 7
        },
        "active_session_id": null
      },
      {
        "module": "music",
        "module_label": "音乐律动",
        "enabled_for_today_task": true,
        "effective_config": {
          "category": "children_song",
          "category_label": "儿歌",
          "batch_size": 5,
          "min_repeat_interval_seconds": 604800,
          "config_version": 4
        },
        "active_session_id": "ls_01J..."
      }
    ]
  }
}
```

`active_session_id` 非空时，前端可展示“继续学习”。

---

## 2.2 今日任务

### 2.2.1 获取今日任务摘要

### `GET /v1/api/car/today-tasks`

首次访问当天任务时，后端可按内部规则生成当天任务；该实现不属于本 API 协议。列表只返回摘要。

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "business_date": "2026-07-16",
    "timezone": "Asia/Shanghai",
    "items": [
      {
        "task_id": "task_01J...",
        "module": "math",
        "module_label": "数学妙算",
        "status": "assigned",
        "title": "今日数学妙算",
        "progress": { "completed_count": 0, "total_count": 10 },
        "expires_at": "2026-07-17T00:00:00+08:00"
      }
    ]
  }
}
```

状态：

```text
assigned → claimed → in_progress → completed
                         └──────→ expired
```

- 每天每模块最多一个任务，全天可有 `0~6` 个任务。
- 次日 `00:00:00+08:00` 未完成任务变为 `expired`，不能再领取或继续。
- 完成后孩子可以继续自由学习；额外学习不再推进已完成任务。

### 2.2.2 获取任务详情

### `GET /v1/api/car/today-tasks/{task_id}`

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "task_id": "task_01J...",
    "module": "math",
    "module_label": "数学妙算",
    "status": "assigned",
    "config_snapshot": {
      "difficulty": "within_10_add_subtract",
      "difficulty_label": "十以内加减法",
      "batch_size": 10,
      "min_repeat_interval_seconds": 604800,
      "config_version": 7
    },
    "progress": {
      "completed_count": 0,
      "total_count": 10,
      "accuracy": null,
      "is_final": false
    },
    "expires_at": "2026-07-17T00:00:00+08:00"
  }
}
```

### 2.2.3 领取任务

### `POST /v1/api/car/today-tasks/{task_id}/claim`

```http
Idempotency-Key: 9c9d7851-1f01-4a09-a2ee-9a9b01b03ca9
```

请求体为空：`{}`。

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "task_id": "task_01J...",
    "status": "claimed",
    "claimed_at": "2026-07-16T09:00:00+08:00"
  }
}
```

领取只改变任务状态；不创建题目、不开始时长、不占用最小重复时间。进入对应学习模块后再创建会话和内容批次。

---

## 2.3 六个学习模块：通用会话规则

六个模块保留独立、清晰的公开路径；后端内部可复用同一套会话、幂等、内容去重逻辑。

### 2.3.1 创建或恢复学习会话

各模块路径：

```http
POST /v1/api/car/learning/science/sessions
POST /v1/api/car/learning/math/sessions
POST /v1/api/car/learning/english/sessions
POST /v1/api/car/learning/poems/sessions
POST /v1/api/car/learning/music/sessions
POST /v1/api/car/learning/quiz/sessions
```

请求：

```json
{
  "source": "today_task",
  "task_id": "task_01J..."
}
```

自由学习：

```json
{
  "source": "free_learning"
}
```

WS 自定义跳转进入学习页：

```json
{
  "source": "ws_navigation",
  "navigation_id": "nav_01J..."
}
```

- `source` 仅可为 `today_task`、`free_learning`、`task_extension`、`ws_navigation`。
- `today_task` 必须携带当天属于当前孩子的 `task_id`。
- `free_learning` 与 `task_extension` 不携带难度、题量、最小重复时间；后端使用有效配置。
- `ws_navigation` 来自服务端通过 WS 下发的自定义跳转；车机只传 `navigation_id`，不传自定义题量或难度。后端根据该 `navigation_id` 校验归属、模块、过期时间和自定义题量。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "session_id": "ls_01J...",
    "module": "math",
    "source": "today_task",
    "task_id": "task_01J...",
    "status": "active",
    "config_snapshot": {
      "difficulty": "within_10_add_subtract",
      "difficulty_label": "十以内加减法",
      "batch_size": 10,
      "min_repeat_interval_seconds": 604800,
      "config_version": 7
    }
  }
}
```

### 2.3.2 创建或恢复内容批次

```http
POST /v1/api/car/learning/science/sessions/{session_id}/batches
POST /v1/api/car/learning/math/sessions/{session_id}/batches
POST /v1/api/car/learning/english/sessions/{session_id}/batches
POST /v1/api/car/learning/poems/sessions/{session_id}/batches
POST /v1/api/car/learning/music/sessions/{session_id}/batches
POST /v1/api/car/learning/quiz/sessions/{session_id}/batches
```

请求体：`{}`，必须带 `Idempotency-Key`。

> 重要：孩子端创建批次时**不传**难度、题量、最小重复时间。后端根据任务快照、家长配置或 WS 跳转指令生成内容；响应中的 `config_snapshot` 明确告诉前端本次实际使用的难度/类别、题量和最小重复时间。

创建成功的批次不可变。刷新、重试或车机重启时，同一幂等请求返回同一批次；内容从批次创建成功时开始计入最小重复时间。所有批次成功响应都包含当前批次的 `config_snapshot`（难度或类别、题量、最小重复时间、`config_version`）。

当内容池无法满足完整数量且不能违反最小重复时间时，返回：

```json
{
  "code": 42001,
  "msg": "content_pool_exhausted",
  "data": {
    "required_count": 10,
    "available_count": 6,
    "min_repeat_interval_seconds": 604800,
    "next_available_at": "2026-07-18T09:00:00+08:00"
  }
}
```

前端不得把该失败解释为孩子完成不足。

### 2.3.3 科学探索批次

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "batch_id": "batch_01J...",
    "session_id": "ls_01J...",
    "module": "science",
    "difficulty": "beginner",
    "difficulty_label": "初级",
    "config_snapshot": {
      "difficulty": "beginner",
      "difficulty_label": "初级",
      "batch_size": 3,
      "min_repeat_interval_seconds": 604800,
      "config_version": 7
    },
    "items": [
      {
        "article_id": "science_001",
        "image_url": "https://...",
        "title": "彩虹是怎么形成的？",
        "content": "当阳光穿过空气中的小水滴时……"
      }
    ]
  }
}
```

完成依据：批次中每篇文章均达到后端配置的有效阅读时长；本模块 `accuracy` 为 `null`。

### 2.3.4 数学妙算批次

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "batch_id": "batch_01J...",
    "session_id": "ls_01J...",
    "module": "math",
    "difficulty": "within_10_add_subtract",
    "difficulty_label": "十以内加减法",
    "config_snapshot": {
      "difficulty": "within_10_add_subtract",
      "difficulty_label": "十以内加减法",
      "batch_size": 10,
      "min_repeat_interval_seconds": 604800,
      "config_version": 7
    },
    "items": [
      {
        "question_id": "math_001",
        "question": "3 + 4 = ?",
        "options": [
          { "option_id": "A", "text": "6" },
          { "option_id": "B", "text": "7" },
          { "option_id": "C", "text": "8" },
          { "option_id": "D", "text": "9" }
        ],
        "correct_option_id": "B"
      }
    ]
  }
}
```

车机可做即时反馈，但上报时只上传 `selected_option_id`；后端以不可变题目快照重新计算正确性。全部题目完成即完成任务，正确率不阻塞完成。

### 2.3.5 英语乐园批次

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "batch_id": "batch_01J...",
    "session_id": "ls_01J...",
    "module": "english",
    "difficulty": "grade_3",
    "difficulty_label": "三年级",
    "config_snapshot": {
      "difficulty": "grade_3",
      "difficulty_label": "三年级",
      "batch_size": 8,
      "min_repeat_interval_seconds": 604800,
      "config_version": 7
    },
    "items": [
      {
        "word_id": "word_001",
        "chinese": "苹果",
        "english": "apple",
        "phonetic": "/ˈæpəl/",
        "example_sentence": "I like red apples.",
        "audio_url": "https://..."
      }
    ]
  }
}
```

完成依据：每个单词达到有效学习时长，并满足原音有效播放比例。第一期不做英语录音和评分。

### 2.3.6 诗词儿歌批次

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "batch_id": "batch_01J...",
    "session_id": "ls_01J...",
    "module": "poems",
    "difficulty": "enlightenment",
    "difficulty_label": "启蒙",
    "config_snapshot": {
      "difficulty": "enlightenment",
      "difficulty_label": "启蒙",
      "batch_size": 2,
      "min_repeat_interval_seconds": 604800,
      "config_version": 7
    },
    "items": [
      {
        "poem_id": "poem_001",
        "title": "静夜思",
        "author": "李白",
        "dynasty": "唐",
        "content_text": "床前明月光，疑是地上霜。举头望明月，低头思故乡。",
        "content_lines": ["床前明月光，疑是地上霜。", "举头望明月，低头思故乡。"],
        "audio_url": "https://...",
        "follow_reading_required": true
      }
    ]
  }
}
```

按下跟读后，录音通过文件服务上传；其关联信息通过生产侧事件 `recording_uploaded` 上报，必须带 `poem_id`。若 `follow_reading_required=true`，有效录音上传和最短录音时长是完成条件之一。

### 2.3.7 音乐律动批次

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "batch_id": "batch_01J...",
    "session_id": "ls_01J...",
    "module": "music",
    "category": "children_song",
    "category_label": "儿歌",
    "config_snapshot": {
      "category": "children_song",
      "category_label": "儿歌",
      "batch_size": 5,
      "min_repeat_interval_seconds": 604800,
      "config_version": 7
    },
    "items": [
      {
        "song_id": "song_001",
        "name": "小星星",
        "category": "children_song",
        "category_label": "儿歌",
        "audio_url": "https://...",
        "audio_srt_url": "https://...",
        "duration_ms": 176000
      }
    ]
  }
}
```

完成依据：唯一有效播放区间的覆盖比例。拖动进度条不计时；重复播放同一区间不重复累计。`accuracy` 为 `null`。

### 2.3.8 益智问答批次

路径：

```http
POST /v1/api/car/learning/quiz/sessions/{session_id}/batches
```

请求体：`{}`，必须带 `Idempotency-Key`。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "batch_id": "batch_01J...",
    "session_id": "ls_01J...",
    "module": "quiz",
    "difficulty": "beginner",
    "difficulty_label": "初级",
    "config_snapshot": {
      "difficulty": "beginner",
      "difficulty_label": "初级",
      "batch_size": 10,
      "min_repeat_interval_seconds": 604800,
      "config_version": 7
    },
    "items": [
      {
        "question_id": "quiz_001",
        "question": "哪种动物被称为森林之王？",
        "options": [
          { "option_id": "A", "text": "老虎" },
          { "option_id": "B", "text": "兔子" },
          { "option_id": "C", "text": "小鸡" },
          { "option_id": "D", "text": "金鱼" }
        ],
        "correct_option_id": "A"
      }
    ]
  }
}
```

本模块同样返回四个选项与 `correct_option_id`，完成不受正确率限制。

---

## 2.4 文件服务

文件服务供诗词跟读、聊天录音、孩子回复家长语音共用。业务接口只传 `file_id`，不直接持久化临时对象存储 URL。

### 2.4.1 初始化上传

### `POST /v1/api/car/files/uploads`

```json
{
  "purpose": "poem_recording",
  "file_name": "poem.m4a",
  "content_type": "audio/mp4",
  "size_bytes": 182400,
  "sha256": "<hex>"
}
```

`purpose`：`poem_recording`、`chat_asr`、`parent_message_voice_reply`。

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "upload_id": "upload_01J...",
    "upload_url": "https://...",
    "method": "PUT",
    "headers": { "Content-Type": "audio/mp4" },
    "expires_at": "2026-07-16T15:35:00+08:00"
  }
}
```

车机将文件直传 `upload_url`，再调用完成接口。

### 2.4.2 确认上传

### `POST /v1/api/car/files/uploads/{upload_id}/complete`

请求体：

```json
{
  "size_bytes": 182400,
  "sha256": "<hex>",
  "etag": "object-storage-etag"
}
```

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "file_id": "file_01J...",
    "purpose": "poem_recording",
    "status": "available"
  }
}
```

### 2.4.3 获取私有文件访问地址

### `GET /v1/api/car/files/{file_id}/access`

仅适用于当前车机有权访问的私有文件。

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "file_id": "file_01J...",
    "url": "https://...",
    "expires_at": "2026-07-16T15:35:00+08:00"
  }
}
```

---

## 2.5 蛋仔聊天：ASR 后文本聊天

### 2.5.1 创建或获取当天聊天 Session

### `POST /v1/api/car/chat/sessions`

请求体：`{}`。该接口是幂等的“创建或返回当天已有会话”。

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "session_id": "chat_session_01J...",
    "business_date": "2026-07-16",
    "timezone": "Asia/Shanghai",
    "status": "active",
    "expires_at": "2026-07-17T00:00:00+08:00"
  }
}
```

同一孩子每天一个 Session；跨天后创建新 Session，昨日内容不自动进入今日上下文。

### 2.5.2 获取当天消息

### `GET /v1/api/car/chat/sessions/{session_id}/messages`

返回当天完整消息。第一期不做分页；服务端以配置限制消息数和上下文长度。

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "session_id": "chat_session_01J...",
    "messages": [
      {
        "message_id": "cm_001",
        "role": "user",
        "content": "蛋仔，你好。",
        "status": "completed",
        "created_at": "2026-07-16T09:00:00+08:00"
      },
      {
        "message_id": "cm_002",
        "role": "assistant",
        "content": "你好呀！今天想聊什么？",
        "status": "completed",
        "created_at": "2026-07-16T09:00:02+08:00"
      }
    ]
  }
}
```

### 2.5.3 语音识别

录音先按 `purpose=chat_asr` 上传，上传确认后调用：

### `POST /v1/api/car/asr/transcriptions`

```json
{
  "file_id": "file_01J..."
}
```

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "transcription_id": "trans_01J...",
    "file_id": "file_01J...",
    "text": "蛋仔，为什么天空是蓝色的？",
    "duration_ms": 4280
  }
}
```

车机将 `text` 填入输入框，孩子确认或修改后再发送。聊天 ASR 音频只用于本次识别，不进入家长消息，也不作为聊天历史展示。

### 2.5.4 Chat Completions SSE

### `POST /v1/api/car/chat/completions`

```http
Accept: text/event-stream
Idempotency-Key: 398bf904-6101-4ea2-9d10-aaf5afd0b467
```

```json
{
  "session_id": "chat_session_01J...",
  "messages": [
    { "role": "user", "content": "蛋仔，你好。" },
    { "role": "assistant", "content": "你好呀！今天想聊什么？" },
    { "role": "user", "content": "为什么天空是蓝色的？" }
  ],
  "stream": true
}
```

约束：

- 车机每次传当天完整聊天记录；最后一条必须是本次新 `user` 消息。
- 后端保存的历史为权威历史，客户端历史必须与其一致；客户端不能伪造、删除或修改历史 `assistant`/`user` 消息。
- 不允许 `system`、`developer`、`model`、`temperature`、`top_p`、`max_tokens` 等字段。
- 建立 SSE 前的校验失败使用普通 `{code,msg,data}` JSON；开始 SSE 后只使用流数据块。
- 后端在内部进行儿童安全检查，输出前按短句缓冲；客户端仍只收到标准 Chat Completions 风格块。

流式数据：

```text
data: {"id":"chatcmpl_01J...","object":"chat.completion.chunk","created":1784188800,"model":"child-chat","choices":[{"index":0,"delta":{"role":"assistant","content":"天空看起来是蓝色的，"},"finish_reason":null}]}

data: {"id":"chatcmpl_01J...","object":"chat.completion.chunk","created":1784188800,"model":"child-chat","choices":[{"index":0,"delta":{"content":"主要和阳光在空气中的散射有关。"},"finish_reason":null}]}

data: {"id":"chatcmpl_01J...","object":"chat.completion.chunk","created":1784188800,"model":"child-chat","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

流被取消、模型失败或安全处理失败时，服务端应发送一个含 `finish_reason` 的最终 chunk 后结束；前端随后通过消息列表刷新最终状态。

---

## 2.6 家长消息（轻量）

第一期只做消息拉取、预设文字回复和语音回复；不做已读/未读、确认、撤回、过期、未读数、详情接口、复杂增量游标或语音 ASR。

### 2.6.1 获取最近消息

### `GET /v1/api/car/parent-messages`

返回最近固定数量消息及其回复（默认 50 条，由后端配置）。

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "items": [
      {
        "message_id": "pm_001",
        "type": "text",
        "content": { "text": "记得完成今天的数学任务哦。" },
        "created_at": "2026-07-16T15:00:00+08:00",
        "replies": [
          {
            "reply_id": "reply_001",
            "type": "preset_text",
            "preset_code": "got_it",
            "text": "知道了",
            "created_at": "2026-07-16T15:05:00+08:00"
          }
        ]
      },
      {
        "message_id": "pm_002",
        "type": "audio",
        "content": {
          "file_id": "file_parent_001",
          "playback_url": "https://...",
          "duration_ms": 8200
        },
        "created_at": "2026-07-16T15:10:00+08:00",
        "replies": []
      }
    ]
  }
}
```

`type`：`text`、`image`、`audio`、`task_card`。

`task_card` 使用白名单模块和任务 ID，例如：

```json
{
  "task_id": "task_01J...",
  "module": "math",
  "module_label": "数学妙算",
  "title": "完成今天的数学妙算"
}
```

### 2.6.2 回复家长消息

### `POST /v1/api/car/parent-messages/{message_id}/replies`

预设文字：

```json
{
  "type": "preset_text",
  "preset_code": "got_it"
}
```

语音：

```json
{
  "type": "voice",
  "file_id": "file_01J...",
  "duration_ms": 6280
}
```

固定预设：

```text
got_it       知道了
will_do_now  马上去做
done         已经完成啦
later        等一下去做
thank_you    谢谢爸爸妈妈
```

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "reply_id": "reply_01J...",
    "message_id": "pm_001",
    "type": "preset_text",
    "preset_code": "got_it",
    "text": "知道了",
    "created_at": "2026-07-16T15:05:00+08:00"
  }
}
```

语音回复响应示例：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "reply_id": "reply_01K...",
    "message_id": "pm_001",
    "type": "voice",
    "file_id": "file_01J...",
    "duration_ms": 6280,
    "created_at": "2026-07-16T15:06:00+08:00"
  }
}
```

- 孩子不能自由输入文字。
- 同一条消息可多次回复。
- 语音使用 `purpose=parent_message_voice_reply` 上传。
- 孩子回复家长的语音**不做 ASR**，不生成、不保存、不返回任何转写文本。

---

# 3. 双向 WebSocket API

## 3.1 连接与鉴权

```text
wss://<host>/v1/api/car/ws
```

建立连接后，车机首先发送：

```json
{
  "type": "auth",
  "data": {
    "access_token": "<access_token>"
  }
}
```

成功：

```json
{
  "type": "auth.ok",
  "data": { "heartbeat_interval_seconds": 30 }
}
```

失败：

```json
{
  "type": "auth.error",
  "data": { "code": "unauthorized" }
}
```

为避免令牌写入 URL 或代理日志，JWT 不放在 WebSocket 查询参数中。

## 3.2 通用事件结构

服务端推送：

```json
{
  "event_id": "evt_01J...",
  "type": "parent_message.refresh",
  "occurred_at": "2026-07-16T15:00:00+08:00",
  "data": {}
}
```

车机收到重要事件可回复：

```json
{
  "type": "ack",
  "data": { "event_id": "evt_01J..." }
}
```

心跳：

```json
{ "type": "ping", "data": {} }
```

服务端：

```json
{ "type": "pong", "data": {} }
```

WS 负责轻量通知、弹窗、本地页面跳转指令、心跳与 ACK；领取、详情、回复、数据上报仍通过 REST。WS 可以让车机在本地直接跳转到白名单页面，但不能传任意 URL 或脚本。

## 3.3 弹窗通知

```json
{
  "event_id": "evt_01J...",
  "type": "notification.popup",
  "occurred_at": "2026-07-16T15:00:00+08:00",
  "data": {
    "level": "normal",
    "title": "爸爸妈妈有消息",
    "content": "快去消息中心看看吧",
    "action": "open_parent_messages"
  }
}
```

`level`：`normal`、`important`、`urgent`。前端展示方式由 UI 决定；服务端不能传任意 URL 或强制执行脚本。

## 3.4 本地自定义跳转

服务端可以通过 WS 下发本地跳转指令，车机校验白名单后直接切换页面。该能力用于家长端或后台触发：让孩子去某个学习模块、打开蛋仔对话或打开家长消息页。

### 3.4.1 通用跳转事件

```json
{
  "event_id": "evt_01J...",
  "type": "navigation.requested",
  "occurred_at": "2026-07-16T15:00:00+08:00",
  "data": {
    "navigation_id": "nav_01J...",
    "mode": "direct",
    "destination": "learning",
    "route_key": "learning_math",
    "title": "来做 5 道数学题吧",
    "module": "math",
    "custom_batch_size": 5,
    "expires_at": "2026-07-16T15:10:00+08:00"
  }
}
```

字段说明：

| 字段 | 含义 |
| --- | --- |
| `navigation_id` | 本次跳转指令 ID；进入学习页创建会话时传回后端校验 |
| `mode` | 第一阶段固定为 `direct`，表示车机本地直接跳转 |
| `destination` | `learning`、`chat`、`parent_messages` |
| `route_key` | 前端白名单路由键，不是 URL |
| `module` | `destination=learning` 时必填，六个学习模块之一 |
| `custom_batch_size` | 可选；仅用于学习跳转时展示和后端校验，表示本次自定义题目数/内容数 |
| `expires_at` | 跳转指令过期时间，过期后前端忽略 |

前端收到后必须：

1. 校验 `route_key` 在本地白名单内；
2. 校验 `expires_at` 未过期；
3. 若当前页面有待上报学习事件，先写入本地队列并触发一次 `events:batch`，再跳转；
4. 对 `destination=learning`，跳转到对应学习页面后调用 `POST /v1/api/car/learning/{module}/sessions`，请求体使用 `source=ws_navigation` 和 `navigation_id`；
5. 不使用 WS 中的 `custom_batch_size` 自行请求题量，最终题量以后端创建会话/批次返回的 `config_snapshot.batch_size` 为准。

### 3.4.2 白名单目标

| `destination` | `route_key` | 说明 |
| --- | --- | --- |
| `learning` | `learning_science` | 科学探索 |
| `learning` | `learning_math` | 数学妙算 |
| `learning` | `learning_english` | 英语乐园 |
| `learning` | `learning_poems` | 诗词儿歌 |
| `learning` | `learning_music` | 音乐律动 |
| `learning` | `learning_quiz` | 益智问答 |
| `chat` | `chat` | 蛋仔对话页 |
| `parent_messages` | `parent_messages` | 家长消息页 |

### 3.4.3 自定义学习题量

WS 自定义学习跳转允许本次学习使用自定义题量，例如让孩子只做 5 道数学题：

```json
{
  "event_id": "evt_01J...",
  "type": "navigation.requested",
  "occurred_at": "2026-07-16T15:00:00+08:00",
  "data": {
    "navigation_id": "nav_math_5q_01J...",
    "mode": "direct",
    "destination": "learning",
    "route_key": "learning_math",
    "module": "math",
    "custom_batch_size": 5,
    "title": "完成 5 道数学小练习",
    "expires_at": "2026-07-16T15:10:00+08:00"
  }
}
```

进入数学页后创建会话：

```json
{
  "source": "ws_navigation",
  "navigation_id": "nav_math_5q_01J..."
}
```

后端校验通过后，返回的 `config_snapshot.batch_size` 为本次自定义题量。难度或类别仍由后端有效配置决定，孩子端不能改。

### 3.4.4 跳转到蛋仔对话

```json
{
  "event_id": "evt_01J...",
  "type": "navigation.requested",
  "occurred_at": "2026-07-16T15:00:00+08:00",
  "data": {
    "navigation_id": "nav_chat_01J...",
    "mode": "direct",
    "destination": "chat",
    "route_key": "chat",
    "title": "和蛋仔聊一聊",
    "expires_at": "2026-07-16T15:10:00+08:00"
  }
}
```

跳转后前端按聊天流程调用 `POST /v1/api/car/chat/sessions` 获取当天聊天 Session。

### 3.4.5 跳转到家长消息页

```json
{
  "event_id": "evt_01J...",
  "type": "navigation.requested",
  "occurred_at": "2026-07-16T15:00:00+08:00",
  "data": {
    "navigation_id": "nav_messages_01J...",
    "mode": "direct",
    "destination": "parent_messages",
    "route_key": "parent_messages",
    "title": "看看爸爸妈妈的消息",
    "expires_at": "2026-07-16T15:10:00+08:00"
  }
}
```

跳转后前端调用 `GET /v1/api/car/parent-messages` 拉取最新消息。

## 3.5 家长消息刷新通知

```json
{
  "event_id": "evt_01J...",
  "type": "parent_message.refresh",
  "occurred_at": "2026-07-16T15:00:00+08:00",
  "data": {}
}
```

收到后直接重新调用：

```http
GET /v1/api/car/parent-messages
```

## 3.6 今日任务刷新通知

```json
{
  "event_id": "evt_01J...",
  "type": "today_task.refresh",
  "occurred_at": "2026-07-16T15:00:00+08:00",
  "data": {}
}
```

收到后重新调用：

```http
GET /v1/api/car/today-tasks
```

### 3.7 断线补漏

- 车机启动、恢复前台、WS 重连成功后，主动拉取今日任务和家长消息。
- WS 不是权威数据来源；即使未收到通知，也应定时拉取。
- 推荐默认：心跳间隔 `30` 秒，`90` 秒未恢复视为断线；任务和家长消息每 `300` 秒做一次 REST 补漏。

---

# 4. 生产侧 API：学习过程数据上报

为保持车机实现轻量，学习过程统一使用批量事件上报，而不是每个动作一个接口。后端以不可变批次快照计算正确率、错题和完成状态；客户端不上传“最终正确率”或“是否正确”。

## 4.1 批量上报事件

### `POST /v1/api/car/telemetry/events:batch`

```http
Idempotency-Key: 126ddcd1-b16b-478b-bbb0-1bb6a11d293d
```

```json
{
  "events": [
    {
      "event_id": "evt_answer_001",
      "type": "answer_submitted",
      "session_id": "ls_01J...",
      "batch_id": "batch_01J...",
      "module": "math",
      "question_id": "math_001",
      "selected_option_id": "B",
      "answer_duration_ms": 4200,
      "occurred_at": "2026-07-16T10:00:00+08:00"
    },
    {
      "event_id": "evt_read_001",
      "type": "active_reading",
      "session_id": "ls_02J...",
      "batch_id": "batch_02J...",
      "module": "science",
      "article_id": "science_001",
      "active_duration_ms": 15000,
      "occurred_at": "2026-07-16T10:01:00+08:00"
    },
    {
      "event_id": "evt_play_001",
      "type": "audio_playback",
      "session_id": "ls_03J...",
      "batch_id": "batch_03J...",
      "module": "music",
      "song_id": "song_001",
      "played_ranges_ms": [[0, 30000], [32000, 80000]],
      "occurred_at": "2026-07-16T10:02:00+08:00"
    },
    {
      "event_id": "evt_record_001",
      "type": "recording_uploaded",
      "session_id": "ls_04J...",
      "batch_id": "batch_04J...",
      "module": "poems",
      "poem_id": "poem_001",
      "file_id": "file_01J...",
      "duration_ms": 12000,
      "occurred_at": "2026-07-16T10:03:00+08:00"
    }
  ]
}
```

支持事件：

| `type` | 适用模块 | 关键字段 | 用途 |
| --- | --- | --- | --- |
| `answer_submitted` | 数学、益智问答 | `question_id`、`selected_option_id`、`answer_duration_ms` | 服务端计算正确、错题与答题时长 |
| `active_reading` | 科学、诗词 | `article_id` 或 `poem_id`、`active_duration_ms` | 累计前台有效阅读时长 |
| `word_studied` | 英语 | `word_id`、`active_duration_ms` | 累计单词有效学习时长 |
| `audio_playback` | 英语、诗词、音乐 | 内容 ID、`played_ranges_ms` | 合并唯一播放区间，计算播放比例 |
| `recording_uploaded` | 诗词 | `poem_id`、`file_id`、`duration_ms` | 关联跟读录音 |

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "accepted_event_ids": ["evt_answer_001", "evt_read_001"],
    "duplicate_event_ids": [],
    "rejected": []
  }
}
```

- `event_id` 是客户端生成的唯一事件 ID；服务端据此幂等去重。
- 车机可离线缓存后批量补传；网络恢复、每隔短周期、页面退出时都应尝试上报。
- `played_ranges_ms` 用于防止拖动或重复播放虚增时长。

## 4.2 请求完成判定

### `POST /v1/api/car/telemetry/sessions/{session_id}/complete`

```json
{}
```

后端按已收事件和会话配置快照判定是否完成；不以客户端传入的完成结论为准。

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "session_id": "ls_01J...",
    "status": "completed",
    "task": {
      "task_id": "task_01J...",
      "status": "completed"
    },
    "summary": {
      "module": "math",
      "completed_count": 10,
      "total_count": 10,
      "accuracy": 0.8,
      "correct_count": 8,
      "wrong_count": 2,
      "total_active_duration_ms": 52000,
      "is_final": true
    }
  }
}
```

未达到条件时：

```json
{
  "code": 43020,
  "msg": "learning_not_complete",
  "data": {
    "session_id": "ls_01J...",
    "missing": [
      { "type": "unanswered_questions", "count": 2 }
    ]
  }
}
```

### 4.3 查询会话汇总

### `GET /v1/api/car/telemetry/sessions/{session_id}/summary`

用于页面刷新后显示当前进度、正确率和完成结果。

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "session_id": "ls_01J...",
    "module": "math",
    "status": "active",
    "completed_count": 8,
    "total_count": 10,
    "accuracy": 0.75,
    "correct_count": 6,
    "wrong_count": 2,
    "total_active_duration_ms": 41200,
    "is_final": false
  }
}
```

科学、英语、诗词、音乐等没有客观选择题的模块返回：

```json
{
  "accuracy": null,
  "correct_count": null,
  "wrong_count": null
}
```

---

# 5. 关键错误码

| code | msg | 含义 | 前端建议 |
| --- | --- | --- | --- |
| `0` | `ok` | 成功 | 正常处理 |
| `41001` | `phone_not_bound` | 手机号未绑定家长/孩子 | 提示家长先完成绑定或联系后台 |
| `41002` | `token_expired` | 访问令牌过期 | 用 refresh token 换新 token |
| `41003` | `refresh_token_invalid` | 刷新令牌无效或已退出 | 回到登录页 |
| `42001` | `content_pool_exhausted` | 内容不足，无法满足完整批次及最小重复时间 | 提示稍后再试，不责备孩子 |
| `43001` | `task_not_claimed` | 需要先领取任务 | 先调用 claim |
| `43002` | `task_expired` | 今日任务已跨天过期 | 引导自由学习或查看新任务 |
| `43003` | `invalid_task_module` | 任务模块与请求路径不匹配 | 刷新任务列表 |
| `43006` | `chat_history_conflict` | 客户端聊天历史与服务端权威历史不一致 | 重新拉取当天消息 |
| `43007` | `chat_session_expired` | 聊天 Session 跨天失效 | 创建/获取当天新 Session |
| `43020` | `learning_not_complete` | 未满足模块完成条件 | 按 `missing` 继续学习 |
| `43021` | `event_invalid` | 学习事件字段不合法或不属于当前会话 | 丢弃该事件并刷新会话 |
| `43022` | `recording_invalid` | 录音不符合跟读要求 | 重新录音 |
| `44001` | `file_not_available` | 文件未完成、已失效或无访问权限 | 重新上传或刷新文件 |
| `44002` | `asr_failed` | ASR 识别失败 | 允许重新录音 |
| `44003` | `chat_input_blocked` | 输入未通过儿童安全规则 | 给出友好提示 |
| `44004` | `chat_output_blocked` | 输出安全处理失败 | 显示安全替代回答或稍后再试 |

---

# 6. 前端最小调用流程

## 6.0 登录启动

```text
输入手机号
→ POST /v1/api/car/auth/login
→ 本地保存 access_token / refresh_token
→ 打开 WS：wss://<host>/v1/api/car/ws
→ 首包发送 auth(access_token)
→ 拉取 GET /v1/api/car/learning/park、GET /v1/api/car/today-tasks、GET /v1/api/car/parent-messages
```

## 6.1 今日任务学习

```text
GET /v1/api/car/today-tasks
→ GET /v1/api/car/today-tasks/{task_id}
→ POST /v1/api/car/today-tasks/{task_id}/claim
→ POST /v1/api/car/learning/{module}/sessions
→ POST /v1/api/car/learning/{module}/sessions/{session_id}/batches
→ POST /v1/api/car/telemetry/events:batch（持续）
→ POST /v1/api/car/telemetry/sessions/{session_id}/complete
```

## 6.2 自由学习

```text
GET /v1/api/car/learning/park
→ POST /v1/api/car/learning/{module}/sessions（source=free_learning）
→ POST /v1/api/car/learning/{module}/sessions/{session_id}/batches
→ POST /v1/api/car/telemetry/events:batch
→ POST /v1/api/car/telemetry/sessions/{session_id}/complete
```

## 6.3 蛋仔聊天

```text
POST /v1/api/car/files/uploads（purpose=chat_asr）
→ 直传音频
→ POST /v1/api/car/files/uploads/{upload_id}/complete
→ POST /v1/api/car/asr/transcriptions
→ 将 text 填入输入框，孩子确认
→ POST /v1/api/car/chat/completions（SSE）
```

## 6.4 家长消息

```text
WS 收到 parent_message.refresh
→ GET /v1/api/car/parent-messages
→ 预设回复：POST /v1/api/car/parent-messages/{message_id}/replies
→ 语音回复：上传文件 → POST /v1/api/car/parent-messages/{message_id}/replies
```

## 6.5 WS 本地直接跳转

```text
WS 收到 navigation.requested
→ 校验 route_key 白名单和 expires_at
→ 若 destination=learning，跳转到对应学习页
→ POST /v1/api/car/learning/{module}/sessions（source=ws_navigation, navigation_id=...）
→ POST /v1/api/car/learning/{module}/sessions/{session_id}/batches
```

```text
WS 收到 navigation.requested(destination=chat)
→ 跳转蛋仔对话页
→ POST /v1/api/car/chat/sessions
```

```text
WS 收到 navigation.requested(destination=parent_messages)
→ 跳转家长消息页
→ GET /v1/api/car/parent-messages
```

---

# 7. 前端实现注意事项与风险

1. `correct_option_id` 仅适用于学习反馈；篡改客户端可读取答案，因此不能用于考试、排名或高价值奖励。
2. 车机时间、答题时长和播放进度不可完全信任；前端应尽量在前台/可见状态才累计有效时长，后端仍会校验。
3. WS 只做加速通知，REST 才是权威数据；必须实现启动、重连、前台恢复和定时补拉。
4. 批次创建后不能替换内容；页面刷新应恢复原批次而不是重新请求新题。
5. 私有语音 URL 会过期；不要永久缓存 URL，只缓存 `file_id`。
6. 家长消息没有已读/未读语义；前端不应显示红点计数或回执。
7. 儿童聊天输出在后端审核后才发送；首字节延迟可能高于直接透传模型 token。

---

# 8. 可配置变量（车机可感知）

| 变量 | 推荐默认 | 含义 |
| --- | ---: | --- |
| `AUTH_ACCESS_TOKEN_TTL_SECONDS` | `7200` | Access Token 有效期 |
| `AUTH_REFRESH_TOKEN_TTL_SECONDS` | `2592000` | Refresh Token 有效期 |
| `PARENT_MESSAGE_LIST_LIMIT` | `50` | 家长消息拉取条数 |
| `PARENT_MESSAGE_POLL_INTERVAL_SECONDS` | `300` | 家长消息和任务 REST 补拉间隔 |
| `WS_HEARTBEAT_INTERVAL_SECONDS` | `30` | WS 心跳间隔 |
| `WS_DISCONNECT_TIMEOUT_SECONDS` | `90` | 视为断线的等待时间 |
| `CHAT_DAILY_MAX_MESSAGES` | `100` | 当天聊天最大消息数 |
| `CHAT_DAILY_MAX_CONTEXT_CHARS` | `30000` | 当天聊天上下文文字上限 |
| `CHAT_ASR_AUDIO_RETENTION_HOURS` | `24` | 聊天 ASR 原始音频最长保留时间 |

最终数值由后端配置管理；前端不写死业务阈值。

---

# 9. OpenAPI 交付物

已导出 OpenAPI 3.0 草案文件：

```text
docs/api/car-openapi.yaml
```

说明：

- OpenAPI 文件覆盖 REST 接口、统一响应、请求体、关键枚举、常用示例和鉴权方式。
- WebSocket 在 OpenAPI 中只做连接地址索引；具体事件结构以本文第 3 章为准。
- Chat Completions SSE 在 OpenAPI 中以 `text/event-stream` 标注；具体 chunk 格式以本文第 2.5.4 节为准。
