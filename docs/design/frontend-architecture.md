# 前端架构设计文档

> AI陪伴机器人家长端 · 微信原生小程序
> 基于：AI陪伴机器人家长端.pen 设计稿 + PRD V1.0

---

## 一、技术栈说明

| 类别 | 技术选型 | 说明 |
|------|---------|------|
| 框架 | 微信原生小程序 | 基础库 2.30+，无第三方框架依赖 |
| 模板 | WXML | 微信模板语言，支持数据绑定、条件渲染、列表渲染 |
| 样式 | WXSS | 支持 rpx 适配，全局变量通过 CSS Variables 管理 |
| 逻辑 | JavaScript（ES6+） | async/await、解构赋值、模块化导入 |
| 组件化 | 微信原生 Component | 自定义组件，支持 properties / observers / lifetimes |
| 状态管理 | 全局 Store（轻量自研） | 基于 getApp().globalData + EventBus |
| 网络请求 | wx.request 封装 | 统一拦截器、Token 管理、错误处理 |
| 实时通信 | WebSocket | 设备状态推送、实时看护视频流控制 |
| 图表 | wx-canvas / 原生 Canvas 2D | 环形图、柱状图、进度条 |
| 地图/定位 | 无 | 当前版本不涉及 |

---

## 二、项目目录结构

```
ai-companion-parent/
├── app.js                    # 小程序入口，全局生命周期
├── app.json                  # 全局配置（页面路由、tabBar、window）
├── app.wxss                  # 全局样式、CSS 变量定义
├── project.config.json       # 项目配置
├── sitemap.json              # 搜索收录配置
│
├── pages/                    # 页面目录
│   ├── index/                # P01 首页
│   ├── monitor/              # P03 看护页
│   ├── report/               # P02 报告页
│   ├── mine/                 # P05 我的
│   ├── learning-track/       # P04 学习追踪
│   ├── notification/         # P06 通知中心
│   ├── usage-duration/       # P07 使用时长
│   ├── behavior-analysis/    # P08 行为分析
│   ├── device-manage/        # P09 设备管理
│   ├── notification-settings/# P10 通知设置
│   ├── learning-goal/        # P11 学习目标
│   ├── device-unbind/        # P14 设备未绑定
│   ├── device-bindstep/      # P18 设备配网绑定
│   ├── login/                # P15 微信授权登录
│   ├── onboarding/           # P16 欢迎引导
│   ├── bind-child/           # P17 绑定孩子信息
│   ├── edit-profile/         # P19 编辑资料
│   ├── report-detail/        # P20 报告详情
│   ├── help-center/          # P21 帮助中心
│   ├── about/                # P22 关于我们
│   ├── child-manage/         # P23 孩子管理
│   ├── device-info/          # P24 设备信息详情
│   ├── connect-log/          # P25 连接记录
│   ├── firmware-update/      # P26 固件更新
│   ├── task-detail/          # P27 任务详情
│   ├── behavior-detail/      # P28 行为详情
│   ├── subject-detail/       # P29 学科详情
│   ├── learning-record/      # P30 学习记录详情
│   ├── score-detail/         # P31 评分维度详情
│   └── all-tasks/            # P32 全部任务
│
├── components/               # 公共组件
│   ├── status-bar/           # C01 状态栏
│   ├── nav-bar/              # C02 自定义导航栏
│   ├── tab-bar/              # C03 自定义 TabBar
│   ├── btn-primary/          # C04 主按钮
│   ├── btn-secondary/        # C05 次要按钮
│   ├── card/                 # C06 卡片容器
│   ├── input-field/          # C07 输入框
│   ├── tag/                  # C08 标签
│   ├── badge/                # C09 角标
│   ├── switch-toggle/        # C10 开关
│   ├── avatar/               # C11 头像
│   ├── progress-ring/        # C12 进度环
│   ├── progress-bar/         # C13 进度条
│   ├── empty-state/          # C14 空状态
│   ├── skeleton/             # C15 骨架屏
│   ├── joystick/             # C16 摇杆控制
│   ├── bottom-sheet/         # C17 底部弹出面板
│   ├── dialog/               # C18 对话框弹窗
│   ├── danzai/               # C19 蛋仔形象（活跃/睡眠）
│   ├── toast/                # 轻提示
│   └── loading/              # 加载指示器
│
├── services/                 # 服务层（API 调用）
│   ├── request.js            # 请求基础封装
│   ├── auth.js               # 登录/Token/用户信息
│   ├── device.js             # 设备绑定/管理/配网
│   ├── child.js              # 孩子信息管理
│   ├── task.js               # 任务派发/查询
│   ├── report.js             # 成长报告
│   ├── learning.js           # 学习追踪/数据
│   ├── behavior.js           # 行为分析
│   ├── notification.js       # 通知中心
│   └── websocket.js          # WebSocket 长连接
│
├── utils/                    # 工具函数
│   ├── event-bus.js          # 全局事件总线
│   ├── storage.js            # 本地缓存封装
│   ├── format.js             # 格式化（时间、数字、文件大小）
│   ├── validator.js          # 表单校验
│   ├── throttle.js           # 节流/防抖
│   ├── router.js             # 路由跳转封装
│   └── constants.js          # 常量定义
│
├── store/                    # 全局状态
│   ├── index.js              # Store 初始化
│   ├── user.js               # 用户状态
│   ├── device.js             # 设备状态
│   └── child.js              # 孩子状态
│
├── assets/                   # 静态资源
│   ├── icons/                # 图标（SVG 转 base64 / 图片）
│   ├── images/               # 插图、品牌图
│   └── lottie/               # 动画文件（可选）
│
└── config/                   # 配置文件
    ├── env.js                # 环境变量（dev/staging/prod）
    └── api.js                # API 基础路径配置
```

