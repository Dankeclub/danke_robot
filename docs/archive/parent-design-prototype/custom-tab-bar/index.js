Component({
  data: {
    active: 0,
    list: [
      { pagePath: '/pages/index/index', text: '首页', icon: '/assets/icons/home.svg', activeIcon: '/assets/icons/home-active.svg' },
      { pagePath: '/pages/monitor/index', text: '看护', icon: '/assets/icons/video.svg', activeIcon: '/assets/icons/video-active.svg' },
      { pagePath: '/pages/report/index', text: '报告', icon: '/assets/icons/chart.svg', activeIcon: '/assets/icons/chart-active.svg' },
      { pagePath: '/pages/mine/index', text: '我的', icon: '/assets/icons/user.svg', activeIcon: '/assets/icons/user-active.svg' }
    ]
  },
  methods: {
    switchTab(e) {
      const { index, path } = e.currentTarget.dataset
      this.setData({ active: index })
      wx.switchTab({ url: path })
    }
  }
})
