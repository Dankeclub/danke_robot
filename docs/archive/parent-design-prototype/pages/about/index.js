Page({
  data: {
    infoItems: [
      { key: 'agreement', icon: 'info-blue', label: '用户协议' },
      { key: 'privacy', icon: 'info', label: '隐私政策' },
      { key: 'license', icon: 'qi-brain', label: '开源许可' }
    ]
  },

  onRowTap(e) {
    const key = e.currentTarget.dataset.key
    wx.showToast({ title: key, icon: 'none' })
  }
})
