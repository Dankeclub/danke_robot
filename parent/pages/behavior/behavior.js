// 行为分析页 — 专注度 / 姿态 / 位置
Page({
  data: {
    activeTab: 'focus',
    tabs: [
      { key: 'focus',    label: '专注度' },
      { key: 'posture',  label: '姿态' },
      { key: 'location', label: '位置' }
    ]
  },

  onSwitchTab: function (e) {
    var tab = e.currentTarget.dataset.tab
    this.setData({ activeTab: tab })

    // 重触发动画
    var that = this
    setTimeout(function () {
      that.setData({ _animKey: Date.now() })
    }, 16)
  },

  goBack: function () {
    wx.navigateBack()
  }
})
