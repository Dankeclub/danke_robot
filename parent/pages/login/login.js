Page({
  data: {
    checked: true
  },

  toggleCheck() {
    this.setData({ checked: !this.data.checked })
  },

  onWechatLogin() {
    if (!this.data.checked) {
      wx.showToast({ title: '请先同意用户协议', icon: 'none' })
      return
    }
    // TODO: 微信登录逻辑
    wx.showToast({ title: '登录成功', icon: 'success' })

    const app = getApp()
    const hasDevice = app.globalData.deviceInfo && app.globalData.deviceInfo.deviceId
    const hasChild = app.globalData.childInfo

    if (!hasDevice) {
      wx.navigateTo({ url: '/pages/bind/bind' })
    } else if (!hasChild) {
      wx.navigateTo({ url: '/pages/child-info/child-info?mode=create' })
    } else {
      wx.switchTab({ url: '/pages/home/home' })
    }
  }
})
