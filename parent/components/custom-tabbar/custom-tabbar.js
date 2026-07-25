const app = getApp()
Component({
  data: { s: 0, sb: 0 },
  lifetimes: {
    attached() {
      this.setData({ sb: app.globalData.safeBottom })
      const p = getCurrentPages()
      const m = { 'pages/home/home':0,'pages/report/report':1,'pages/monitor/monitor':2,'pages/learning/learning':3,'pages/profile/profile':4 }
      this.setData({ s: m[(p.slice(-1)[0]||{}).route]??0 })
    }
  },
  pageLifetimes: { show() { this.lifetimes.attached() } },
  methods: {
    go(e) {
      wx.switchTab({ url: ['/pages/home/home','/pages/report/report','/pages/monitor/monitor','/pages/learning/learning','/pages/profile/profile'][Number(e.currentTarget.dataset.i)] })
    }
  }
})