---

## 三、页面结构

### 3.1 页面与路由映射

```json
// app.json - tabBar 配置
{
  "tabBar": {
    "custom": true,
    "color": "#6B7280",
    "selectedColor": "#316AFD",
    "list": [
      { "pagePath": "pages/index/index", "text": "首页", "iconPath": "assets/icons/home.png", "selectedIconPath": "assets/icons/home-active.png" },
      { "pagePath": "pages/monitor/index", "text": "看护", "iconPath": "assets/icons/video.png", "selectedIconPath": "assets/icons/video-active.png" },
      { "pagePath": "pages/report/index", "text": "报告", "iconPath": "assets/icons/chart.png", "selectedIconPath": "assets/icons/chart-active.png" },
      { "pagePath": "pages/mine/index", "text": "我的", "iconPath": "assets/icons/user.png", "selectedIconPath": "assets/icons/user-active.png" }
    ]
  }
}
```

### 3.2 页面分类

| 类型 | 页面 | 路由方式 |
|------|------|---------|
| Tab 页 | 首页、看护、报告、我的 | `wx.switchTab` |
| 子页面 | P04-P32 全部子页面 | `wx.navigateTo` |
| 登录/引导 | P15、P16、P17、P18 | `wx.redirectTo`（不可返回） |
| 弹窗层 | Dialog、Bottom Sheet、Toast | 组件内 show/hide 控制 |

### 3.3 单个页面文件结构

```
pages/index/
├── index.wxml              # 模板
├── index.wxss              # 页面样式
├── index.js                # 页面逻辑
└── index.json              # 页面配置（引用组件）
```

---

## 四、组件结构

### 4.1 组件与设计稿对应关系

