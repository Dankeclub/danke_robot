// 报告中心

function getMonday(d) {
  var date = new Date(d)
  var day = date.getDay()
  var diff = day === 0 ? -6 : 1 - day
  date.setDate(date.getDate() + diff)
  return formatDateKey(date)
}

function formatDateKey(d) {
  var y = d.getFullYear()
  var m = String(d.getMonth() + 1).padStart(2, '0')
  var day = String(d.getDate()).padStart(2, '0')
  return y + '-' + m + '-' + day
}

function formatWeekLabel(mondayStr) {
  var parts = mondayStr.split('-').map(Number)
  var mon = new Date(parts[0], parts[1] - 1, parts[2])
  var sun = new Date(parts[0], parts[1] - 1, parts[2] + 6)
  return (mon.getMonth() + 1) + '月' + mon.getDate() + '日—' + (sun.getMonth() + 1) + '月' + sun.getDate() + '日'
}

function shortLabel(mondayStr) {
  var parts = mondayStr.split('-').map(Number)
  var mon = new Date(parts[0], parts[1] - 1, parts[2])
  var sun = new Date(parts[0], parts[1] - 1, parts[2] + 6)
  return (mon.getMonth() + 1) + '/' + mon.getDate() + '—' + (sun.getMonth() + 1) + '/' + sun.getDate()
}

function formatWeekNum(mondayStr) {
  var parts = mondayStr.split('-').map(Number)
  var mon = new Date(parts[0], parts[1] - 1, parts[2])
  var jan1 = new Date(parts[0], 0, 1)
  var days = Math.floor((mon - jan1) / 86400000)
  var weekNum = Math.ceil((days + jan1.getDay() + 1) / 7)
  return parts[0] + '年第' + weekNum + '周'
}

// 每期周报的真实 mock 数据
function seedData(key) {
  var map = {
    '2026-06-22': { focusTrend: '↓ 3%', postureTrend: '↑ 5%', anomalyCount: 2, discoveryCount: 3, hasNew: true },
    '2026-06-15': { focusTrend: '↓ 1%', postureTrend: '↑ 2%', anomalyCount: 1, discoveryCount: 2, hasNew: true },
    '2026-06-08': { focusTrend: '↑ 2%', postureTrend: '↓ 1%', anomalyCount: 0, discoveryCount: 2, hasNew: false },
    '2026-06-01': { focusTrend: '→ 持平', postureTrend: '↑ 3%', anomalyCount: 1, discoveryCount: 3, hasNew: false },
    '2026-05-25': { focusTrend: '↓ 2%', postureTrend: '→ 持平', anomalyCount: 0, discoveryCount: 1, hasNew: false },
    '2026-05-18': { focusTrend: '↑ 4%', postureTrend: '↑ 1%', anomalyCount: 1, discoveryCount: 2, hasNew: false },
    '2026-05-11': { focusTrend: '→ 持平', postureTrend: '↓ 2%', anomalyCount: 0, discoveryCount: 1, hasNew: false },
    '2026-05-04': { focusTrend: '↓ 1%', postureTrend: '→ 持平', anomalyCount: 0, discoveryCount: 1, hasNew: false }
  }
  return map[key] || { focusTrend: '→ 持平', postureTrend: '→ 持平', anomalyCount: 0, discoveryCount: 1, hasNew: false }
}

function buildHistory(key, weeks) {
  // 选出比当前周更早的周
  var currentIdx = -1
  for (var i = 0; i < weeks.length; i++) {
    if (weeks[i].key === key) { currentIdx = i; break }
  }
  var older = weeks.slice(currentIdx + 1)
  var list = []
  for (var j = 0; j < older.length && j < 4; j++) {
    var w = older[j]
    var d = seedData(w.key)
    list.push({
      id: w.key,
      key: w.key,
      type: 'mining',
      title: w.weekNum + ' · 行为挖掘报告',
      subtitle: '专注' + d.focusTrend + ' · 坐姿' + d.postureTrend,
      tags: d.anomalyCount > 0 ? [{ text: d.anomalyCount + '个异常', cls: 'warn' }] : [{ text: '无异常', cls: 'good' }],
      faded: j >= 3
    })
  }
  return list
}

function buildWeeks() {
  var today = new Date()
  var weeks = []
  for (var i = 0; i < 8; i++) {
    var d = new Date(today)
    d.setDate(d.getDate() - i * 7)
    var key = getMonday(d)
    var sd = seedData(key)
    weeks.push({
      key: key,
      label: formatWeekLabel(key),
      shortLabel: shortLabel(key),
      weekNum: formatWeekNum(key),
      hasNew: sd.hasNew
    })
  }
  return { weeks: weeks, currentKey: weeks[0].key }
}

Page({
  data: {
    weeks: [],
    currentWeekKey: '',
    activeWeekId: '',
    weekData: {},
    newCount: 3
  },

  onLoad: function () {
    var result = buildWeeks()
    var wk = result.currentKey
    this.setData({
      weeks: result.weeks,
      currentWeekKey: wk,
      activeWeekId: 'ws-' + wk,
      weekData: this.makeWeekData(wk, result.weeks)
    })
  },

  onShow: function () {
    var app = getApp()
    if (app.globalData.childInfo) {
      this.setData({ childName: app.globalData.childInfo.name })
    }
  },

  makeWeekData: function (key, weeks) {
    var wks = weeks || this.data.weeks
    var week = wks.find(function (w) { return w.key === key })
    if (!week) week = {}
    var d = seedData(key)
    return {
      weekNum: week.weekNum || '',
      label: week.label || '',
      shortLabel: week.shortLabel || '',
      focusTrend: d.focusTrend,
      postureTrend: d.postureTrend,
      anomalyCount: d.anomalyCount,
      discoveryCount: d.discoveryCount,
      history: buildHistory(key, wks)
    }
  },

  onWeekTap: function (e) {
    var key = e.currentTarget.dataset.key
    if (key === this.data.currentWeekKey) return
    this.setData({
      currentWeekKey: key,
      activeWeekId: 'ws-' + key,
      weekData: this.makeWeekData(key)
    })
  },

  goReportDetail: function (e) {
    var key = e.currentTarget.dataset.key || this.data.currentWeekKey
    wx.navigateTo({ url: '/pages/report-detail/report-detail?week=' + key })
  },

  goBehavior: function () {
    wx.navigateTo({ url: '/pages/behavior/behavior' })
  }
})
