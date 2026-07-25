// 行为挖掘报告详情

// Canvas 折线图绘制
function drawLineChart(canvas, width, height, labels, data, yMin, yMax, threshold) {
  var dpr = wx.getSystemInfoSync().pixelRatio
  canvas.width = width * dpr
  canvas.height = height * dpr
  var ctx = canvas.getContext('2d')
  ctx.scale(dpr, dpr)

  var pad = { top: 16, right: 16, bottom: 32, left: 36 }
  var pw = width - pad.left - pad.right
  var ph = height - pad.top - pad.bottom

  function y(v) { return pad.top + ph * (1 - (v - yMin) / (yMax - yMin)) }
  function x(i) { return pad.left + pw * i / (labels.length - 1) }

  // 软网格
  ctx.strokeStyle = 'rgba(0,0,0,0.05)'
  ctx.lineWidth = 1
  for (var yi = yMin; yi <= yMax; yi += 10) {
    ctx.beginPath()
    ctx.moveTo(pad.left, y(yi))
    ctx.lineTo(width - pad.right, y(yi))
    ctx.stroke()
  }

  // Y 轴标签
  ctx.fillStyle = '#B8AEA8'
  ctx.font = '11px sans-serif'
  ctx.textAlign = 'right'
  ;[50, 60, 70, 80, 90, 100].filter(function (v) { return v >= yMin && v <= yMax }).forEach(function (v) {
    ctx.fillText(String(v), pad.left - 6, y(v) + 4)
  })

  // X 轴标签
  ctx.textAlign = 'center'
  labels.forEach(function (l, i) { ctx.fillText(l, x(i), height - 8) })

  // 预警虚线
  if (threshold !== undefined) {
    ctx.strokeStyle = '#F0A855'
    ctx.lineWidth = 1.5
    ctx.setLineDash([6, 4])
    ctx.beginPath()
    ctx.moveTo(pad.left, y(threshold))
    ctx.lineTo(width - pad.right, y(threshold))
    ctx.stroke()
    ctx.setLineDash([])
  }

  // 填充渐变
  var grad = ctx.createLinearGradient(0, pad.top, 0, height - pad.bottom)
  grad.addColorStop(0, 'rgba(119,140,205,0.18)')
  grad.addColorStop(1, 'rgba(119,140,205,0)')

  // 贝塞尔曲线路径
  ctx.beginPath()
  ctx.moveTo(x(0), y(data[0]))
  for (var i = 1; i < data.length; i++) {
    var cx1 = x(i - 1) + (x(i) - x(i - 1)) * 0.5
    var cx2 = x(i) - (x(i) - x(i - 1)) * 0.5
    ctx.bezierCurveTo(cx1, y(data[i - 1]), cx2, y(data[i]), x(i), y(data[i]))
  }

  // 填充
  ctx.lineTo(x(data.length - 1), height - pad.bottom)
  ctx.lineTo(x(0), height - pad.bottom)
  ctx.closePath()
  ctx.fillStyle = grad
  ctx.fill()

  // 绘制曲线
  ctx.beginPath()
  ctx.moveTo(x(0), y(data[0]))
  for (var j = 1; j < data.length; j++) {
    var c1 = x(j - 1) + (x(j) - x(j - 1)) * 0.5
    var c2 = x(j) - (x(j) - x(j - 1)) * 0.5
    ctx.bezierCurveTo(c1, y(data[j - 1]), c2, y(data[j]), x(j), y(data[j]))
  }
  ctx.strokeStyle = '#778ccd'
  ctx.lineWidth = 2.8
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.stroke()

  // 数据点
  data.forEach(function (v, i) {
    ctx.beginPath()
    ctx.arc(x(i), y(v), i === 2 ? 6 : 4, 0, Math.PI * 2)
    ctx.fillStyle = i === 2 ? '#D97A84' : '#778ccd'
    ctx.fill()
    ctx.strokeStyle = '#fff'
    ctx.lineWidth = 2
    ctx.stroke()
  })
}

