const store = require('../../store/index')

Page({
  onPair() {
    wx.showLoading({ title: '配网中...' })
    setTimeout(() => {
      wx.hideLoading()
      store.setState('deviceInfo', {
        name: 'DZ-001 Pro',
        battery: '85%',
        network: '良好',
        storage: '2.1G',
        online: true
      })
      wx.redirectTo({ url: '/pages/device-manage/index' })
    }, 2000)
  },

  onHelp() {
    wx.showToast({ title: '查看配网教程', icon: 'none' })
  }
})
