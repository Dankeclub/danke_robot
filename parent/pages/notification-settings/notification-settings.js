function buildHours() {
  const hours = []
  for (let h = 0; h <= 23; h++) hours.push(String(h).padStart(2, '0'))
  return hours
}
function buildMinutes() {
  const minutes = []
  for (let m = 0; m <= 55; m += 5) minutes.push(String(m).padStart(2, '0'))
  return minutes
}

Page({
  data: {
    behaviorAlert: true,
    dailySummary: true,
    deviceStatus: true,
    weeklyReport: true,
    realtimeAlert: true,
    goalAchieved: false,
    enabledCount: 5,
    dndStart: '22:00',
    dndEnd: '08:00',
    hours: buildHours(),
    minutes: buildMinutes(),
    showTimePicker: false,
    timePickerLabel: '',
    timePickerValue: [0, 0],
    timePickerField: ''
  },

  onShow() {
    this.updateCount()
  },

  onSwitchBehavior(e)  { this.setData({ behaviorAlert: e.detail.value }); this.updateCount() },
  onSwitchDaily(e)     { this.setData({ dailySummary: e.detail.value }); this.updateCount() },
  onSwitchDevice(e)    { this.setData({ deviceStatus: e.detail.value }); this.updateCount() },
  onSwitchWeekly(e)    { this.setData({ weeklyReport: e.detail.value }); this.updateCount() },
  onSwitchRealtime(e)  { this.setData({ realtimeAlert: e.detail.value }); this.updateCount() },
  onSwitchGoal(e)      { this.setData({ goalAchieved: e.detail.value }); this.updateCount() },

  updateCount() {
    const keys = ['behaviorAlert','dailySummary','deviceStatus','weeklyReport','realtimeAlert','goalAchieved']
    this.setData({ enabledCount: keys.filter(k => this.data[k]).length })
  },

  onSubscribe() {
    wx.requestSubscribeMessage({
      tmplIds: [], // TODO: 填入实际模板ID
      success() {
        wx.showToast({ title: '订阅成功', icon: 'success' })
      }
    })
  },

  onTapTimeChip(e) {
    const field = e.currentTarget.dataset.field
    const time = this.data[field]
    const [h, m] = time.split(':').map(Number)
    const hi = this.data.hours.indexOf(String(h).padStart(2, '0'))
    const mi = this.data.minutes.indexOf(String(m).padStart(2, '0'))
    this.setData({
      showTimePicker: true,
      timePickerField: field,
      timePickerLabel: field === 'dndStart' ? '选择开始时间' : '选择结束时间',
      timePickerValue: [hi >= 0 ? hi : 22, mi >= 0 ? mi : 0]
    })
  },

  onCloseTimePicker() {
    this.setData({ showTimePicker: false })
  },

  onTimePickerChange(e) {
    this.setData({ timePickerValue: e.detail.value })
  },

  onConfirmTimePicker() {
    const [hi, mi] = this.data.timePickerValue
    const time = this.data.hours[hi] + ':' + this.data.minutes[mi]
    this.setData({
      [this.data.timePickerField]: time,
      showTimePicker: false
    })
  }
})
