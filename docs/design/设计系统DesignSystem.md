# 设计系统 Design System

> AI陪伴机器人家长端 · 微信小程序 · 390×844
> 提取自：AI陪伴机器人家长端.pen

---

## 一、品牌色彩 Colors

### 主色调 Primary

| Token | 色值 | 用途 |
|-------|------|------|
| `$primary` | `#316AFD` | 主按钮、选中态、图标高亮 |
| `$secondary` | `#4075FF` | 次要按钮、渐变辅助 |
| `$light-blue` | `#84A6FD` | 装饰元素、头像底色 |
| `$primary-dark` | `#2855CC` | 按钮按下态 |

### 语义色 Semantic

| Token | 色值 | 用途 |
|-------|------|------|
| `$success` | `#ACE828` | 成功状态、已完成、绿色按钮 |
| `$accent-green` | `#ACE828` | 同 `$success`，用于强调色点缀（别名） |
| `$warning` | `#FFB547` | 警告状态、进行中 |
| `$danger` | `#FF6B6B` | 危险操作、删除、退出 |
| `$disabled` | `#C4C9D4` | 禁用态文字/边框 |

### 背景色 Background

| Token | 色值 | 用途 |
|-------|------|------|
| `$background` | `#F6F8FF` | 页面主背景 |
| `$card` | `#FFFFFF` | 卡片、列表项、Sheet、Dialog |
| `$overlay` | `#00000066` | 弹窗蒙层（40% 黑） |
| `$divider` | `#E8EDF7` | 分割线 |
| `$skeleton` | `#E8EDF7` | 骨架屏占位 |

### 文字色 Text

| Token | 色值 | 用途 |
|-------|------|------|
| `$text-primary` | `#1F2937` | 标题、正文 |
| `$text-secondary` | `#6B7280` | 辅助文字、描述 |
| `$text-white` | `#FFFFFF` | 深色背景上的文字 |

### 标签色 Tag Backgrounds

| Token | 色值 | 用途 |
|-------|------|------|
| `$tag-blue-bg` | `#EBF0FF` | 蓝色标签底色 |
| `$tag-green-bg` | `#F0F9E0` | 绿色标签底色（成功） |
| `$tag-warning-bg` | `#FFF4E0` | 黄色标签底色（警告） |
| `$tag-danger-bg` | `#FFEDED` | 红色标签底色（危险） |

---

## 二、字体排版 Typography

### 字体族

| Token | 值 |
|-------|-----|
| `$font-family` | `Noto Sans SC` |

### 字号

| Token | 值 | 用途 |
|-------|-----|------|
| `$font-size-xs` | 10 | Tab Bar 标签 |
| `$font-size-sm` | 12 | 辅助说明 |
| `$font-size-base` | 14 | 正文、列表项 |
| `$font-size-md` | 16 | 卡片标题 |
| `$font-size-lg` | 18 | Sheet/Dialog 标题 |
| `$font-size-xl` | 20 | 页面大标题 |
| `$font-size-2xl` | 24 | 数值展示 |
| `$font-size-3xl` | 28 | 环形图中心数值 |

### 字重

| 使用场景 | 字重 |
|---------|------|
| 大标题、数值 | 700（Bold） |
| 标题、Tab 选中 | 600（SemiBold） |
| 正文、列表 | 500（Medium）或 400（Normal） |
| 辅助说明 | 400（Normal） |

---

## 三、间距 Spacing

| Token | 值 | 用途 |
|-------|-----|------|
| `$spacing-xs` | 4 | 极小间隙 |
| `$spacing-sm` | 8 | 标签内边距、紧凑 gap |
| `$spacing-md` | 12 | 列表项间隙 |
| `$spacing-base` | 16 | 卡片 padding、常规 gap |
| `$spacing-lg` | 20 | 段落间距 |
| `$spacing-xl` | 24 | 区块间距 |
| `$spacing-2xl` | 32 | 大区块间距 |
| `$spacing-3xl` | 40 | 页面级间距 |
| `$spacing-4xl` | 48 | 超大间距 |

---

## 四、圆角 Border Radius