| 组件 | 设计稿 ID | 复用场景 |
|------|-----------|---------|
| nav-bar | `KIZRh` | 所有子页面顶部导航 |
| tab-bar | `MzjHm` | 4 个 Tab 主页面底部 |
| btn-primary | `pAZUM` | 提交、确认、主操作 |
| btn-secondary | `OxCwA` | 次要操作、取消 |
| card | `n60l4` | 通用内容卡片容器 |
| input-field | `QlgvB` | 搜索框、表单输入 |
| tag | `brzbw` | 状态标签、分类标签 |
| badge | `L7Yx2q` | 通知角标 |
| switch-toggle | `mtx5U` | 通知设置开关 |
| avatar | `h0jeI` | 用户/孩子头像 |
| progress-ring | `o0eUPp` | 学习进度环形图 |
| progress-bar | `uGU9g` | 学科进度条 |
| empty-state | `iBUE8` | 无数据空状态 |
| skeleton | `CDKGD` | 页面加载骨架屏 |
| joystick | `mRUL3` | 看护页机器人控制 |
| bottom-sheet | `T4VII` | 蛋仔派任务面板 |
| dialog | `ufdvh` | 退出登录/解绑确认 |
| danzai | `SvBqT` / `MjRxt` | 品牌形象（活跃/睡眠） |

### 4.2 组件通信规范

```
┌─────────────────────────────────────────────┐
│  Page（页面）                                 │
│                                             │
│  ┌──────────┐    properties     ┌────────┐ │
│  │ Component│ ◄──────────────── │  Page  │ │
│  │          │ ────────────────► │  Data  │ │
│  └──────────┘    triggerEvent   └────────┘ │
│                                             │
└─────────────────────────────────────────────┘
```

- **父 → 子**：通过 `properties` 传递数据
- **子 → 父**：通过 `triggerEvent` 触发自定义事件
- **跨组件**：通过 EventBus 或 Store 订阅

### 4.3 组件示例（btn-primary）

```javascript
// components/btn-primary/index.js
Component({
  properties: {
    text: { type: String, value: '按钮' },
    icon: { type: String, value: '' },
    disabled: { type: Boolean, value: false },
    block: { type: Boolean, value: false },
    type: { type: String, value: 'primary' } // primary | danger
  },
  methods: {
    handleTap() {
      if (!this.data.disabled) {
        this.triggerEvent('tap')
      }
    }
  }
})
```

---

## 五、页面通信

### 5.1 通信方式一览

| 场景 | 方式 | 示例 |
|------|------|------|
| 父页面 → 子页面 | URL 参数 + `onLoad(options)` | 任务详情页接收 taskId |
| 子页面 → 父页面 | EventBus / EventChannel | 编辑资料后刷新我的页 |
| 兄弟组件 | EventBus 发布-订阅 | 派任务成功后刷新首页任务列表 |
| 全局广播 | Store 状态变更 + 监听 | 设备离线状态全局更新 |
| 弹窗结果 | 组件事件回调 | Dialog confirm/cancel |

### 5.2 EventBus 实现

```javascript
// utils/event-bus.js
class EventBus {
  constructor() { this._events = {} }
  on(event, fn) {
    (this._events[event] || (this._events[event] = [])).push(fn)
  }
  off(event, fn) {
    const fns = this._events[event]
    if (fns) this._events[event] = fns.filter(f => f !== fn)
  }
  emit(event, ...args) {
    (this._events[event] || []).forEach(fn => fn(...args))
  }
}
module.exports = new EventBus()
```

### 5.3 EventChannel（页面间）

```javascript
// 从首页跳转到任务详情，并监听返回结果
wx.navigateTo({
  url: '/pages/task-detail/index?id=123',
  events: {
    taskCompleted(data) {
      // 子页面返回后刷新列表
      this.refreshTaskList()
    }
  }
})
```

---

## 六、数据流

### 6.1 数据流架构

```
┌─────────────────────────────────────────────────────┐
│                     View (WXML)                      │
│                        │ ▲                           │
│                  bind  │ │ setData                   │
│                        ▼ │                           │
│                   Page / Component                   │
│                        │ ▲                           │
│              call      │ │ callback / Promise        │
│                        ▼ │                           │
│                    Services Layer                    │
│                        │ ▲                           │
│              request   │ │ response                  │
│                        ▼ │                           │
│                   request.js (HTTP)                  │
│                   websocket.js (WS)                  │
│                        │ ▲                           │
│                        ▼ │                           │
│                    Backend API                       │
└─────────────────────────────────────────────────────┘
```

