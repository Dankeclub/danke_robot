Page({
  data: {
    childName: '小宇',
    ageText: '6 岁'
  },

  onShow() {
    const app = getApp()
    if (app.globalData.childInfo) {
      const info = app.globalData.childInfo
      const age = new Date().getFullYear() - info.birthYear
      this.setData({
        childName: info.name,
        ageText: age + ' 岁'
      })
    }
  },

  goDevice() {
    wx.navigateTo({ url: '/pages/device/device' })
  },

  goNotifSettings() {
    wx.navigateTo({ url: '/pages/notification-settings/notification-settings' })
  },

  goChildInfo() {
    wx.navigateTo({ url: '/pages/child-info/child-info?mode=edit' })
  },

  onLogout() {
    wx.showModal({
      title: '退出登录',
      content: '确定要退出当前账号吗？',
      confirmColor: '#C77974',
      success(res) {
        if (res.confirm) {
          wx.reLaunch({ url: '/pages/login/login' })
        }
      }
    })
  }
})
