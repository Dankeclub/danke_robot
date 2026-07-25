# 👨‍👩‍👧 家长端 · 微信小程序

## 代码导航

```text
parent/
│
│  📲 入口层（自动加载，一般不改）
│  ├── app.js          ← 小程序启动、全局数据
│  ├── app.json        ← 页面注册、窗口配置
│  ├── app.wxss        ← 全局样式
│  ├── project.config.json  ← 微信开发者工具配置
│  └── sitemap.json    ← 微信搜索索引
│
│  📄 页面层 — 15 个功能入口
│  │
│  ├── login/            ← 微信登录                       · 首次进入
│  ├── bind/             ← 扫码绑定机器人                  · 设备绑定流程
│  ├── home/             ← 首页仪表盘                      · ⭐ 核心页
│  │                        孩子状态 / 今日数据 / AI 摘要
│  ├── monitor/          ← 实时视频 + 机器人控制            · 看孩子
│  ├── behavior/         ← 行为分析数据                    · 坐姿 / 专注度
│  ├── learning/         ← 学习进度追踪                    · 各科进度
│  ├── goal/             ← 成长目标设定                    · 学习目标
│  ├── report/           ← 成长报告列表                    · 周报 / 月报
│  ├── report-detail/    ← 报告详情                        · 单击进入
│  ├── usage/            ← 使用时长统计                    · 屏幕时间
│  ├── device/           ← 设备管理                        · 绑定 / 解绑
│  ├── child-info/       ← 孩子档案                        · 编辑信息
│  ├── notifications/    ← 消息通知列表                    · 系统消息
│  ├── notification-settings/ ← 通知偏好设置               · 开关
│  └── profile/          ← 个人中心                        · 我的
│
│  🧩 组件层 — 被页面引用，不用直接改
│  ├── custom-tabbar/    ← 底部导航栏 (首页/学习/报告/监控/我的)
│  ├── danke-mascot/     ← 蛋仔吉祥物 (不同状态动画)
│  └── icon/             ← 通用图标组件
│
│  🛠️ 工具层
│  ├── utils/router.js       ← 页面跳转封装
│  ├── utils/design-tokens.js ← 颜色/字号/间距 变量
│  └── icons/ (80+ SVG)      ← 图标素材库
│
│  ⚙️ 平台配置
│  └── .cloudbase/       ← 微信云开发配置 (不要删)
```

## 页面间跳转关系

```text
login ──▶ bind ──▶ child-info ──▶ home ←── 核心枢纽
                                    │
         ┌──────────────────────────┼──────────────────────┐
         │              │           │          │           │
         ▼              ▼           ▼          ▼           ▼
      monitor       behavior     learning    report      usage
         │                          │          │
         │                          ▼          ▼
         │                       goal      report-detail
         │
         ▼
      device ──▶ device 内部流转
      
      home 底部 TabBar ──▶ 首页 / 学习 / 报告 / 监控 / 我的(profile)
```