### 6.2 数据流向规则

1. **单向数据流**：数据从 Service → Page data → WXML 渲染，用户操作触发事件回到 Page
2. **setData 最小化**：只更新变化的字段路径，避免全量更新
3. **缓存优先**：列表数据先读本地缓存展示骨架，API 返回后更新
4. **乐观更新**：开关类操作先更新 UI，失败时回滚

---

## 七、API 调用方式

### 7.1 请求基础封装

```javascript
// services/request.js
const { API_BASE_URL } = require('../config/api')
const storage = require('../utils/storage')

function request(options) {
  const token = storage.get('token')
  return new Promise((resolve, reject) => {
    wx.request({
      url: API_BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      success(res) {
        if (res.statusCode === 401) {
          // Token 过期，跳转登录
          wx.redirectTo({ url: '/pages/login/index' })
          return reject({ code: 401, msg: '登录过期' })
        }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          reject(res.data)
        }
      },
      fail: reject
    })
  })
}

module.exports = { get: (url, data) => request({ url, data }),
  post: (url, data) => request({ url, data, method: 'POST' }),
  put: (url, data) => request({ url, data, method: 'PUT' }),
  del: (url, data) => request({ url, data, method: 'DELETE' })
}
```

### 7.2 Service 层示例

```javascript
// services/task.js
const http = require('./request')

module.exports = {
  getTaskList: (params) => http.get('/tasks', params),
  getTaskDetail: (id) => http.get(`/tasks/${id}`),
  sendTasks: (data) => http.post('/tasks/send', data),
  completeTask: (id) => http.put(`/tasks/${id}/complete`)
}
```

### 7.3 页面调用

```javascript
// pages/index/index.js
const taskService = require('../../services/task')

Page({
  data: { tasks: [], loading: true },
  async onLoad() {
    this.loadTasks()
  },
  async loadTasks() {
    this.setData({ loading: true })
    try {
      const res = await taskService.getTaskList({ date: 'today' })
      this.setData({ tasks: res.data, loading: false })
    } catch (e) {
      this.setData({ loading: false })
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  }
})
```

---

## 八、全局状态管理

### 8.1 Store 设计

采用轻量级响应式 Store，不引入第三方库。

```javascript
// store/index.js
const eventBus = require('../utils/event-bus')

const store = {
  state: {
    userInfo: null,
    childInfo: null,
    deviceInfo: null,
    deviceOnline: false,
    unreadCount: 0
  },

  setState(key, value) {
    this.state[key] = value
    eventBus.emit(`store:${key}`, value)
  },

  getState(key) {
    return this.state[key]
  },

  subscribe(key, fn) {
    eventBus.on(`store:${key}`, fn)
    return () => eventBus.off(`store:${key}`, fn)
  }
}

module.exports = store
```

### 8.2 全局状态字段

| 字段 | 类型 | 说明 | 更新时机 |
|------|------|------|---------|
| `userInfo` | Object | 家长信息 | 登录成功/编辑资料 |
| `childInfo` | Object | 孩子信息 | 绑定/编辑孩子 |
| `deviceInfo` | Object | 设备信息 | 绑定设备/WebSocket 推送 |
| `deviceOnline` | Boolean | 设备在线状态 | WebSocket 心跳/事件 |
| `unreadCount` | Number | 未读通知数 | 推送通知/进入通知中心 |

### 8.3 页面中使用

```javascript
// pages/index/index.js
const store = require('../../store/index')

Page({
  data: { deviceOnline: true },
  onLoad() {
    this._unsubscribe = store.subscribe('deviceOnline', (online) => {
      this.setData({ deviceOnline: online })
    })
    this.setData({ deviceOnline: store.getState('deviceOnline') })
  },
  onUnload() {
    this._unsubscribe && this._unsubscribe()
  }
})
```

