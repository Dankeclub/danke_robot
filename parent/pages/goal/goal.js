Page({
  data: {
    goalMinutes: 120,
    sliderPercent: 50,
    modules: [
      { key: 'math',  name: '数学', hint: '心算 + 应用题',   minutes: 30 },
      { key: 'sci',   name: '科学', hint: '自然常识 + 实验', minutes: 25 },
      { key: 'eng',   name: '英语', hint: '单词 + 阅读',     minutes: 25 },
      { key: 'poem',  name: '诗歌', hint: '唐诗 + 儿歌',     minutes: 20 },
      { key: 'music', name: '音乐', hint: '节奏 + 乐器认知', minutes: 20 }
    ],
    minGoal: 30,
    maxGoal: 240
  },

  onLoad() {
    this.updateSliderFromGoal()
  },

  updateGoalFromSlider(pct) {
    const { minGoal, maxGoal } = this.data
    const val = Math.round((minGoal + pct * (maxGoal - minGoal)) / 5) * 5
    const clamped = Math.max(minGoal, Math.min(maxGoal, val))
    this.setData({ goalMinutes: clamped })
  },

  updateSliderFromGoal() {
    const { goalMinutes, minGoal, maxGoal } = this.data
    const pct = (goalMinutes - minGoal) / (maxGoal - minGoal) * 100
    this.setData({ sliderPercent: pct })
  },

  onSliderTap(e) {
    const rect = e.currentTarget.getBoundingClientRect()
    // 小程序中需用 touch 事件的 detail
    if (e.detail && e.detail.x) {
      const pct = (e.detail.x - rect.left) / rect.width * 100
      const clamped = Math.max(0, Math.min(100, pct))
      this.setData({ sliderPercent: Math.round(clamped) })
      this.updateGoalFromSlider(clamped / 100)
    }
  },

  onThumbStart(e) {
    this._thumbDragging = true
  },

  onThumbMove(e) {
    if (!this._thumbDragging) return
    const { minGoal, maxGoal } = this.data
    // 用当前触摸位置计算百分比
    const touch = e.touches[0]
    // 简化：用 pageX 近似
    const winWidth = wx.getSystemInfoSync().windowWidth
    const trackStart = 44 // var(--m) in rpx/2 ≈ px
    const trackWidth = winWidth - trackStart * 2
    const px = touch.pageX - trackStart
    const pct = Math.round(Math.max(0, Math.min(1, px / trackWidth)) * 100)
    this.setData({ sliderPercent: pct })
    this.updateGoalFromSlider(pct / 100)
  },

  onThumbEnd() {
    this._thumbDragging = false
  },

  onAdjust(e) {
    const { key, delta } = e.currentTarget.dataset
    const modules = this.data.modules.map(m => {
      if (m.key === key) {
        const v = Math.max(5, Math.min(90, m.minutes + Number(delta)))
        return { ...m, minutes: v }
      }
      return m
    })
    this.setData({ modules })
  },

  onSave() {
    wx.showToast({ title: '已保存', icon: 'success' })
  }
})
