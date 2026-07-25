# 家长端微信小程序 API 设计

- **状态**：草案，等待需求方确认后才允许进入开发
- **适用对象**：家长端微信小程序前端、家长端网络层、后端 API 开发与测试人员
- **API 前缀**：`/v1/api/parent`
- **业务时区**：`Asia/Shanghai`
- **范围**：微信登录、家庭与孩子管理、设备绑定、学习配置、每日目标、今日任务/学习大盘、行为与使用时长、学习报告、家长消息下发、远程遥控、通知设置与通知中心、文件服务
- **不在范围内**：实时视频流、摇杆/电机控制、远程拍照、固件升级（第一期跳过）

> 本文与《车机学习与互动 API 设计》（`/v1/api/car`）配套使用。家长端负责“配置、查看、下发消息和遥控”，车机端负责“学习、交互、数据生产”。两端共享孩子、家庭、设备、配置快照和家长消息等核心数据，但接口前缀、鉴权 scope 和暴露字段不同。

---

## 1. 基本约定

### 1.1 鉴权与身份

家长端微信小程序使用微信登录 + 手机号绑定的组合鉴权：

1. 小程序调用 `wx.login()` 获取 `code`，调用后端 `/v1/api/parent/auth/wechat/login` 换取 `openid`/`unionid` 和临时令牌；
2. 若家长未绑定手机号，小程序调用 `wx.getPhoneNumber()` 获取加密手机号，再调用 `/v1/api/parent/auth/phone/bind` 完成绑定；
3. 登录成功后后端签发 JWT，家长端所有业务接口携带：

```http
Authorization: Bearer <access_token>
```

- 一个家长账号可属于多个家庭，可管理多个孩子；
- 所有涉及孩子的接口通过 URL 中的 `child_id` 指定目标孩子；后端校验该孩子是否属于当前家长的某个家庭；
- 无权限时统一返回 `404`，不暴露孩子是否存在；
- 需要防止重复写入的 POST/PUT/PATCH/DELETE 请求必须携带 `Idempotency-Key`（UUID 或等价随机唯一值）。

### 1.2 普通 JSON 响应包裹

与车机端保持一致：

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

所有响应应返回 `X-Request-ID`。

### 1.3 时间、ID、文件 URL

- 业务日期：`YYYY-MM-DD`，以后端 `Asia/Shanghai` 为准。
- 时间：ISO 8601 且带偏移量，如 `2026-07-16T15:20:38+08:00`。
- 所有资源 ID 为不透明字符串；前端不解析 ID 结构。
- `audio_url`、`image_url`、`playback_url` 可能为短期签名 URL；过期后重新请求相关资源或文件访问接口。

### 1.4 稳定枚举

#### 1.4.1 学习模块枚举

与车机端共享同一套学习模块枚举，家长端配置页必须严格使用：

| 模块 | 枚举值 |
| --- | --- |
| 科学探索 `science` | `beginner`、`intermediate`、`advanced` |
| 数学妙算 `math` | `within_10_add_subtract`、`within_10_multiply_divide`、`two_digit_add_subtract`、`two_digit_multiply_divide`、`three_digit_four_operations`、`mixed_four_operations` |
| 英语乐园 `english` | `grade_3`、`grade_4`、`grade_5`、`grade_6` |
| 诗词儿歌 `poems` | `enlightenment`、`beginner`、`intermediate`、`advanced` |
| 音乐律动 `music` | `children_song`、`popular_music`、`classical_music`、`classic_music`、`patriotic_music`、`mixed` |
| 益智问答 `quiz` | `beginner`、`intermediate`、`advanced` |

#### 1.4.2 设备类型枚举

家长端与车机端统一使用 `device_type`：

| 枚举值 | 含义 |
| --- | --- |
| `car` | 儿童车机（android_car 等固定屏幕设备） |
| `robot` | 蛋仔机器人（可移动、带摄像头、带电池） |

#### 1.4.3 任务分类枚举

今日任务扩展为四类：

| 枚举值 | 含义 |
| --- | --- |
| `learning` | 学习类任务，关联六个学习模块 |
| `lifestyle` | 生活类任务（整理书桌、浇花等） |
| `sports` | 运动类任务（跳绳、跑步等） |
| `custom` | 家长自定义文本任务 |

---

## 1.5 前端页面与接口映射

| 前端页面/功能 | 主要接口 | 触发时机 | 页面拿到的数据 |
| --- | --- | --- | --- |
| 登录/授权页 | `POST /v1/api/parent/auth/wechat/login`、`POST /v1/api/parent/auth/phone/bind` | 小程序启动、`wx.login`、手机号授权 | 家长 Token、openid、绑定状态 |
| 首页 / 切换孩子 | `GET /v1/api/parent/children`、`GET /v1/api/parent/children/{child_id}/dashboard/today` | 进入首页、onShow、切换孩子 | 孩子列表、今日学习概览、在线状态、任务摘要 |
| 孩子资料页 | `GET /v1/api/parent/children/{child_id}`、`PUT /v1/api/parent/children/{child_id}` | 编辑/保存孩子资料 | 孩子昵称、生日、性别、头像 |
| 设备页 | `GET /v1/api/parent/children/{child_id}/device`、`PUT .../device`、`DELETE .../device` | 查看/重命名/解绑车机 | 设备信息、在线状态、绑定关系 |
| 学习配置页 | `GET /v1/api/parent/children/{child_id}/learning/config`、`PUT .../learning/config` | 进入配置页、修改开关/难度/题量 | 六个模块当前配置、可选项 |
| 目标设置页 | `GET /v1/api/parent/children/{child_id}/learning/goal`、`PUT .../learning/goal` | 进入目标页、保存每日目标 | 每日总目标、分模块时长 |
| 学习追踪页 | `GET /v1/api/parent/children/{child_id}/learning/progress`、`GET .../sessions` | onShow、筛选日期 | 模块完成趋势、会话列表 |
| 行为分析页 | `GET /v1/api/parent/children/{child_id}/behavior/focus`、`GET .../behavior/posture`、`GET .../behavior/location`、`GET .../behavior/insights` | onShow、切换 tab | 专注度/坐姿/位置数据、挖掘发现 |
| 使用时长页 | `GET /v1/api/parent/children/{child_id}/usage`、`GET .../usage/modules` | onShow、切换日周月 | 使用时长序列、模块分布 |
| 报告中心/详情 | `GET /v1/api/parent/children/{child_id}/reports/weekly`、`GET .../reports/weekly/{week_key}` | 进入报告页、切换周 | 周报摘要（学习+行为聚合） |
| 看护/消息页 | `GET /v1/api/parent/children/{child_id}/messages`、`POST .../messages` | 进入消息页、发送消息 | 消息历史、孩子回复 |
| 远程遥控 | `POST /v1/api/parent/children/{child_id}/navigations` | 点击“让他去做 5 道数学题” | 跳转指令创建结果 |
| 通知中心 | `GET /v1/api/parent/notifications`、`PUT /v1/api/parent/notifications/{id}/read` | 进入通知页、标记已读 | 通知列表、未读数 |
| 通知设置页 | `GET /v1/api/parent/children/{child_id}/notification-settings`、`PUT .../notification-settings` | onShow、开关变更 | 各类通知开关、DND 时段 |