// Canvas 柱状图绘制
function drawBarChart(canvas, width, height, labels, data, yMin, yMax, threshold, colors) {
  var dpr = wx.getSystemInfoSync().pixelRatio
  canvas.width = width * dpr
  canvas.height = height * dpr
  var ctx = canvas.getContext('2d')
  ctx.scale(dpr, dpr)

  var pad = { top: 28, right: 16, bottom: 32, left: 36 }
  var pw = width - pad.left - pad.right
  var ph = height - pad.top - pad.bottom

  function y(v) { return pad.top + ph * (1 - (v - yMin) / (yMax - yMin)) }

  // 软网格
  ctx.strokeStyle = 'rgba(0,0,0,0.05)'
  ctx.lineWidth = 1
  for (var yi = yMin; yi <= yMax; yi += 10) {
    ctx.beginPath()
    ctx.moveTo(pad.left, y(yi))
    ctx.lineTo(width - pad.right, y(yi))
    ctx.stroke()
  }

  // Y 轴标签
  ctx.fillStyle = '#B8AEA8'
  ctx.font = '11px sans-serif'
  ctx.textAlign = 'right'
  ;[60, 70, 80, 90, 100].filter(function (v) { return v >= yMin && v <= yMax }).forEach(function (v) {
    ctx.fillText(String(v), pad.left - 6, y(v) + 4)
  })

  // X 轴标签
  ctx.textAlign = 'center'
  labels.forEach(function (l, i) {
    ctx.fillText(l, pad.left + pw * (i + 0.5) / data.length, height - 8)
  })

  // 预警虚线
  if (threshold !== undefined) {
    ctx.strokeStyle = '#F0A855'
    ctx.lineWidth = 1.5
    ctx.setLineDash([6, 4])
    ctx.beginPath()
    ctx.moveTo(pad.left, y(threshold))
    ctx.lineTo(width - pad.right, y(threshold))
    ctx.stroke()
    ctx.setLineDash([])
  }

  // 柱状图
  var barW = pw / data.length * 0.55
  var r = 6
  data.forEach(function (v, i) {
    var bX = pad.left + pw * (i + 0.5) / data.length - barW / 2
    var bY = y(v)
    var bH = y(yMin) - bY

    ctx.beginPath()
    ctx.moveTo(bX + r, bY)
    ctx.lineTo(bX + barW - r, bY)
    ctx.arcTo(bX + barW, bY, bX + barW, bY + r, r)
    ctx.lineTo(bX + barW, bY + bH)
    ctx.lineTo(bX, bY + bH)
    ctx.lineTo(bX, bY + r)
    ctx.arcTo(bX, bY, bX + r, bY, r)
    ctx.closePath()
    ctx.fillStyle = colors[i]
    ctx.fill()

    // 数值标签
    ctx.fillStyle = colors[i]
    ctx.font = 'bold 12px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(v + '%', bX + barW / 2, bY - 8)
  })
}

// 多周 mock 数据
function dataForWeek(key) {
  var map = {
    '2026-06-22': {
      reportDate: '2026年第26周 · 6月22日—6月28日',
      metrics: { focus: 89, posture: 82, dailyUsage: 78, focusChange: -3, focusChangeText: '3%', postureChange: 5, postureChangeText: '5%' },
      focusData: [92, 90, 78, 85, 88, 91, 89],
      postureData: [75, 74, 77, 82],
      postureColors: ['#97979C', '#B8AEA8', '#a0c8a8', '#4F9A5F'],
      anomalies: [
        { title: '周三下午专注度骤降', desc: '15:30-16:20 跌至 62 分，与"思维游戏"上线时间吻合。中断次数为平时 3.2 倍。', icon: 'ic-clock-pd', iconBg: 'focus', tags: [{ text: '专注度', cls: 'tf' }, { text: '使用时长', cls: 'tt' }] },
        { title: '周四下午连续坐姿异常 40 分钟', desc: '当日使用时长达 95 分钟（本周最高），长时间使用后坐姿问题概率 ×2.5。', icon: 'ic-heart-rose', iconBg: 'posture', tags: [{ text: '姿态', cls: 'tp' }] }
      ]
    },
    '2026-06-15': {
      reportDate: '2026年第25周 · 6月15日—6月21日',
      metrics: { focus: 90, posture: 78, dailyUsage: 82, focusChange: -1, focusChangeText: '1%', postureChange: 2, postureChangeText: '2%' },
      focusData: [91, 88, 90, 86, 93, 94, 90],
      postureData: [76, 73, 77, 78],
      postureColors: ['#97979C', '#B8AEA8', '#a0c8a8', '#6DAF7D'],
      anomalies: [
        { title: '周四专注度小幅下滑', desc: '午后 14:00-15:00 降至 86 分，与课外活动切换时间重合。', icon: 'ic-clock-pd', iconBg: 'focus', tags: [{ text: '专注度', cls: 'tf' }] }
      ]
    },
    '2026-06-08': {
      reportDate: '2026年第24周 · 6月8日—6月14日',
      metrics: { focus: 91, posture: 77, dailyUsage: 75, focusChange: 2, focusChangeText: '2%', postureChange: -1, postureChangeText: '1%' },
      focusData: [90, 92, 91, 89, 93, 92, 91],
      postureData: [78, 76, 75, 77],
      postureColors: ['#97979C', '#B8AEA8', '#B8AEA8', '#6DAF7D'],
      anomalies: []
    },
    '2026-06-01': {
      reportDate: '2026年第23周 · 6月1日—6月7日',
      metrics: { focus: 89, posture: 79, dailyUsage: 80, focusChange: 0, focusChangeText: '持平', postureChange: 3, postureChangeText: '3%' },
      focusData: [88, 90, 87, 91, 89, 88, 89],
      postureData: [74, 73, 76, 79],
      postureColors: ['#97979C', '#B8AEA8', '#a0c8a8', '#4F9A5F'],
      anomalies: [
        { title: '周一早晨轻度走神', desc: '8:30-9:00 专注度降至 88 分，较同期平均值低 3 分。', icon: 'ic-clock-pd', iconBg: 'focus', tags: [{ text: '专注度', cls: 'tf' }] }
      ]
    },
    '2026-05-25': {
      reportDate: '2026年第22周 · 5月25日—5月31日',
      metrics: { focus: 91, posture: 76, dailyUsage: 72, focusChange: -2, focusChangeText: '2%', postureChange: 0, postureChangeText: '持平' },
      focusData: [93, 92, 88, 91, 90, 93, 91],
      postureData: [77, 76, 75, 76],
      postureColors: ['#B8AEA8', '#97979C', '#B8AEA8', '#6DAF7D'],
      anomalies: []
    },
    '2026-05-18': {
      reportDate: '2026年第21周 · 5月18日—5月24日',
      metrics: { focus: 93, posture: 76, dailyUsage: 70, focusChange: 4, focusChangeText: '4%', postureChange: 1, postureChangeText: '1%' },
      focusData: [90, 93, 92, 95, 94, 91, 93],
      postureData: [74, 75, 76, 76],
      postureColors: ['#97979C', '#B8AEA8', '#a0c8a8', '#6DAF7D'],
      anomalies: [
        { title: '周中专注达到学期最高', desc: '周四单日专注度 95 分，本周思维游戏内容适龄匹配度高。', icon: 'ic-star-pd', iconBg: 'focus', tags: [{ text: '专注度', cls: 'tf' }] }
      ]
    }
  }
  return map[key] || map['2026-06-22']
}

