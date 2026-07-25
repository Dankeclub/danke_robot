Page({
  data: {},

  onScan() {
    wx.scanCode({
      success(res) {
        wx.showToast({ title: '绑定成功', icon: 'success' })
        setTimeout(() => {
          wx.navigateTo({ url: '/pages/child-info/child-info?mode=create' })
        }, 1500)
      },
      fail() {
        wx.showToast({ title: '扫码取消', icon: 'none' })
      }
    })
  },

  onManual() {
    wx.showModal({
      title: '输入设备编号',
      editable: true,
      placeholderText: '请输入设备编号',
      success: (res) => {
        if (res.confirm && res.content) {
          wx.showToast({ title: '绑定成功', icon: 'success' })
          setTimeout(() => {
            wx.navigateTo({ url: '/pages/child-info/child-info?mode=create' })
          }, 1500)
        }
      }
    })
  },

  onSkip() {
    wx.switchTab({ url: '/pages/home/home' })
  }
})