---

## 2. 认证与账号

### 2.1 微信登录

### `POST /v1/api/parent/auth/wechat/login`

关联前端：**登录页**。

请求头：

```http
Content-Type: application/json
Idempotency-Key: 0cb36a87-9cb6-4971-94e4-5cf20e3f77ab
```

请求体：

```json
{
  "wx_code": "071xxxxxxxxxxxxxx",
  "app_id": "wx_parent_miniapp_xxx",
  "invite_code": "INV001"
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `wx_code` | string | 是 | `wx.login()` 获取的临时登录凭证 |
| `app_id` | string | 是 | 小程序 AppID，后端校验并调用微信接口 |
| `invite_code` | string | 否 | 邀请码，用于被邀请加入家庭 |

成功响应（已绑定手机号）：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "token_type": "Bearer",
    "access_token": "eyJhbGciOi...",
    "expires_in": 7200,
    "refresh_token": "rt_parent_01J...",
    "refresh_expires_in": 2592000,
    "parent": {
      "parent_id": "p_01J...",
      "phone_masked": "138****8000",
      "nickname": "妈妈",
      "avatar_url": "https://..."
    },
    "families": [
      {
        "family_id": "f_01J...",
        "name": "小明的家",
        "children": [
          {
            "child_id": "c_01J...",
            "nickname": "小明",
            "avatar_url": "https://...",
            "is_default": true
          }
        ]
      }
    ]
  }
}
```

成功响应（未绑定手机号）：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "token_type": "Bearer",
    "access_token": "eyJhbGciOi...",
    "expires_in": 600,
    "refresh_token": null,
    "parent": null,
    "auth_step": "phone_bind_required",
    "wx_bind_token": "wbt_01J..."
  }
}
```

`wx_bind_token` 用于后续手机号绑定，有效期短（如 10 分钟），不拥有业务接口权限。

### 2.2 绑定手机号

### `POST /v1/api/parent/auth/phone/bind`

关联前端：**手机号授权页**。

小程序通过 `wx.getPhoneNumber()` 或用户手动输入获取加密数据后提交：

```json
{
  "wx_bind_token": "wbt_01J...",
  "encrypted_data": "...",
  "iv": "...",
  "phone": "13800138000",
  "verify_code": "123456"
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `wx_bind_token` | string | 是 | 微信登录返回的临时绑定令牌 |
| `encrypted_data` | string | 条件 | 微信加密手机号数据（优先） |
| `iv` | string | 条件 | 微信加密算法的 iv（优先） |
| `phone` | string | 条件 | 手动输入手机号时使用，需配合验证码 |
| `verify_code` | string | 条件 | 短信验证码，手动输入手机号时必填 |

后端优先使用微信加密数据解密手机号；解密失败或用户拒绝授权时，可退回到短信验证码 + 手动输入。

成功响应同 2.1 已绑定手机号场景。

### 2.3 刷新令牌

### `POST /v1/api/parent/auth/token/refresh`

关联前端：**启动页/全局网络层**。Access Token 过期前或收到 `401` 后调用。

请求体：

```json
{
  "refresh_token": "rt_parent_01J..."
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
    "refresh_token": "rt_parent_01K...",
    "refresh_expires_in": 2592000
  }
}
```

### 2.4 退出登录

### `POST /v1/api/parent/auth/logout`

关联前端：**我的/设置页**。

请求体：

```json
{
  "refresh_token": "rt_parent_01K..."
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

---

## 3. 家庭与孩子

### 3.1 获取孩子列表

### `GET /v1/api/parent/children`

关联前端：**首页孩子切换器、所有页面的顶部切换**。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "children": [
      {
        "child_id": "c_01J...",
        "nickname": "小明",
        "avatar_url": "https://...",
        "birth_date": "2019-06-01",
        "gender": "boy",
        "family_id": "f_01J...",
        "family_name": "小明的家",
        "is_default": true
      }
    ]
  }
}
```

### 3.2 获取孩子详情

### `GET /v1/api/parent/children/{child_id}`

关联前端：**孩子资料页 onLoad**。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "child_id": "c_01J...",
    "nickname": "小明",
    "avatar_url": "https://...",
    "birth_date": "2019-06-01",
    "gender": "boy",
    "family_id": "f_01J...",
    "created_at": "2024-09-01T10:00:00+08:00",
    "updated_at": "2026-07-10T12:00:00+08:00"
  }
}
```

> **生日精度规则**：API 统一使用 `birth_date`（`YYYY-MM-DD`）。若前端仅收集年月，后端默认以 `day=01` 兜底落库；展示时按产品需求可只显示年月。

### 3.3 更新孩子资料

### `PUT /v1/api/parent/children/{child_id}`

关联前端：**孩子资料页保存**。

请求头：

```http
Idempotency-Key: 9c9d7851-1f01-4a09-a2ee-9a9b01b03ca9
```

请求体：

```json
{
  "nickname": "小明",
  "avatar_url": "https://...",
  "birth_date": "2019-06-01",
  "gender": "boy"
}
```

响应：返回更新后的完整孩子对象（同 3.2）。

### 3.4 新增孩子

### `POST /v1/api/parent/children`

关联前端：**家庭管理/添加孩子**。

请求头：

```http
Idempotency-Key: 9c9d7851-1f01-4a09-a2ee-9a9b01b03ca9
```

请求体：

```json
{
  "nickname": "小红",
  "avatar_url": "https://...",
  "birth_date": "2021-03-01",
  "gender": "girl",
  "family_id": "f_01J..."
}
```

响应：返回创建后的完整孩子对象。

### 3.5 解绑孩子

### `DELETE /v1/api/parent/children/{child_id}`

关联前端：**孩子资料页解绑**。

请求头：

```http
Idempotency-Key: 9c9d7851-1f01-4a09-a2ee-9a9b01b03ca9
```

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": null
}
```

