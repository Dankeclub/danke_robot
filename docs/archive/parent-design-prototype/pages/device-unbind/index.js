Page({
  data: {
    bound: false,
    features: [
      { id: 1, text: '实时查看学习状态' },
      { id: 2, text: '远程陪伴孩子' },
      { id: 3, text: '查看成长报告' },
      { id: 4, text: '接收学习通知' }
    ],
    successFeatures: [
      { id: 1, text: '设备在线 · 电量 86%' },
      { id: 2, text: '可实时查看学习状态和远程看护' },
      { id: 3, text: '每日自动生成学习报告' },
      { id: 4, text: '重要消息将通过微信通知' }
    ],
    tips: ['设备已开机', 'Wi-Fi 已连接', '手机与设备处于同一网络'],
    nextSteps: ['前往首页查看孩子学习状态', '设置每日学习目标和计划', '在设备管理中管理机器人']
  },

  onPrimaryTap() {
    if (this.data.bound) {
      wx.switchTab({ url: '/pages/index/index' })
    } else {
      wx.navigateTo({ url: '/pages/device-bindstep/index' })
    }
  },

  onTutorial() {
    wx.showToast({ title: '查看绑定教程', icon: 'none' })
  },

  onLoad(options) {
    if (options && options.bound === '1') {
      this.setData({ bound: true })
    }
  }
})
