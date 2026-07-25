Page({
  data: {
    appNotif: {
      behavior: true,
      studySummary: true,
      goalComplete: true
    },
    wxNotif: {
      weeklyReport: true,
      deviceOffline: true,
      lowBattery: true
    },
    dnd: {
      enabled: false
    }
  },

  onDndChange(e) {
    this.setData({ 'dnd.enabled': e.detail.value })
  }
})