> 解绑孩子需先解除设备绑定，或允许一并解绑（产品决策）。后端至少应校验无活跃车机绑定，或记录解绑审计。

---

## 4. 设备绑定

### 4.1 获取已绑定设备

### `GET /v1/api/parent/children/{child_id}/device`

关联前端：**设备页 onShow**。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "device_id": "car_device_001",
    "device_name": "儿童车机 A",
    "device_type": "car",
    "platform": "android_car",
    "app_version": "1.0.0",
    "online": true,
    "last_online_at": "2026-07-16T15:00:00+08:00",
    "bound_at": "2024-09-01T10:00:00+08:00",
    "bind_status": "active",
    "battery_level": null,
    "signal_strength": null,
    "connection_type": "wifi",
    "current_zone": null
  }
}
```

`bind_status`：`active`、`inactive`、`revoked`。

`device_type` 见 1.4.2。`battery_level`、`signal_strength`、`current_zone` 等设备状态由车机/设备端通过遥测或心跳上报（见 4.5），家长端只读。

### 4.2 修改设备名称

### `PUT /v1/api/parent/children/{child_id}/device`

关联前端：**设备页重命名**。

请求头：

```http
Idempotency-Key: 9c9d7851-1f01-4a09-a2ee-9a9b01b03ca9
```

请求体：

```json
{
  "device_name": "小明的车机"
}
```

响应：返回更新后的完整设备对象。

### 4.3 解绑设备

### `DELETE /v1/api/parent/children/{child_id}/device`

关联前端：**设备页解绑**。

请求头：

```http
Idempotency-Key: 9c9d7851-1f01-4a09-a2ee-9a9b01b03ca9
```

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": null
}
```

### 4.4 绑定新设备

### `POST /v1/api/parent/children/{child_id}/device/bind`

关联前端：**设备页添加/扫码绑定**。

**强制规则：一个孩子一期只允许绑定一台设备。绑定新设备前必须先解绑旧设备。**

绑定方式第一期建议支持“设备码”或“家长手机号在车机端登录后自动关联”：

```json
{
  "bind_method": "device_code",
  "device_code": "DC20260716001",
  "device_name": "客厅车机"
}
```

或：

```json
{
  "bind_method": "phone_auto",
  "device_id": "car_device_002",
  "device_name": "卧室车机"
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `bind_method` | string | 是 | `device_code` / `phone_auto` / `scan_qr` |
| `device_code` | string | 条件 | 设备机身码或扫码结果，绑定方式所需 |
| `device_id` | string | 条件 | 设备唯一标识，`phone_auto` 时由车机上报 |
| `device_name` | string | 否 | 家长自定义展示名 |

响应：返回绑定后的完整设备对象。

若该孩子已存在活跃绑定，返回：

```json
{
  "code": 42004,
  "msg": "device_already_bound",
  "data": {
    "existing_device_id": "car_device_001",
    "existing_device_name": "儿童车机 A"
  }
}
```

### 4.5 设备状态数据 prerequisite（车机/设备端）

家长端 `device` 接口中的 `battery_level`、`signal_strength`、`connection_type`、`current_zone` 等字段需要车机/设备端上报。建议通过以下方式补充《车机学习与互动 API 设计》：

1. **遥测事件批量上报** `POST /v1/api/car/telemetry/events:batch` 新增事件类型：
   - `device_status`：携带 `battery_level`、`signal_strength`、`connection_type`、`current_zone`；
   - `zone_changed`：区域切换事件；
2. 或新增 **设备心跳接口** `POST /v1/api/car/device/heartbeat`，由设备定期上报状态。

家长端只读取聚合后的最新状态，不参与原始上报协议定义。

---

## 5. 学习配置

### 5.1 获取当前学习配置

### `GET /v1/api/parent/children/{child_id}/learning/config`

关联前端：**学习配置页 onShow**。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "child_id": "c_01J...",
    "updated_at": "2026-07-16T10:00:00+08:00",
    "updated_by": {
      "parent_id": "p_01J...",
      "nickname": "妈妈"
    },
    "modules": [
      {
        "module": "science",
        "module_label": "科学探索",
        "enabled": true,
        "effective_config": {
          "difficulty": "beginner",
          "difficulty_label": "初级",
          "batch_size": 3,
          "min_repeat_interval_seconds": 604800,
          "config_version": 7
        }
      },
      {
        "module": "math",
        "module_label": "数学妙算",
        "enabled": true,
        "effective_config": {
          "difficulty": "within_10_add_subtract",
          "difficulty_label": "十以内加减法",
          "batch_size": 10,
          "min_repeat_interval_seconds": 604800,
          "config_version": 7
        }
      }
    ]
  }
}
```

### 5.2 更新学习配置

### `PUT /v1/api/parent/children/{child_id}/learning/config`

关联前端：**学习配置页保存**。

请求头：

```http
Idempotency-Key: 9c9d7851-1f01-4a09-a2ee-9a9b01b03ca9
```

请求体：

```json
{
  "modules": [
    {
      "module": "science",
      "enabled": true,
      "difficulty": "beginner",
      "batch_size": 3,
      "min_repeat_interval_seconds": 604800
    },
    {
      "module": "math",
      "enabled": true,
      "difficulty": "within_10_add_subtract",
      "batch_size": 10,
      "min_repeat_interval_seconds": 604800
    }
  ]
}
```

约束：

- 家长只能修改自己家庭下孩子的配置；
- 可修改字段限制为 `enabled`、`difficulty`/`category`、`batch_size`、`min_repeat_interval_seconds`；
- 每次修改对应模块 `config_version + 1`，并写配置审计记录；
- `batch_size`、`min_repeat_interval_seconds` 必须受服务端上下限约束；
- 已生成今日任务、已创建会话和已创建批次不回写新配置；
- 新自由学习会话和新生成今日任务读取当前有效配置。

响应：返回更新后的完整配置（同 5.1）。

### 5.3 获取配置变更历史

### `GET /v1/api/parent/children/{child_id}/learning/config/audit`

关联前端：**学习配置页历史记录**。

