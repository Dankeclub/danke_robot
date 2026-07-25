// 报告页 — 周报

// 获取周一的日期字符串 (YYYY-MM-DD)
function getMonday(d) {
  const date = new Date(d)
  const day = date.getDay()
  const diff = day === 0 ? -6 : 1 - day
  date.setDate(date.getDate() + diff)
  return formatDateKey(date)
}

function formatDateKey(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function formatWeekLabel(mondayStr) {
  const [y, m, d] = mondayStr.split('-').map(Number)
  const mon = new Date(y, m - 1, d)
  const sun = new Date(y, m - 1, d + 6)
  const fmt = (dt) => `${dt.getMonth() + 1} 月 ${dt.getDate()} 日`
  return `${fmt(mon)} — ${fmt(sun)}`
}

function formatShortLabel(mondayStr) {
  const [y, m, d] = mondayStr.split('-').map(Number)
  return `${m} 月第${Math.ceil(d / 7)}周`
}

// 生成迷你柱状图 (确定性, 基于 seed, 返回 rpx 值)
function generateSparkBars(count, minH, maxH, hiThreshold, seed) {
  const bars = []
  const range = maxH - minH
  for (let i = 0; i < count; i++) {
    const h = minH + ((seed * (i + 1) * 7 + i * 13) % range)
    bars.push({ h, hi: h > hiThreshold })
  }
  return bars
}

// 生成模拟周报数据
function generateWeekData(mondayStr) {
  const base = parseInt(mondayStr.split('-')[2]) || 16
  const seed = (base * 7 + 3) % 20
  return {
    highlights: [
      seed > 10 ? '数学心算连续满分' : '诗词背诵表现突出',
      seed > 12 ? `专注度提升 ${seed}%` : `正确率提升 ${seed}%`
    ],
    tips: [
      seed < 8 ? '坐姿需关注' : '阅读时长偏短',
      seed < 10 ? '英语口语可加强' : '科学实验动手不足'
    ],
    aiSummary: seed > 10
      ? '小宇本周学习状态持续向好，数学表现尤为突出。建议下周适当增加英语听力练习。'
      : '小宇本周整体表现平稳，英语方面进步明显。建议下周多关注科学实验环节，培养动手能力。',
    metrics: {
      dailyUsage: 65 + seed,
      accuracy: 80 + seed,
      knowledge: 14 + Math.floor(seed / 2)
    },
    sparkBars: {
      dailyUsage: generateSparkBars(7, 14, 48, 30, seed),
      accuracy: generateSparkBars(5, 14, 48, 30, seed),
      knowledge: generateSparkBars(3, 16, 48, 30, seed)
    }
  }
}

// 生成连续数周的周报列表
function buildWeeks() {
  const today = new Date()
  const currentMonday = getMonday(today)
  const weeks = []
  // 生成最近 8 周的记录
  for (let i = 0; i < 8; i++) {
    const d = new Date(today)
    d.setDate(d.getDate() - i * 7)
    const key = getMonday(d)
    weeks.push({
      key,
      label: i === 0 ? '本周' : i === 1 ? '上周' : formatShortLabel(key),
      date: formatWeekLabel(key),
      active: i === 0
    })
  }
  return { weeks, currentKey: currentMonday }
}

Page({
  data: {
    weekLabel: '',
    historyWeeks: [],
    currentWeekKey: '',
    // 当前展示的数据
    highlights: [],
    tips: [],
    aiSummary: '',
    metrics: { dailyUsage: 0, accuracy: 0, knowledge: 0 },
    sparkBars: { dailyUsage: [], accuracy: [], knowledge: [] }
  },

  onLoad() {
    const { weeks, currentKey } = buildWeeks()
    const weekData = generateWeekData(currentKey)
    this.setData({
      weekLabel: formatWeekLabel(currentKey),
      historyWeeks: weeks,
      currentWeekKey: currentKey,
      highlights: weekData.highlights,
      tips: weekData.tips,
      aiSummary: weekData.aiSummary,
      metrics: weekData.metrics,
      sparkBars: weekData.sparkBars,
      allWeekKeys: weeks.map(w => w.key),
      allWeekLabels: weeks.map(w => w.date)
    })
  },

  // 加载指定周的数据
  loadWeek(weekKey) {
    const weekData = generateWeekData(weekKey)
    const historyWeeks = this.data.historyWeeks.map(w => ({
      ...w,
      active: w.key === weekKey
    }))
    this.setData({
      weekLabel: formatWeekLabel(weekKey),
      currentWeekKey: weekKey,
      historyWeeks,
      highlights: weekData.highlights,
      tips: weekData.tips,
      aiSummary: weekData.aiSummary,
      metrics: weekData.metrics,
      sparkBars: weekData.sparkBars
    })
  },

  // 上一周
  onPrevWeek() {
    const keys = this.data.allWeekKeys
    const idx = keys.indexOf(this.data.currentWeekKey)
    if (idx < keys.length - 1) {
      this.loadWeek(keys[idx + 1])
    } else {
      wx.showToast({ title: '没有更早的周报了', icon: 'none' })
    }
  },

  // 下一周
  onNextWeek() {
    const keys = this.data.allWeekKeys
    const idx = keys.indexOf(this.data.currentWeekKey)
    if (idx > 0) {
      this.loadWeek(keys[idx - 1])
    } else {
      wx.showToast({ title: '已是本周', icon: 'none' })
    }
  },

  // 点击日期标签 → 弹出周选择器
  onWeekLabelTap() {
    const that = this
    const labels = this.data.allWeekLabels
    wx.showActionSheet({
      itemList: labels.length > 6 ? labels.slice(0, 6) : labels,
      success(res) {
        const keys = that.data.allWeekKeys
        if (keys[res.tapIndex]) {
          that.loadWeek(keys[res.tapIndex])
        }
      }
    })
  },

  // 点击历史周报列表项
  onSelectWeek(e) {
    const idx = Number(e.currentTarget.dataset.index)
    const key = this.data.allWeekKeys[idx]
    if (key) {
      this.loadWeek(key)
      wx.pageScrollTo({ scrollTop: 0, duration: 300 })
    }
  },

  // 跳转使用时长详情
  goUsage() {
    wx.navigateTo({ url: '/pages/usage/usage' })
  }
})
