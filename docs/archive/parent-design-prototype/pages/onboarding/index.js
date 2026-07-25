Page({
  data: {
    statusBarHeight: 44,
    features: [
      { icon: 'bot', title: 'AI智能陪伴', desc: '蛋仔机器人随时陪伴孩子学习与玩耍' },
      { icon: 'video', title: '实时远程看护', desc: '随时随地查看孩子的学习状态和安全' },
      { icon: 'qi-chart', title: '成长数据报告', desc: '每周自动生成学习报告，见证成长' }
    ]
  },
  onLoad() {
    const sysInfo = wx.getWindowInfo()
    this.setData({ statusBarHeight: sysInfo.statusBarHeight || 44 })
  },
  onTapStart() {
    wx.redirectTo({ url: '/pages/bind-child/index' })
  }
})
