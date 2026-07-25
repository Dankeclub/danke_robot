Page({
  data: {},

  onWechatLogin() {
    wx.showLoading({ title: '登录中...' })
    setTimeout(() => {
      wx.hideLoading()
      wx.redirectTo({ url: '/pages/onboarding/index' })
    }, 1500)
  }
})
