Page({
  data: {
    behaviorAlert: true,
    dailySummary: true,
    deviceStatus: true,
    weeklyReport: true,
    realtimeAlert: true,
    goalAchieved: false,
    dndStart: '22:00',
    dndEnd: '08:00'
  },

  onSwitchBehavior(e)  { this.setData({ behaviorAlert: e.detail.value }) },
  onSwitchDaily(e)     { this.setData({ dailySummary: e.detail.value }) },
  onSwitchDevice(e)    { this.setData({ deviceStatus: e.detail.value }) },
  onSwitchWeekly(e)    { this.setData({ weeklyReport: e.detail.value }) },
  onSwitchRealtime(e)  { this.setData({ realtimeAlert: e.detail.value }) },
  onSwitchGoal(e)      { this.setData({ goalAchieved: e.detail.value }) },

  onSubscribe() {
    wx.requestSubscribeMessage({
      tmplIds: [], // TODO: 填入实际模板ID
      success() {
        wx.showToast({ title: '订阅成功', icon: 'success' })
      }
    })
  },

  onPickDndStart() {
    // TODO: 时间选择器
  },

  onPickDndEnd() {
    // TODO: 时间选择器
  }
})