| Token | 值 | 用途 |
|-------|-----|------|
| `$radius-sm` | 8 | 输入框、小卡片 |
| `$radius-md` | 16 | 任务卡片、列表项 |
| `$radius-lg` | 24 | 大卡片、Sheet 顶部 |
| `$radius-pill` | 100 | 按钮、标签、头像、开关 |

---

## 五、阴影 Effects

| 场景 | blur | color | offset | spread |
|------|------|-------|--------|--------|
| 卡片阴影 | 12px | `#0000000A` (4%黑) | y:2 | — |
| 按钮阴影 | 16px | `#316AFD33` (20%蓝) | y:4 | — |
| Bottom Sheet | 20px | `#0000001A` (10%黑) | y:-4 | — |
| Dialog | 24px | `#0000001A` (10%黑) | y:8 | — |
| Toast | 28px | `#00000026` (15%黑) | y:8 | — |
| Switch Thumb | 6+8px | `#316AFD33` / `#316AFD1A` | y:2 | 2px |
| 插画元素 | 20px | `#316AFD40` (25%蓝) | y:6 | — |

---

## 六、组件 Components（共 20 个）

### 6.1 Status Bar（状态栏）

```
尺寸：390 × 44
布局：horizontal, justifyContent: space_between, alignItems: center
填充：$card
内边距：top 12, right 24, bottom 0, left 24
内容：时间文字（9:41）+ 信号/WiFi/电量图标
```

| 属性 | 子元素 | 值 |
|------|--------|-----|
| 时间 | Text "9:41" | fontSize 14, fontWeight 600, `$text-primary` |
| 信号 | Icon "signal" | 16×16, `$text-primary` |
| WiFi | Icon "wifi" | 16×16, `$text-primary` |
| 电量 | Icon "battery-full" | 16×16, `$text-primary` |
| 图标间隙 | gap | 6 |

**实例覆写**：深色页面（看护/P12/登录）需将全部文字和图标色覆写为 `$text-white`。

---

### 6.2 Navigation Bar（导航栏）

```
尺寸：390 × 56
布局：horizontal, justifyContent: space_between, alignItems: center
填充：$card
内边距：vertical 0, horizontal 16
```

| 属性 | 子元素 | 值 |
|------|--------|-----|
| 返回箭头 | Icon "chevron-left" | 24×24, `$text-primary` |
| 标题 | Text "页面标题" | fontSize 17, fontWeight 600, `$text-primary` |
| 更多按钮 | Icon "more-horizontal" | 24×24, `$text-primary` |

> 注：此组件定义但实际页面中未使用 ref，各页手写内联导航。

---

### 6.3 Tab Bar（底部导航）

```
尺寸：390 × 80
布局：horizontal, justifyContent: space_around, alignItems: center
填充：$card
内边距：top 8, right 16, bottom 24, left 16
```

| Tab | Icon | Label | 默认状态 |
|-----|------|-------|---------|
| 首页 | "house" 24×24 | "首页" | `$primary` fill + fontWeight 600 |
| 看护 | "video" 24×24 | "看护" | `$text-secondary` fill + fontWeight normal |
| 报告 | "chart-bar" 24×24 | "报告" | `$text-secondary` fill + fontWeight normal |
| 我的 | "user" 24×24 | "我的" | `$text-secondary` fill + fontWeight normal |

**实例覆写**：通过 `descendants` 切换活跃 Tab 的 icon/label 颜色和字重。

---

### 6.4 Button Primary（主按钮）

```
宽度：auto（fit_content）
内边距：12 24
圆角：$radius-pill（100）
填充：$primary
阴影：blur 16, #316AFD33, y:4
```

| 子元素 | 值 |
|--------|-----|
| Icon | 18×18, `$text-white`, 可选隐藏 |
| Label | fontSize 14, fontWeight 600, `$text-white` |
| gap | 8 |

**实例覆写**：`width: "fill_container"` 铺满、`fill: "$danger"` 危险按钮。

---

### 6.5 Button Secondary（次要按钮）

```
内边距：12 24
圆角：$radius-pill
填充：$tag-blue-bg
```

