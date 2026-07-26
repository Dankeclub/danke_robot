const app = getApp()
Component({
  data: { s: 0, sb: 0 },
  lifetimes: {
    attached() {
      this._sync()
    }
  },
  pageLifetimes: { show() { this._sync() } },
  methods: {
    _sync() {
      this.setData({ sb: app.globalData.safeBottom })
      const p = getCurrentPages()
      const m = { 'pages/home/home': 0, 'pages/monitor/monitor': 1, 'pages/profile/profile': 2 }
      this.setData({ s: m[(p.slice(-1)[0] || {}).route] ?? 0 })
    },
    go(e) {
      wx.switchTab({ url: ['/pages/home/home', '/pages/monitor/monitor', '/pages/profile/profile'][Number(e.currentTarget.dataset.i)] })
    }
  }
})