参数：`?module=math&limit=20&cursor=`。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "items": [
      {
        "audit_id": "audit_01J...",
        "module": "math",
        "module_label": "数学妙算",
        "old_config": {
          "difficulty": "within_10_add_subtract",
          "batch_size": 10
        },
        "new_config": {
          "difficulty": "two_digit_add_subtract",
          "batch_size": 10
        },
        "changed_by": {
          "parent_id": "p_01J...",
          "nickname": "妈妈"
        },
        "changed_at": "2026-07-16T10:00:00+08:00",
        "reason": "小明十以内已很熟练"
      }
    ],
    "next_cursor": "..."
  }
}
```

### 5.4 每日学习目标

### `GET /v1/api/parent/children/{child_id}/learning/goal`

关联前端：**目标设置页 onLoad**。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "child_id": "c_01J...",
    "daily_goal_minutes": 120,
    "modules": [
      {
        "module": "math",
        "module_label": "数学妙算",
        "goal_minutes": 30
      },
      {
        "module": "science",
        "module_label": "科学探索",
        "goal_minutes": 20
      }
    ],
    "updated_at": "2026-07-16T10:00:00+08:00"
  }
}
```

### `PUT /v1/api/parent/children/{child_id}/learning/goal`

关联前端：**目标设置页保存**。

请求头：

```http
Idempotency-Key: 9c9d7851-1f01-4a09-a2ee-9a9b01b03ca9
```

请求体：

```json
{
  "daily_goal_minutes": 120,
  "modules": [
    { "module": "math", "goal_minutes": 30 },
    { "module": "science", "goal_minutes": 20 }
  ]
}
```

约束：

- 分模块目标分钟数之和不能超过 `daily_goal_minutes`；
- 服务端保存后用于首页“目标达成率”、使用时长页“距离每日限额”等计算；
- 学习配置（§5）与学习目标（§5.4）是两个独立维度：前者管“每次做多少题/什么难度”，后者管“每天学多久”。

响应：返回更新后的完整目标（同 GET）。

---

## 6. 今日任务与学习大盘

### 6.1 今日学习大盘

### `GET /v1/api/parent/children/{child_id}/dashboard/today`

关联前端：**首页 onShow / 下拉刷新**。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "business_date": "2026-07-16",
    "timezone": "Asia/Shanghai",
    "child_status": {
      "online": true,
      "last_seen_at": "2026-07-16T15:30:00+08:00",
      "current_zone": "客厅",
      "current_activity": "正在完成数学妙算"
    },
    "today_tasks": {
      "total": 4,
      "completed": 1,
      "in_progress": 1,
      "pending": 2,
      "items": [
        {
          "task_id": "task_01J...",
          "task_category": "learning",
          "module": "math",
          "module_label": "数学妙算",
          "status": "in_progress",
          "title": "今日数学妙算",
          "progress": { "completed_count": 3, "total_count": 10 },
          "expires_at": "2026-07-17T00:00:00+08:00"
        },
        {
          "task_id": "task_02J...",
          "task_category": "lifestyle",
          "module": null,
          "module_label": null,
          "status": "pending",
          "title": "整理书桌",
          "progress": null,
          "expires_at": "2026-07-17T00:00:00+08:00"
        }
      ]
    },
    "today_summary": {
      "total_active_duration_minutes": 45,
      "modules_touched": ["math", "science"],
      "accuracy": 0.8,
      "goal_progress_percent": 72,
      "goal_remaining_minutes": 33,
      "last_learning_at": "2026-07-16T15:20:00+08:00"
    },
    "behavior_summary": {
      "focus_score": 92,
      "focus_score_change_percent": 3,
      "ai_insight": {
        "title": "蛋仔说…",
        "body": "小宇连续答对 12 道心算题，数学正确率较昨日提升 8%。继续保持哦！"
      },
      "recent_timeline": [
        {
          "time": "10:42",
          "type": "focus",
          "text": "专注时段 · 连续 25 分钟",
          "tag": { "text": "优秀", "color": "mint" }
        }
      ]
    }
  }
}
```

### 6.2 获取今日任务列表

### `GET /v1/api/parent/children/{child_id}/today-tasks`

关联前端：**首页任务列表、学习追踪页**。

参数：`?date=2026-07-16`（默认当天业务日期）。

响应：

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
        "task_category": "learning",
        "module": "math",
        "module_label": "数学妙算",
        "status": "in_progress",
        "title": "今日数学妙算",
        "progress": { "completed_count": 3, "total_count": 10, "accuracy": 0.75, "is_final": false },
        "expires_at": "2026-07-17T00:00:00+08:00"
      },
      {
        "task_id": "task_02J...",
        "task_category": "lifestyle",
        "module": null,
        "module_label": null,
        "status": "pending",
        "title": "整理书桌",
        "progress": null,
        "expires_at": "2026-07-17T00:00:00+08:00"
      }
    ]
  }
}
```

### 6.3 获取任务详情

### `GET /v1/api/parent/children/{child_id}/today-tasks/{task_id}`