| 子元素 | 值 |
|--------|-----|
| Icon | 18×18, `$primary`, 可选隐藏 |
| Label | fontSize 14, fontWeight 600, `$primary` |
| gap | 8 |

---

### 6.6 Card（卡片）

```
宽度：358
圆角：$radius-lg（24）
填充：$card
内边距：16
阴影：blur 12, #0000000A, y:2
布局：vertical, gap 12
```

| 子元素 | 值 |
|--------|-----|
| Card Header | horizontal, title fontSize 16 fontWeight 600 `$text-primary` + chevron-right 20×20 |
| Card Body | vertical, gap 8, text fontSize 14 `$text-secondary` |

---

### 6.7 Input（输入框）

```
尺寸：358 × 48
圆角：$radius-sm（8）
填充：#F3F4F6
内边距：0 16
gap：8
```

| 子元素 | 值 |
|--------|-----|
| Search Icon | 18×18, `$text-secondary` |
| Placeholder | fontSize 14, `$disabled` |

---

### 6.8 Tag（标签）

```
内边距：4 12
圆角：$radius-pill
填充：$tag-blue-bg
```

| 子元素 | 值 |
|--------|-----|
| Label | fontSize 12, fontWeight 500, `$primary` |

---

### 6.9 Badge（角标）

```
尺寸：20 × 20
圆角：$radius-pill
填充：$danger
```

| 子元素 | 值 |
|--------|-----|
| Count | fontSize 10, fontWeight 600, `$text-white` |

---

### 6.10 Switch（开关）

```
尺寸：48 × 28
圆角：14
填充：$primary
布局：none（绝对定位子元素）
```

| 子元素 | 值 |
|--------|-----|
| Track | ellipse, 40×20, innerRadius 0.8 |
| Thumb | ellipse, 26×26, `$text-white`, shadow blur 6+8 |

---

### 6.11 Avatar（头像）

```
尺寸：48 × 48
圆角：$radius-pill
填充：$light-blue
clip：true
```

| 子元素 | 值 |
|--------|-----|
| Icon | "user" 24×24, `$text-white` |

---

### 6.12 Progress Ring（进度环）

```
尺寸：120 × 120
布局：none
```

| 子元素 | 值 |
|--------|-----|
| BG Ring | ellipse 120×120, innerRadius 0.87, stroke `$divider` 8px |
| Fill Ring | ellipse 120×120, innerRadius 0.87, stroke `$primary` 8px, sweepAngle 控制进度 |
| Center Text | vertical layout, 值 fontSize 28 fontWeight 700, 标签 fontSize 12 |

---

### 6.13 Progress Bar（进度条）

```
尺寸：240 × 8
圆角：4
填充：$divider
布局：none
```

| 子元素 | 值 |
|--------|-----|
| Fill | rectangle, 高度 8, `$primary`, 宽度 = 百分比 |

---

### 6.14 Empty State（空状态）

```
宽度：358
高度：280
布局：vertical, justifyContent: center, gap: 16
```

| 子元素 | 值 |
|--------|-----|
| 插图 | 120×120, `$tag-blue-bg` 圆底 + "inbox" icon |
| 标题 | fontSize 16, fontWeight 600, `$text-primary` |
| 描述 | fontSize 14, `$text-secondary` |
| 操作按钮 | ref Button Primary, 文字改为 "去操作" |

---

### 6.15 Skeleton Card（骨架屏）

```
宽度：358
圆角：$radius-lg
填充：$card
内边距：16
gap：12
```

| 子元素 | 值 |
|--------|-----|
| Row | horizontal, gap 12, avatar 40×40 ellipse `$skeleton` + text placeholders |
| Block | rectangle, 高度 32, 圆角 8, `$skeleton` |

---

### 6.16 Joystick（摇杆）

```
尺寸：120 × 120
布局：none
```

| 子元素 | 值 |
|--------|-----|
| BG | ellipse 120×120, `#F3F4F6`, stroke `$divider` 1px |
| Thumb | ellipse 50×50, `$primary`, shadow blur 8 `#316AFD40` y:2 |
| Arrows ×4 | chevron-up/down/left/right, 16×16, `$text-secondary` |

---

### 6.17 Bottom Sheet（底部弹出）

