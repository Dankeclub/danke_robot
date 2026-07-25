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

  goBind() {
    wx.navigateTo({ url: '/pages/bind/bind' })
  },

  onUnbind() {
    wx.showModal({
      title: '解绑设备',
      content: '确定要解绑蛋仔机器人吗？将清除所有设备数据。',
      confirmColor: '#C77974',
      success: (res) => {
        if (res.confirm) {
          this.setData({ hasDevice: false })
          wx.showToast({ title: '已解绑', icon: 'success' })
        }
      }
    })
  }
})
