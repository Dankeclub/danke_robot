Page({
  data: {
    activePeriod: 'today',
    weekBars: [
      { day: '一', height: 120, color: '#84A6FD' },
      { day: '二', height: 160, color: '#84A6FD' },
      { day: '三', height: 100, color: '#84A6FD' },
      { day: '四', height: 190, color: '#84A6FD' },
      { day: '五', height: 140, color: '#84A6FD' },
      { day: '六', height: 210, color: '#84A6FD' },
      { day: '日', height: 90, color: '#316AFD', active: true }
    ],
    usageDetails: [
      { id: 1, name: '数学思维训练', time: '09:30 - 10:15', duration: '45min', color: '#316AFD' },
      { id: 2, name: '英语绘本阅读', time: '10:30 - 11:00', duration: '30min', color: '#4075FF' },
      { id: 3, name: '科学小问答', time: '14:00 - 14:20', duration: '20min', color: '#84A6FD' },
      { id: 4, name: '自由对话', time: '15:30 - 15:50', duration: '20min', color: '#84A6FD' }
    ]
  },

  onPeriodChange(e) {
    this.setData({ activePeriod: e.currentTarget.dataset.period })
  }
})