关联前端：**任务详情页**。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "task_id": "task_01J...",
    "task_category": "learning",
    "module": "math",
    "module_label": "数学妙算",
    "status": "in_progress",
    "config_snapshot": {
      "difficulty": "within_10_add_subtract",
      "difficulty_label": "十以内加减法",
      "batch_size": 10,
      "min_repeat_interval_seconds": 604800,
      "config_version": 7
    },
    "progress": {
      "completed_count": 3,
      "total_count": 10,
      "accuracy": 0.75,
      "correct_count": 3,
      "wrong_count": 1,
      "is_final": false
    },
    "expires_at": "2026-07-17T00:00:00+08:00",
    "created_at": "2026-07-16T00:00:00+08:00"
  }
}
```

对于 `task_category` 为 `lifestyle` / `sports` / `custom` 的任务，`module` 为 `null`，`config_snapshot` 和 `progress.accuracy` 也为 `null`。

### 6.4 派发任务（家长端主动创建）

### `POST /v1/api/parent/children/{child_id}/dispatched-tasks`

关联前端：**首页/看护页派任务面板**。

请求头：

```http
Idempotency-Key: 9c9d7851-1f01-4a09-a2ee-9a9b01b03ca9
```

请求体：

```json
{
  "tasks": [
    {
      "task_category": "learning",
      "module": "math",
      "title": "数学口算 10 题"
    },
    {
      "task_category": "lifestyle",
      "module": null,
      "title": "整理书桌"
    },
    {
      "task_category": "sports",
      "module": null,
      "title": "跳绳 100 下"
    },
    {
      "task_category": "custom",
      "module": null,
      "title": "帮妈妈浇花"
    }
  ]
}
```

约束：

- `learning` 类任务必须指定六个学习模块之一；
- `lifestyle` / `sports` / `custom` 不关联模块；
- 后端生成当天任务，并触发 `today_task.refresh` WS 事件通知车机；
- 同一天同一模块最多一个 `learning` 任务（与车机端规则一致）。

响应：返回创建的任务列表。

### `GET /v1/api/parent/children/{child_id}/dispatched-tasks`

关联前端：**首页/看护页查看今日已派发任务**。

参数：`?date=2026-07-16`。

响应：返回当天家长派发的任务列表（结构同 6.2）。

### 6.5 非学习任务完成 prerequisite（车机/设备端）

`lifestyle` / `sports` / `custom` 类任务没有学习会话/批次流程，需要车机端提供简单完成确认能力。建议在《车机学习与互动 API 设计》中补充：

```http
POST /v1/api/car/today-tasks/{task_id}/complete
```

请求体：`{}`，幂等。

车机端孩子勾选完成后调用，后端将任务标记为 `completed`。

---

## 7. 行为与使用时长

### 7.1 专注度

### `GET /v1/api/parent/children/{child_id}/behavior/focus`

关联前端：**行为分析页 - 专注度 tab**。

参数：`?period=week`（`day` / `week` / `month`，默认 `week`）。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "period": "week",
    "score": 89,
    "change_percent": -3,
    "stats": [
      { "label": "分散次数", "value": 3, "unit": "次" },
      { "label": "最长专注", "value": 25, "unit": "min" },
      { "label": "专注占比", "value": 87, "unit": "%" },
      { "label": "打断次数", "value": 4, "unit": "次" }
    ],
    "daily_series": [
      { "date": "2026-07-14", "score": 92 },
      { "date": "2026-07-15", "score": 90 },
      { "date": "2026-07-16", "score": 78 }
    ]
  }
}
```

### 7.2 坐姿

### `GET /v1/api/parent/children/{child_id}/behavior/posture`

关联前端：**行为分析页 - 姿态 tab**。

参数：`?period=week`。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "period": "week",
    "score": 82,
    "change_percent": 5,
    "reminder_count": 6,
    "distribution": [
      { "label": "标准坐姿", "percent": 78 },
      { "label": "轻微倾斜", "percent": 15 },
      { "label": "明显歪斜", "percent": 7 }
    ],
    "weekly_series": [
      { "week_key": "2026-06-23", "score": 74 },
      { "week_key": "2026-06-30", "score": 75 },
      { "week_key": "2026-07-07", "score": 77 },
      { "week_key": "2026-07-14", "score": 82 }
    ]
  }
}
```

### 7.3 位置

### `GET /v1/api/parent/children/{child_id}/behavior/location`

关联前端：**行为分析页 - 位置 tab**。

参数：`?period=week`。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "period": "week",
    "active_zones_count": 3,
    "distribution": [
      { "zone": "客厅", "percent": 65 },
      { "zone": "书房", "percent": 25 },
      { "zone": "卧室", "percent": 10 }
    ],
    "anomaly_detected": false
  }
}
```

### 7.4 行为洞察

### `GET /v1/api/parent/children/{child_id}/behavior/insights`

关联前端：**行为分析页挖掘发现卡片、报告详情页 discoveries**。

参数：`?period=week&type=`。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "items": [
      {
        "insight_id": "insight_01J...",
        "type": "focus",
        "title": "周三下午专注度骤降",
        "description": "15:30-16:20 跌至 62 分，与\"思维游戏\"上线时间吻合。中断次数为平时 3.2 倍。",
        "tags": [
          { "text": "专注度", "cls": "tf" },
          { "text": "使用时长", "cls": "tt" }
        ],
        "occurred_at": "2026-07-16T15:30:00+08:00"
      }
    ]
  }
}
```

### 7.5 使用时长

### `GET /v1/api/parent/children/{child_id}/usage`

关联前端：**使用时长页**。

参数：`?granularity=day`（`day` / `week` / `month`）。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "granularity": "day",
    "daily_goal_minutes": 120,
    "series": [
      { "date": "2026-07-10", "total_minutes": 46 },
      { "date": "2026-07-11", "total_minutes": 72 },
      { "date": "2026-07-12", "total_minutes": 96 },
      { "date": "2026-07-13", "total_minutes": 58 },
      { "date": "2026-07-14", "total_minutes": 81 },
      { "date": "2026-07-15", "total_minutes": 63 },
      { "date": "2026-07-16", "total_minutes": 86 }
    ]
  }
}
```

### `GET /v1/api/parent/children/{child_id}/usage/modules`

关联前端：**使用时长页模块分布**。

参数：`?date=2026-07-16`。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "date": "2026-07-16",
    "total_minutes": 86,
    "modules": [
      { "module": "math", "module_label": "数学妙算", "minutes": 36, "percent": 42 },
      { "module": "science", "module_label": "科学探索", "minutes": 26, "percent": 30 },
      { "module": "english", "module_label": "英语乐园", "minutes": 14, "percent": 16 },
      { "module": "poems", "module_label": "诗词儿歌", "minutes": 10, "percent": 12 }
    ]
  }
}
```

> 注意：`usage` 统计的是“设备总使用时长”，可能包含非学习时段；`learning/progress` 统计的是“学习主动时长”。两者口径不同，展示时应避免混为一谈。

---

## 8. 学习报告

### 8.1 学习进度总览

### `GET /v1/api/parent/children/{child_id}/learning/progress`

关联前端：**学习追踪页**。

参数：`?start_date=2026-07-01&end_date=2026-07-16`。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "period": { "start_date": "2026-07-01", "end_date": "2026-07-16" },
    "module_stats": [
      {
        "module": "math",
        "module_label": "数学妙算",
        "sessions_count": 8,
        "completed_tasks": 6,
        "total_tasks": 8,
        "total_active_duration_minutes": 120,
        "accuracy": 0.82,
        "correct_count": 66,
        "wrong_count": 14
      }
    ],
    "daily_trend": [
      {
        "date": "2026-07-16",
        "total_active_duration_minutes": 45,
        "completed_modules": ["math", "science"]
      }
    ]
  }
}
```

### 8.2 学习会话列表

### `GET /v1/api/parent/children/{child_id}/learning/sessions`

关联前端：**学习追踪页会话列表**。

