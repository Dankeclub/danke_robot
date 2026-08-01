App({
  onLaunch() {
    const sys = wx.getSystemInfoSync()
    this.globalData.safeBottom = sys.safeArea ? (sys.screenHeight - sys.safeArea.bottom) : 0

    // 从本地存储恢复孩子信息
    const saved = wx.getStorageSync('childInfo')
    if (saved) {
      this.globalData.childInfo = saved
    }

    // 从本地存储恢复设备信息
    const savedDevice = wx.getStorageSync('deviceInfo')
    if (savedDevice) {
      this.globalData.deviceInfo = savedDevice
    }

    // 从本地存储恢复派发任务
    const savedTasks = wx.getStorageSync('dispatchedTasks')
    if (savedTasks) {
      this.globalData.dispatchedTasks = savedTasks
    } else {
      this.globalData.dispatchedTasks = []
    }

    // 加载字体（国内可能失败，回退到 PingFang SC）
    wx.loadFontFace({
      family: 'Nunito',
      source: 'url("https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap")',
      success: () => console.log('Nunito loaded'),
      fail: () => console.log('Nunito fallback to system')
    })
    wx.loadFontFace({
      family: 'Inter',
      source: 'url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap")',
      success: () => console.log('Inter loaded'),
      fail: () => console.log('Inter fallback to system')
    })
  },
  globalData: {
    safeBottom: 0,
    dankeState: 'online',
    childInfo: {
      name: '小宇',
      birthYear: 2019,
      birthMonth: 6,
      gender: 'boy'
    }
  }
})