---

## 九、样式管理

### 9.1 全局 CSS 变量（app.wxss）

```css
page {
  /* Colors */
  --color-primary: #316AFD;
  --color-secondary: #4075FF;
  --color-light-blue: #84A6FD;
  --color-primary-dark: #2855CC;
  --color-success: #ACE828;
  --color-accent-green: #ACE828;
  --color-warning: #FFB547;
  --color-danger: #FF6B6B;
  --color-disabled: #C4C9D4;
  --color-background: #F6F8FF;
  --color-card: #FFFFFF;
  --color-overlay: rgba(0, 0, 0, 0.4);
  --color-divider: #E8EDF7;
  --color-text-primary: #1F2937;
  --color-text-secondary: #6B7280;
  --color-text-white: #FFFFFF;
  --color-tag-blue-bg: #EBF0FF;
  --color-tag-green-bg: #F0F9E0;
  --color-tag-warning-bg: #FFF4E0;
  --color-tag-danger-bg: #FFEDED;

  /* Spacing */
  --spacing-xs: 8rpx;
  --spacing-sm: 16rpx;
  --spacing-md: 24rpx;
  --spacing-base: 32rpx;
  --spacing-lg: 40rpx;
  --spacing-xl: 48rpx;
  --spacing-2xl: 64rpx;
  --spacing-3xl: 80rpx;

  /* Font */
  --font-family: 'Noto Sans SC', -apple-system, sans-serif;
  --font-size-xs: 20rpx;
  --font-size-sm: 24rpx;
  --font-size-base: 28rpx;
  --font-size-md: 32rpx;
  --font-size-lg: 36rpx;
  --font-size-xl: 40rpx;
  --font-size-2xl: 48rpx;
  --font-size-3xl: 56rpx;

  /* Radius */
  --radius-sm: 16rpx;
  --radius-md: 32rpx;
  --radius-lg: 48rpx;
  --radius-pill: 200rpx;

  /* Base */
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  background-color: var(--color-background);
}
```

### 9.2 样式规范

- 使用 `rpx` 单位，设计稿 390px 宽度换算：`1px = 2rpx`
- 颜色统一使用 CSS 变量引用，禁止硬编码色值
- 组件样式使用 `styleIsolation: 'isolated'` 隔离
- 公共工具类放在 `app.wxss`（flex、margin、padding 快捷类）
- 每个页面的 wxss 只写页面特有样式

---

## 十、工具函数

### 10.1 utils 目录说明

| 文件 | 职责 | 关键方法 |
|------|------|---------|
| `format.js` | 数据格式化 | `formatTime`, `formatDuration`, `formatNumber` |
| `validator.js` | 表单验证 | `isPhone`, `isNickname`, `required` |
| `storage.js` | 本地缓存 | `get`, `set`, `remove`, `clear` |
| `router.js` | 路由封装 | `push`, `replace`, `back`, `switchTab` |
| `throttle.js` | 节流防抖 | `throttle`, `debounce` |
| `event-bus.js` | 事件总线 | `on`, `off`, `emit` |
| `constants.js` | 常量定义 | 页面路径、错误码、枚举值 |

### 10.2 路由封装

```javascript
// utils/router.js
const routes = {
  index: '/pages/index/index',
  monitor: '/pages/monitor/index',
  report: '/pages/report/index',
  mine: '/pages/mine/index',
  learningTrack: '/pages/learning-track/index',
  notification: '/pages/notification/index',
  taskDetail: '/pages/task-detail/index',
  // ... 其余页面
}

const TAB_PAGES = ['index', 'monitor', 'report', 'mine']

module.exports = {
  push(name, params = {}) {
    const query = Object.entries(params).map(([k, v]) => `${k}=${v}`).join('&')
    const url = routes[name] + (query ? `?${query}` : '')
    if (TAB_PAGES.includes(name)) {
      wx.switchTab({ url: routes[name] })
    } else {
      wx.navigateTo({ url })
    }
  },
  replace(name, params = {}) {
    const query = Object.entries(params).map(([k, v]) => `${k}=${v}`).join('&')
    wx.redirectTo({ url: routes[name] + (query ? `?${query}` : '') })
  },
  back(delta = 1) {
    wx.navigateBack({ delta })
  }
}
```