参数：`?module=math&status=completed&start_date=2026-07-01&end_date=2026-07-16&page=1&page_size=20`。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "items": [
      {
        "session_id": "ls_01J...",
        "module": "math",
        "module_label": "数学妙算",
        "source": "today_task",
        "status": "completed",
        "created_at": "2026-07-16T09:00:00+08:00",
        "completed_at": "2026-07-16T09:20:00+08:00",
        "summary": {
          "completed_count": 10,
          "total_count": 10,
          "accuracy": 0.8,
          "correct_count": 8,
          "wrong_count": 2,
          "total_active_duration_ms": 52000
        }
      }
    ],
    "pagination": { "page": 1, "page_size": 20, "total": 5, "total_pages": 1 }
  }
}
```

### 8.3 会话详情

### `GET /v1/api/parent/children/{child_id}/learning/sessions/{session_id}`

关联前端：**会话详情页**。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "session_id": "ls_01J...",
    "module": "math",
    "module_label": "数学妙算",
    "source": "today_task",
    "status": "completed",
    "config_snapshot": {
      "difficulty": "within_10_add_subtract",
      "difficulty_label": "十以内加减法",
      "batch_size": 10,
      "min_repeat_interval_seconds": 604800,
      "config_version": 7
    },
    "batches": [
      {
        "batch_id": "batch_01J...",
        "sequence_no": 1,
        "items_count": 10,
        "issued_at": "2026-07-16T09:00:00+08:00"
      }
    ],
    "summary": {
      "completed_count": 10,
      "total_count": 10,
      "accuracy": 0.8,
      "correct_count": 8,
      "wrong_count": 2,
      "total_active_duration_ms": 52000
    }
  }
}
```

### 8.4 错题本

### `GET /v1/api/parent/children/{child_id}/learning/wrong-answers`

关联前端：**错题本页**。

参数：`?module=math&page=1&page_size=20`。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "items": [
      {
        "wrong_answer_id": "wa_01J...",
        "module": "math",
        "module_label": "数学妙算",
        "question_snapshot": {
          "question_id": "math_001",
          "question": "3 + 4 = ?",
          "options": [
            { "option_id": "A", "text": "6" },
            { "option_id": "B", "text": "7" },
            { "option_id": "C", "text": "8" },
            { "option_id": "D", "text": "9" }
          ],
          "correct_option_id": "B"
        },
        "selected_option_id": "A",
        "first_wrong_at": "2026-07-16T09:05:00+08:00",
        "last_wrong_at": "2026-07-16T09:05:00+08:00",
        "wrong_count": 1
      }
    ],
    "pagination": { "page": 1, "page_size": 20, "total": 3, "total_pages": 1 }
  }
}
```

### 8.5 周报列表

### `GET /v1/api/parent/children/{child_id}/reports/weekly`

关联前端：**报告中心页**。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "current_week": {
      "week_key": "2026-07-14",
      "label": "7月14日—7月20日",
      "start_date": "2026-07-14",
      "end_date": "2026-07-20"
    },
    "summary": {
      "focus_score": 89,
      "focus_change_percent": -3,
      "posture_score": 82,
      "posture_change_percent": 5,
      "anomaly_count": 2,
      "discovery_count": 3
    },
    "weeks": [
      {
        "week_key": "2026-07-14",
        "label": "7月14日—7月20日",
        "has_new": true
      },
      {
        "week_key": "2026-07-07",
        "label": "7月7日—7月13日",
        "has_new": false
      }
    ]
  }
}
```

### 8.6 周报详情

### `GET /v1/api/parent/children/{child_id}/reports/weekly/{week_key}`

关联前端：**报告详情页**。

`week_key` 格式为当周周一日期 `YYYY-MM-DD`。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "week_key": "2026-07-14",
    "label": "7月14日—7月20日",
    "start_date": "2026-07-14",
    "end_date": "2026-07-20",
    "learning_summary": {
      "total_active_duration_minutes": 320,
      "completed_tasks": 12,
      "total_tasks": 14,
      "average_accuracy": 0.85,
      "modules_touched": ["math", "science", "english"]
    },
    "behavior_summary": {
      "focus_score": 89,
      "focus_change_percent": -3,
      "posture_score": 82,
      "posture_change_percent": 5,
      "daily_usage_score": 78
    },
    "focus_daily_series": [
      { "date": "2026-07-14", "score": 92 },
      { "date": "2026-07-15", "score": 90 },
      { "date": "2026-07-16", "score": 78 },
      { "date": "2026-07-17", "score": 85 },
      { "date": "2026-07-18", "score": 88 },
      { "date": "2026-07-19", "score": 91 },
      { "date": "2026-07-20", "score": 89 }
    ],
    "posture_weekly_series": [
      { "week_key": "2026-06-23", "score": 74 },
      { "week_key": "2026-06-30", "score": 75 },
      { "week_key": "2026-07-07", "score": 77 },
      { "week_key": "2026-07-14", "score": 82 }
    ],
    "anomalies": [
      {
        "title": "周三下午专注度骤降",
        "description": "15:30-16:20 跌至 62 分，与\"思维游戏\"上线时间吻合。中断次数为平时 3.2 倍。",
        "tags": [
          { "text": "专注度", "cls": "tf" },
          { "text": "使用时长", "cls": "tt" }
        ]
      }
    ],
    "discoveries": [
      {
        "title": "使用时长 > 90分钟 → 坐姿问题 +40%",
        "description": "3 天超过 90 分钟，坐姿问题次数平均多出 40%。建议在 80 分钟时触发休息提醒。",
        "color": "#778ccd"
      }
    ],
    "ai_summary": "这周值得关注：专注度变化 3%，坐姿变化 5%。关键规律已被蛋仔捕捉到——用太久坐姿会变差，客厅学习效率不如书房，早上状态最好。"
  }
}
```

---

## 9. 家长消息

### 9.1 获取消息历史

### `GET /v1/api/parent/children/{child_id}/messages`

关联前端：**消息历史页 / 看护页消息列表**。

参数：`?page=1&page_size=20`。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "items": [
      {
        "message_id": "pm_001",
        "direction": "parent_to_child",
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
        "direction": "parent_to_child",
        "type": "audio",
        "content": {
          "file_id": "file_parent_001",
          "playback_url": "https://...",
          "duration_ms": 8200
        },
        "created_at": "2026-07-16T15:10:00+08:00",
        "replies": []
      }
    ],
    "pagination": { "page": 1, "page_size": 20, "total": 5, "total_pages": 1 }
  }
}
```

`direction`：`parent_to_child` / `child_to_parent`（本期主要是家长发的消息和孩子回复）。

`type`：`text`、`image`、`audio`、`task_card`。

### 9.2 发送家长消息

