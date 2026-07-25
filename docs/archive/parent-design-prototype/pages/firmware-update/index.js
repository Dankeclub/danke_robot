Page({
  data: {
    currentVersion: 'v1.2.0',
    isLatest: true,
    changelog: [
      {
        version: 'v1.2.0',
        items: [
          '优化语音识别准确率，提升对话流畅度',
          '新增睡前故事模式，支持定时播放',
          '修复部分场景下蓝牙连接不稳定的问题'
        ]
      },
      {
        version: 'v1.1.0',
        items: [
          '新增学习进度追踪功能',
          '优化电量管理，延长续航时间',
          '修复若干已知问题，提升系统稳定性'
        ]
      }
    ]
  },

  onCheckUpdate() {
    wx.showLoading({ title: '检查中...' })
    setTimeout(() => {
      wx.hideLoading()
      wx.showToast({ title: '已是最新版本', icon: 'success' })
    }, 1500)
  },

  onLoad() {}
})
