Component({
  properties: {
    title: { type: String, value: '' },
    showBack: { type: Boolean, value: true },
    rightIcon: { type: String, value: '' },
    transparent: { type: Boolean, value: false }
  },
  data: {
    statusBarHeight: 44
  },
  lifetimes: {
    attached() {
      const sysInfo = wx.getWindowInfo()
      this.setData({ statusBarHeight: sysInfo.statusBarHeight || 44 })
    }
  },
  methods: {
    goBack() {
      wx.navigateBack({ delta: 1 })
    },
    onRightTap() {
      this.triggerEvent('righttap')
    }
  }
})