---

## 十一、Assets 管理

### 11.1 图标管理

- 使用 Lucide 图标库对应的 SVG 文件
- 小图标（< 10KB）转 base64 内联使用
- 大图标/插图通过 CDN 加载
- TabBar 图标使用 PNG 格式（微信要求）

### 11.2 图片管理

```
assets/
├── icons/
│   ├── home.png / home-active.png       # TabBar 图标
│   ├── video.png / video-active.png
│   ├── chart.png / chart-active.png
│   ├── user.png / user-active.png
│   └── ...
├── images/
│   ├── logo.png                         # 品牌 Logo
│   ├── onboarding-1.png                 # 引导页插图
│   ├── empty-device.png                 # 设备空状态
│   ├── empty-task.png                   # 任务空状态
│   ├── bind-success.png                 # 绑定成功插图
│   └── danzai-*.png                     # 蛋仔形象资源
└── lottie/
    ├── loading.json                     # 加载动画
    └── success.json                     # 成功动画
```

### 11.3 资源加载策略

| 资源类型 | 策略 | 说明 |
|---------|------|------|
| TabBar 图标 | 本地打包 | 微信要求本地资源 |
| 页面小图标 | Base64 内联 | 减少请求 |
| 插图/大图 | CDN + 懒加载 | `<image lazy-load>` |
| Lottie 动画 | 本地 JSON | 首次加载关键动画 |

---

## 十二、Services 管理

### 12.1 服务模块划分

| 模块 | 文件 | 对应页面 | 核心接口 |
|------|------|---------|---------|
| 认证 | `auth.js` | P15-P16 | 微信登录、获取用户信息、刷新 Token |
| 设备 | `device.js` | P09/P14/P18/P24-P26 | 绑定、解绑、配网、状态查询、固件更新 |
| 孩子 | `child.js` | P17/P23 | 创建、编辑、获取孩子信息 |
| 任务 | `task.js` | P01/P12/P27/P32 | 任务列表、派发、详情、完成 |
| 报告 | `report.js` | P02/P20/P31 | 日报、周报、报告详情、评分维度 |
| 学习 | `learning.js` | P04/P07/P29/P30 | 学习数据、学科进度、使用时长 |
| 行为 | `behavior.js` | P08/P28 | 行为分析、行为详情 |
| 通知 | `notification.js` | P06/P10 | 通知列表、已读标记、通知设置 |
| WebSocket | `websocket.js` | 全局 | 设备状态推送、心跳保活 |

### 12.2 WebSocket 管理

```javascript
// services/websocket.js
const store = require('../store/index')
let socketTask = null
let heartbeatTimer = null

module.exports = {
  connect(deviceId) {
    socketTask = wx.connectSocket({ url: `wss://api.example.com/ws?device=${deviceId}` })
    socketTask.onOpen(() => { this.startHeartbeat() })
    socketTask.onMessage((msg) => {
      const data = JSON.parse(msg.data)
      if (data.type === 'device_status') {
        store.setState('deviceOnline', data.online)
      }
    })
    socketTask.onClose(() => {
      store.setState('deviceOnline', false)
      this.stopHeartbeat()
      setTimeout(() => this.connect(deviceId), 5000)
    })
  },
  startHeartbeat() {
    heartbeatTimer = setInterval(() => {
      socketTask.send({ data: JSON.stringify({ type: 'ping' }) })
    }, 30000)
  },
  stopHeartbeat() {
    clearInterval(heartbeatTimer)
  },
  disconnect() {
    socketTask && socketTask.close()
    this.stopHeartbeat()
  }
}
```

---

## 十三、Utils 管理

### 13.1 format.js

```javascript
module.exports = {
  formatTime(date, fmt = 'YYYY-MM-DD HH:mm') { /* ... */ },
  formatDuration(minutes) {
    if (minutes < 60) return `${minutes}分钟`
    const h = Math.floor(minutes / 60)
    const m = minutes % 60
    return m ? `${h}小时${m}分钟` : `${h}小时`
  },
  formatNumber(num) {
    if (num >= 10000) return (num / 10000).toFixed(1) + '万'
    return num.toString()
  }
}
```

### 13.2 storage.js

```javascript
const PREFIX = 'ai_companion_'

