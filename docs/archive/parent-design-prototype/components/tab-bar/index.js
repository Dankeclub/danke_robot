Component({
  properties: {
    active: { type: Number, value: 0 }
  },
  methods: {
    switchTab(e) {
      const { path, index } = e.currentTarget.dataset
      if (Number(index) === this.data.active) return
      wx.switchTab({ url: path })
    }
  }
})
