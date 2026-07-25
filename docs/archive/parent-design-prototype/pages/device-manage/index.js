const store = require('../../store/index')

Page({
  onLoad() {
    if (!store.getState('deviceInfo')) {
      wx.redirectTo({ url: '/pages/device-unbind/index' })
    }
  },

  onViewDetail() {
    wx.navigateTo({ url: '/pages/device-info/index' })
  },

  onOpTap(e) {
    const key = e.currentTarget.dataset.key
    if (key === 'firmware') {
      wx.navigateTo({ url: '/pages/firmware-update/index' })
    } else if (key === 'reconnect') {
      wx.showLoading({ title: '重新连接中...' })
      setTimeout(() => {
        wx.hideLoading()
        wx.showToast({ title: '已重新连接', icon: 'success' })
      }, 1500)
    } else if (key === 'info') {
      wx.navigateTo({ url: '/pages/device-info/index' })
    } else if (key === 'connect') {
      wx.navigateTo({ url: '/pages/connect-log/index' })
    }
  },

  onUnbind() {
    wx.showModal({
      title: '确认解绑',
      content: '解绑后设备将断开连接，确定要解绑吗？',
      success: (res) => {
        if (res.confirm) {
          store.setState('deviceInfo', null)
          wx.redirectTo({ url: '/pages/device-unbind/index' })
        }
      }
    })
  }
})