```
宽度：390
圆角：顶部 24，底部 0
填充：$card
内边距：top 12, right 16, bottom 32, left 16
阴影：blur 20, #0000001A, y:-4
布局：vertical, gap 16
```

| 子元素 | 值 |
|--------|-----|
| Handle | 居中, rectangle 40×4, 圆角 2, `$divider` |
| Header | space_between, title fontSize 18 fontWeight 600, close icon "x" 24×24 |
| Content | 180px 内容区 |

---

### 6.18 Dialog（弹窗）

```
宽度：300
圆角：$radius-lg
填充：$card
内边距：24
阴影：blur 24, #0000001A, y:8
布局：vertical, alignItems: center, gap 16
```

| 子元素 | 值 |
|--------|-----|
| Title | fontSize 18, fontWeight 600, `$text-primary` |
| Message | fontSize 14, `$text-secondary`, textAlign center |
| Buttons | horizontal, gap 12, 取消（Secondary）+ 确定（Primary/Danger） |

---

### 6.19 DanZai（蛋仔-活跃态）

```
尺寸：64 × 64
布局：none
```

组成：白色椭圆身体(52×60, stroke `$light-blue` 2px) + 圆眼(6×7, `$text-primary`) + 粉色腮红(8×5, #FFB6C1) + 红色嘴巴(8×4, #FF8A80) + 高光椭圆(#FFFFFF33, 旋转-20°)

---

### 6.20 DanZai Sleep（蛋仔-睡眠态）

```
尺寸：64 × 64
布局：none
```

与活跃态区别：闭眼（矩形 6×2 替代椭圆）+ 粉色圆形嘴巴(6×3) + 文字"Z"(fontSize 10, `$light-blue`)

---

## 七、通用布局规则

### 页面模板

| 页面类型 | Status Bar | 导航 | 内容区 | Tab Bar |
|---------|-----------|------|--------|---------|
| Tab 主页 | ✅ | Header（无返回） | `height: fill_container` | ✅ |
| 子页面 | ✅ | ← 返回 + 标题 | `height: fill_container` | ❌ |
| Bottom Sheet | ✅（白色文字） | 首页背景 + 蒙层 | Sheet 底部弹出 | ✅（首页高亮） |
| Dialog | ✅ | 基础页 + 蒙层 | Dialog 居中 | 视页面而定 |
| 登录/引导 | ✅/❌ | 无 | 品牌展示 + 按钮 | ❌ |

### 内容区规范

- 左右 padding：16px（`$spacing-base`）
- 卡片宽度：358px（390 - 16×2）
- 卡片间距：12-16px
- 卡片填充：`$card` + 阴影
- 页面背景：`$background`

### 图标

- 使用 Lucide 图标库
- 常规尺寸：24×24（导航）、20×20（卡片箭头）、18×18（按钮内）、16×16（状态栏）
- 颜色：`$text-primary`（默认）、`$text-secondary`（次要）、`$text-white`（深色背景上）

---

## 八、CSS 变量速查

```css
:root {
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
  --color-skeleton: #E8EDF7;
  --color-text-primary: #1F2937;
  --color-text-secondary: #6B7280;
  --color-text-white: #FFFFFF;
  --color-tag-blue-bg: #EBF0FF;
  --color-tag-green-bg: #F0F9E0;
  --color-tag-warning-bg: #FFF4E0;
  --color-tag-danger-bg: #FFEDED;

  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 12px;
  --spacing-base: 16px;
  --spacing-lg: 20px;
  --spacing-xl: 24px;
  --spacing-2xl: 32px;
  --spacing-3xl: 40px;
  --spacing-4xl: 48px;

  /* Font Size */
  --font-size-xs: 10px;
  --font-size-sm: 12px;
  --font-size-base: 14px;
  --font-size-md: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 20px;
  --font-size-2xl: 24px;
  --font-size-3xl: 28px;

  /* Border Radius */
  --radius-sm: 8px;
  --radius-md: 16px;
  --radius-lg: 24px;
  --radius-pill: 100px;

  /* Font */
  --font-family: 'Noto Sans SC', sans-serif;
}
```
