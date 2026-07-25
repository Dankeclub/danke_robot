Page({
  data: {
    dankeState: 'online',
    states: ['online', 'focused', 'tired', 'offline'],
    childName: '小宇',
    statusText: '在线 · 正在解答数学题',
    todayItems: [
      { text: '数学心算', sub: '已完成 · 连续答对 12 题', done: true },
      { text: '英语单词', sub: '已完成 · 正确率 87%', done: true },
      { text: '科学小实验', sub: '进行中 · 预计 15 分钟', done: false }
    ],
    timelineItems: [
      { time: '10:42', text: '专注时段 · 连续 25 分钟', tag: '优秀', tagColor: 'mint', color: 'mint' },
      { time: '10:20', text: '坐姿不良提醒', tag: '已纠正', tagColor: 'amber', color: 'amber' },
      { time: '09:55', text: '回到学习区域', tag: '', tagColor: '', color: 'sky' }
    ],
    miniProgress: [
      { label: '数学', percent: 90, color: 'a', barColor: 'var(--pd)' },
      { label: '科学', percent: 65, color: 'b', barColor: 'var(--pg)' },
      { label: '诗歌', percent: 55, color: 'c', barColor: 'var(--pp)' },
      { label: '英语', percent: 70, color: 'd', barColor: 'var(--pa1)' }
    ]
  },

  stateConfig: {
    online:  { statusText: '在线 · 正在解答数学题' },
    focused: { statusText: '专注 · 答题中' },
    tired:   { statusText: '今日已用 86 分钟，休息一下吧' },
    offline: { statusText: '设备已离线' }
  },

  onSwitchState(e) {
    const state = e.currentTarget.dataset.state
    const cfg = this.stateConfig[state]
    this.setData({
      dankeState: state,
      statusText: cfg.statusText
    })
  },

  goUsage()    { wx.navigateTo({ url: '/pages/usage/usage' }) },
  goBehavior() { wx.navigateTo({ url: '/pages/behavior/behavior' }) },
  goLearning() { wx.switchTab({ url: '/pages/learning/learning' }) },
  goReport()   { wx.switchTab({ url: '/pages/report/report' }) },
  goDevice()   { wx.navigateTo({ url: '/pages/device/device' }) },

  openTask() {
    wx.showToast({ title: '派任务面板待实现', icon: 'none' })
  },

  goNotifs() {
    wx.navigateTo({ url: '/pages/notifications/notifications' })
  },

  onShow() {
    const app = getApp()
    if (app.globalData.childInfo) {
      this.setData({ childName: app.globalData.childInfo.name })
    }
  }
})
