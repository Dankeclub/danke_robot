Page({
  data: {
    hasDevice: true,
    device: {
      name: '蛋仔机器人',
      online: true,
      battery: 80,
      version: 'v2.4.1',
      serial: 'SN2024'
    }
  },

  onShow() {
    const app = getApp()
    if (app.globalData.deviceInfo) {
      this.setData({ device: app.globalData.deviceInfo, hasDevice: true })
    }
  },

  goBind() {
    wx.navigateTo({ url: '/pages/bind/bind' })
  },

  onEditName() {
    wx.showModal({
      title: '修改设备名称',
      editable: true,
      placeholderText: '请输入设备名称',
      content: this.data.device.name,
      success: (res) => {
        if (res.confirm && res.content && res.content.trim()) {
          const name = res.content.trim()
          const device = { ...this.data.device, name }
          this.setData({ device })
          const app = getApp()
          app.globalData.deviceInfo = device
          wx.setStorageSync('deviceInfo', device)
          wx.showToast({ title: '已更新', icon: 'success' })
        }
      }
    })
  },

  onUnbind() {
    wx.showModal({
      title: '解绑设备',
      content: '确定要解绑蛋仔机器人吗？将清除所有设备数据。',
      confirmColor: '#C77974',
      success: (res) => {
        if (res.confirm) {
          this.setData({ hasDevice: false })
          const app = getApp()
          app.globalData.deviceInfo = null
          wx.removeStorageSync('deviceInfo')
          wx.showToast({ title: '已解绑', icon: 'success' })
        }
      }
    })
  }
})