### `POST /v1/api/parent/children/{child_id}/messages`

关联前端：**看护页发送消息**。

请求头：

```http
Idempotency-Key: 9c9d7851-1f01-4a09-a2ee-9a9b01b03ca9
```

文字消息：

```json
{
  "type": "text",
  "content": { "text": "坐直哦，注意用眼。" }
}
```

图片消息（先上传文件）：

```json
{
  "type": "image",
  "content": { "file_id": "file_image_001" }
}
```

音频消息（先上传文件）：

```json
{
  "type": "audio",
  "content": {
    "file_id": "file_audio_001",
    "duration_ms": 8200
  }
}
```

任务卡片：

```json
{
  "type": "task_card",
  "content": {
    "task_id": "task_01J...",
    "task_category": "learning",
    "module": "math",
    "module_label": "数学妙算",
    "title": "完成今天的数学妙算"
  }
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `type` | string | 是 | `text` / `image` / `audio` / `task_card` |
| `content.text` | string | 条件 | 文字消息必填 |
| `content.file_id` | string | 条件 | 图片/音频必填 |
| `content.duration_ms` | int | 条件 | 音频必填 |
| `content.task_id` | string | 条件 | 任务卡片必填，必须是当天属于该孩子的任务 |

响应：返回创建后的消息对象（同 9.1 单条）。

发送成功后，后端向车机推送 `parent_message.refresh` WS 事件，车机拉取 `GET /v1/api/car/parent-messages`。

### 9.3 删除消息

### `DELETE /v1/api/parent/children/{child_id}/messages/{message_id}`

关联前端：**消息历史页长按删除**。

请求头：

```http
Idempotency-Key: 9c9d7851-1f01-4a09-a2ee-9a9b01b03ca9
```

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": null
}
```

> 删除仅从家长端视角隐藏；车机端是否同步隐藏由产品决策决定。后端至少应记录删除审计。

---

## 10. 远程遥控

### 10.1 创建跳转指令

### `POST /v1/api/parent/children/{child_id}/navigations`

关联前端：**看护页“让他去学习”/首页快捷遥控**。

请求头：

```http
Idempotency-Key: 9c9d7851-1f01-4a09-a2ee-9a9b01b03ca9
```

跳到学习模块：

```json
{
  "destination": "learning",
  "route_key": "learning_math",
  "module": "math",
  "custom_batch_size": 5,
  "title": "来做 5 道数学题吧",
  "expires_in_seconds": 600
}
```

跳到蛋仔对话：

```json
{
  "destination": "chat",
  "route_key": "chat",
  "title": "和蛋仔聊一聊",
  "expires_in_seconds": 600
}
```

跳到家长消息页：

```json
{
  "destination": "parent_messages",
  "route_key": "parent_messages",
  "title": "看看爸爸妈妈的消息",
  "expires_in_seconds": 600
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `destination` | string | 是 | `learning` / `chat` / `parent_messages` |
| `route_key` | string | 是 | 车机端白名单路由键 |
| `module` | string | 条件 | `destination=learning` 时必填 |
| `custom_batch_size` | int | 否 | 学习跳转时本次自定义题量 |
| `title` | string | 否 | 弹窗或跳转提示标题 |
| `expires_in_seconds` | int | 否 | 指令过期时间，默认 600 秒 |

约束：

- `route_key` 必须在车机端白名单内；
- `custom_batch_size` 必须在服务端允许范围内；
- 难度/类别仍取当前有效配置，家长端本次只改题量，不改难度；
- 指令创建后立即通过 WebSocket 推送给车机。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "navigation_id": "nav_01J...",
    "destination": "learning",
    "route_key": "learning_math",
    "module": "math",
    "custom_batch_size": 5,
    "title": "来做 5 道数学题吧",
    "expires_at": "2026-07-16T15:10:00+08:00",
    "created_at": "2026-07-16T15:00:00+08:00"
  }
}
```

### 10.2 获取在线状态

### `GET /v1/api/parent/children/{child_id}/online-status`

关联前端：**首页在线状态点、设备页**。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "online": true,
    "ws_connected": true,
    "last_seen_at": "2026-07-16T15:30:00+08:00",
    "current_zone": "客厅",
    "current_route_key": "learning_math",
    "current_activity": "正在完成数学妙算"
  }
}
```

---

## 11. 通知设置与通知中心

### 11.1 获取通知设置

### `GET /v1/api/parent/children/{child_id}/notification-settings`

关联前端：**通知设置页 onShow**。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "child_id": "c_01J...",
    "settings": {
      "task_completed": true,
      "task_expired": true,
      "child_replied": true,
      "behavior_alert": true,
      "realtime_alert": true,
      "goal_achieved": true,
      "daily_summary": true,
      "weekly_report": true,
      "device_offline": true,
      "learning_milestone": false
    },
    "dnd": {
      "enabled": true,
      "start_time": "22:00",
      "end_time": "08:00"
    },
    "updated_at": "2026-07-16T10:00:00+08:00"
  }
}
```

### 11.2 更新通知设置

### `PUT /v1/api/parent/children/{child_id}/notification-settings`

关联前端：**通知设置页开关变更**。

请求头：

```http
Idempotency-Key: 9c9d7851-1f01-4a09-a2ee-9a9b01b03ca9
```

请求体：

```json
{
  "settings": {
    "task_completed": true,
    "task_expired": true,
    "child_replied": true,
    "behavior_alert": true,
    "realtime_alert": true,
    "goal_achieved": true,
    "daily_summary": true,
    "weekly_report": true,
    "device_offline": true,
    "learning_milestone": false
  },
  "dnd": {
    "enabled": true,
    "start_time": "22:00",
    "end_time": "08:00"
  }
}
```

响应：返回更新后的完整设置（同 11.1）。

### 11.3 通知中心列表

### `GET /v1/api/parent/notifications`

关联前端：**通知中心页**。

参数：`?filter=all&page=1&page_size=20`。