Page({
  data: {
    reportDate: '',
    metrics: {},
    anomalies: [],
    focusData: [],
    postureData: [],
    postureColors: [],
    discoveries: [],
    aiSummary: '',
    currentWeek: ''
  },

  onLoad: function (opts) {
    var key = opts.week || '2026-06-22'
    var d = dataForWeek(key)
    var noAnomaly = d.anomalies.length === 0
    this.setData({
      currentWeek: key,
      reportDate: d.reportDate,
      metrics: d.metrics,
      anomalies: d.anomalies,
      focusData: d.focusData,
      postureData: d.postureData,
      postureColors: d.postureColors,
      discoveries: [
        { title: '使用时长 > 90分钟 → 坐姿问题 +40%', desc: '3 天超过 90 分钟，坐姿问题次数平均多出 40%。建议在 80 分钟时触发休息提醒。', color: '#778ccd' },
        { title: '客厅专注度比书房低 12%', desc: '书房内平均 92 分，客厅降至 80 分。周二、四在客厅学习时专注度均低于警戒线。', color: '#4F9A5F' },
        { title: '早晨专注度比晚上高 35%', desc: '早 8-10 点平均 94 分，晚 7-9 点降至 70 分。高难度学习任务建议安排在上午进行。', color: '#F0A855' }
      ],
      aiSummary: noAnomaly
        ? '这周整体表现稳定，专注度和坐姿均保持良好水平。孩子在学习中保持了较高的投入度，没有出现明显异常。继续保持目前的学习节奏和坐姿习惯。'
        : '这周值得关注：专注度变化 ' + d.metrics.focusChangeText + '，坐姿变化 ' + d.metrics.postureChangeText + '。关键规律已被蛋仔捕捉到——用太久坐姿会变差，客厅学习效率不如书房，早上状态最好。'
    })
  },

  onReady: function () {
    this.drawCharts()
  },

  drawCharts: function () {
    var that = this
    wx.createSelectorQuery().in(this)
      .select('#focusChart').fields({ node: true, size: true })
      .select('#postureChart').fields({ node: true, size: true })
      .exec(function (res) {
        if (res[0]) {
          drawLineChart(
            res[0].node, res[0].width, res[0].height,
            ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
            that.data.focusData,
            50, 100, 70
          )
        }
        if (res[1]) {
          drawBarChart(
            res[1].node, res[1].width, res[1].height,
            ['第23周', '第24周', '第25周', '第26周'],
            that.data.postureData,
            60, 100, 80,
            that.data.postureColors
          )
        }
      })
  },

  goBack: function () {
    wx.navigateBack()
  },

  onShare: function () {
    wx.showToast({ title: '分享功能开发中', icon: 'none' })
  }
})