module.exports = {
  get(key) {
    try { return wx.getStorageSync(PREFIX + key) }
    catch { return null }
  },
  set(key, value) {
    wx.setStorageSync(PREFIX + key, value)
  },
  remove(key) {
    wx.removeStorageSync(PREFIX + key)
  },
  clear() {
    wx.clearStorageSync()
  }
}
```

### 13.3 constants.js

```javascript
module.exports = {
  DEVICE_STATUS: {
    ONLINE: 'online',
    OFFLINE: 'offline',
    CONNECTING: 'connecting'
  },
  TASK_STATUS: {
    PENDING: 'pending',
    IN_PROGRESS: 'in_progress',
    COMPLETED: 'completed'
  },
  TASK_CATEGORY: {
    LEARNING: 'learning',
    LIFE: 'life',
    PARENT_CHILD: 'parent_child'
  },
  REPORT_TYPE: {
    DAILY: 'daily',
    WEEKLY: 'weekly'
  },
  NOTIFICATION_CATEGORY: {
    ALL: 'all',
    LEARNING: 'learning',
    BEHAVIOR: 'behavior',
    DEVICE: 'device',
    TASK: 'task'
  }
}
```

---

## 十四、项目规范

### 14.1 命名规范

| 类别 | 规则 | 示例 |
|------|------|------|
| 页面目录 | kebab-case | `learning-track/` |
| 组件目录 | kebab-case | `btn-primary/` |
| JS 文件 | kebab-case | `event-bus.js` |
| 变量/函数 | camelCase | `getTaskList` |
| 常量 | UPPER_SNAKE_CASE | `DEVICE_STATUS` |
| CSS 类名 | BEM（block__element--modifier） | `.card__header--active` |
| 自定义事件 | camelCase | `onTaskComplete` |
| data 字段 | camelCase | `deviceOnline` |

### 14.2 文件规范

- 单个 JS 文件不超过 300 行，超出则拆分模块
- 组件 properties 必须声明类型和默认值
- Service 方法必须返回 Promise
- 页面 `onLoad` 中只做初始化，业务逻辑抽取为方法

### 14.3 Git 规范

```
feat: 新增学习追踪页面
fix: 修复设备离线状态未同步问题
style: 调整卡片圆角为 24rpx
refactor: 重构请求拦截器逻辑
docs: 更新前端架构文档
```

### 14.4 性能规范

| 规则 | 说明 |
|------|------|
| setData 最小化 | 只传差异路径，禁止全量 `setData({ ...this.data })` |
| 图片懒加载 | 列表中的图片使用 `lazy-load` |
| 分页加载 | 列表页使用触底加载，每页 20 条 |
| 骨架屏 | 首屏数据未返回时展示 Skeleton 组件 |
| 防抖节流 | 搜索输入防抖 300ms，按钮点击节流 1000ms |
| 预加载 | Tab 页切换时预请求数据 |

### 14.5 安全规范

| 规则 | 说明 |
|------|------|
| Token 存储 | 使用 `wx.setStorageSync` 加密存储 |
| 请求签名 | 敏感接口添加请求签名 |
| XSS 防护 | 禁止 `rich-text` 渲染未过滤的用户输入 |
| 敏感信息 | 孩子信息展示时部分脱敏 |
| 权限控制 | 摄像头/麦克风权限使用前弹窗授权 |