`filter`：`all`、`unread`、`behavior`、`learning`、`device`、`system`。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "unread_count": 3,
    "items": [
      {
        "notification_id": "notif_01J...",
        "type": "behavior_alert",
        "icon": "ic-posture",
        "title": "坐姿提醒",
        "description": "小宇连续 10 分钟坐姿歪斜",
        "child_id": "c_01J...",
        "child_nickname": "小宇",
        "is_read": false,
        "created_at": "2026-07-16T15:00:00+08:00"
      },
      {
        "notification_id": "notif_02J...",
        "type": "learning",
        "icon": "ic-math",
        "title": "数学任务已完成",
        "description": "小宇完成了今日数学妙算，正确率 80%",
        "child_id": "c_01J...",
        "child_nickname": "小宇",
        "is_read": true,
        "created_at": "2026-07-16T14:30:00+08:00"
      }
    ],
    "pagination": { "page": 1, "page_size": 20, "total": 5, "total_pages": 1 }
  }
}
```

### 11.4 标记通知已读

### `PUT /v1/api/parent/notifications/{notification_id}/read`

关联前端：**通知中心页点击标记已读**。

请求头：

```http
Idempotency-Key: 9c9d7851-1f01-4a09-a2ee-9a9b01b03ca9
```

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "notification_id": "notif_01J...",
    "is_read": true,
    "read_at": "2026-07-16T15:05:00+08:00"
  }
}
```

---

## 12. 文件服务

家长端文件服务与车机端文件服务共享底层对象存储，但用途和访问主体不同。

### 12.1 初始化上传

### `POST /v1/api/parent/files/uploads`

请求体：

```json
{
  "purpose": "parent_message_image",
  "file_name": "message.jpg",
  "content_type": "image/jpeg",
  "size_bytes": 102400,
  "sha256": "<hex>"
}
```

`purpose`：`parent_message_image`、`parent_message_audio`、`parent_avatar`、`child_avatar`。

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "upload_id": "upload_01J...",
    "upload_url": "https://...",
    "method": "PUT",
    "headers": { "Content-Type": "image/jpeg" },
    "expires_at": "2026-07-16T15:35:00+08:00"
  }
}
```

### 12.2 确认上传

### `POST /v1/api/parent/files/uploads/{upload_id}/complete`

请求体：

```json
{
  "size_bytes": 102400,
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
    "purpose": "parent_message_image",
    "status": "available"
  }
}
```

### 12.3 获取私有文件访问地址

### `GET /v1/api/parent/files/{file_id}/access`

仅适用于当前家长有权访问的私有文件（自己发的消息附件、孩子回复的语音等）。

响应：

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

## 13. 关键错误码

| code | msg | 含义 | 前端建议 |
| --- | --- | --- | --- |
| `0` | `ok` | 成功 | 正常处理 |
| `41001` | `phone_not_bound` | 手机号未绑定 | 引导绑定手机号 |
| `41002` | `token_expired` | 访问令牌过期 | 用 refresh token 换新 token |
| `41003` | `refresh_token_invalid` | 刷新令牌无效或已退出 | 回到登录页 |
| `41004` | `wx_code_invalid` | 微信临时 code 无效或已过期 | 重新 `wx.login` |
| `41005` | `wx_phone_decrypt_failed` | 微信加密手机号解密失败 | 引导短信验证码方式 |
| `42001` | `child_not_found` | 孩子不存在或无权限 | 不暴露详情，返回 404 |
| `42002` | `device_not_bound` | 孩子尚未绑定设备 | 引导绑定设备 |
| `42003` | `device_offline` | 设备当前不在线 | 提示稍后重试 |
| `42004` | `device_already_bound` | 该孩子已绑定其他设备 | 先解绑旧设备 |
| `43001` | `task_not_found` | 任务不存在或不属于该孩子 | 刷新任务列表 |
| `43002` | `task_card_invalid` | 任务卡片引用的任务无效 | 选择有效任务 |
| `43003` | `navigation_invalid` | 跳转指令参数非法 | 检查 route_key / module |
| `44001` | `file_not_available` | 文件未完成、已失效或无访问权限 | 重新上传或刷新文件 |
| `45001` | `config_value_invalid` | 配置值超范围或枚举非法 | 按服务端返回范围调整 |
| `45002` | `module_disabled` | 该模块已关闭 | 先启用模块 |
| `45003` | `goal_invalid` | 分模块目标分钟数超过总目标 | 调整模块分配 |

---

## 14. 可配置变量（家长端可感知）

| 变量 | 推荐默认 | 含义 |
| --- | ---: | --- |
| `AUTH_ACCESS_TOKEN_TTL_SECONDS` | `7200` | Access Token 有效期 |
| `AUTH_REFRESH_TOKEN_TTL_SECONDS` | `2592000` | Refresh Token 有效期 |
| `AUTH_WX_BIND_TOKEN_TTL_SECONDS` | `600` | 微信绑定手机号临时令牌有效期 |
| `PARENT_MESSAGE_PAGE_SIZE` | `20` | 家长消息历史每页条数 |
| `NOTIFICATION_PAGE_SIZE` | `20` | 通知中心每页条数 |
| `LEARNING_SESSION_PAGE_SIZE` | `20` | 学习会话列表每页条数 |
| `WRONG_ANSWER_PAGE_SIZE` | `20` | 错题本每页条数 |
| `NAVIGATION_DEFAULT_EXPIRE_SECONDS` | `600` | 远程跳转指令默认过期时间 |
| `MAX_NAVIGATION_CUSTOM_BATCH_SIZE` | `20` | 远程跳转自定义题量上限 |
| `MIN_NAVIGATION_CUSTOM_BATCH_SIZE` | `1` | 远程跳转自定义题量下限 |
| `DEVICE_STATUS_TTL_SECONDS` | `300` | 设备在线/电量/信号状态过期时间 |

最终数值由后端配置管理；前端不写死业务阈值。

---

## 15. 对车机端 API 的 prerequisite 变更

为保证家长端数据可读，以下变更需要在《车机学习与互动 API 设计》中同步补充：

1. **设备状态上报**：车机/设备端需通过遥测事件或心跳接口上报 `battery_level`、`signal_strength`、`connection_type`、`current_zone`；
2. **设备类型字段**：登录和设备信息中增加 `device_type`（`car` / `robot`）；
3. **非学习任务完成**：增加 `POST /v1/api/car/today-tasks/{task_id}/complete` 用于 `lifestyle` / `sports` / `custom` 任务；
4. **任务分类字段**：`today-tasks` 响应中增加 `task_category`，`learning` 类保留 `module`，其他类 `module=null`。

---

## 16. OpenAPI 交付物

已导出 OpenAPI 3.0 草案文件：

```text
docs/parent-openapi.yaml
```

说明：

- OpenAPI 文件覆盖 REST 接口、统一响应、请求体、关键枚举、常用示例和鉴权方式。
- 家长端与车机端共享同一套学习模块枚举和配置快照结构，OpenAPI 中通过 `$ref` 复用相关定义。
