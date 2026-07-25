const store = require('./store/index')

App({
  globalData: {
    store: store
  },

  onLaunch() {
    this.initStore()
  },

  initStore() {
    const userInfo = wx.getStorageSync('userInfo')
    const childInfo = wx.getStorageSync('childInfo')
    const deviceInfo = wx.getStorageSync('deviceInfo')

    if (userInfo) store.setState('userInfo', userInfo)
    if (childInfo) store.setState('childInfo', childInfo)
    if (deviceInfo) store.setState('deviceInfo', deviceInfo)

    store.setState('deviceOnline', true)
  }
})
