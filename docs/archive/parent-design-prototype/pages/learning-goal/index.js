Page({
  data: {
    dailyGoal: 45,
    subjectGoals: [
      { name: '阅读', icon: 'qi-book', minutes: 15, color: '#316AFD' },
      { name: '英语', icon: 'qi-video', minutes: 15, color: '#4075FF' },
      { name: '数学', icon: 'qi-brain', minutes: 15, color: '#316AFD' },
      { name: '兴趣拓展', icon: 'qi-chart', minutes: 10, color: '#84A6FD' }
    ],
    weeklyTotal: 8
  },

  _updateWeekly() {
    const total = Math.round(this.data.dailyGoal * 7 / 60)
    this.setData({ weeklyTotal: total })
  },

  onMinus() {
    if (this.data.dailyGoal > 15) {
      this.setData({ dailyGoal: this.data.dailyGoal - 5 })
      this._updateWeekly()
    }
  },

  onPlus() {
    if (this.data.dailyGoal < 120) {
      this.setData({ dailyGoal: this.data.dailyGoal + 5 })
      this._updateWeekly()
    }
  },

  /* ── Main Slider ── */
  onSliderStart(e) {
    this._isSliding = true
    this._updateMainSlider(e.touches[0])
  },
  onSliderMove(e) {
    if (!this._isSliding) return
    this._updateMainSlider(e.touches[0])
  },
  onSliderEnd() { this._isSliding = false },
  _updateMainSlider(touch) {
    const query = wx.createSelectorQuery().in(this)
    query.select('.progress-wrap').boundingClientRect(rect => {
      if (!rect) return
      const ratio = (touch.clientX - rect.left) / rect.width
      const clamped = Math.max(0, Math.min(1, ratio))
      const minutes = Math.round((15 + clamped * 105) / 5) * 5
      this.setData({ dailyGoal: Math.max(15, Math.min(120, minutes)) })
      this._updateWeekly()
    }).exec()
  },

  /* ── Subject Sliders ── */
  onSubSliderStart(e) {
    this._subIdx = e.currentTarget.dataset.index
    this._isSubSliding = true
    this._updateSub(e.touches[0])
  },
  onSubSliderMove(e) {
    if (!this._isSubSliding || this._subIdx == null) return
    this._updateSub(e.touches[0])
  },
  onSubSliderEnd() { this._isSubSliding = false; this._subIdx = null },
  _updateSub(touch) {
    const idx = this._subIdx
    const query = wx.createSelectorQuery().in(this)
    query.selectAll('.subj-slider').boundingClientRect(rects => {
      if (!rects || !rects[idx]) return
      const rect = rects[idx]
      const ratio = (touch.clientX - rect.left) / rect.width
      const clamped = Math.max(0, Math.min(1, ratio))
      const minutes = Math.round(clamped * 30 / 5) * 5
      this.setData({ ['subjectGoals[' + idx + '].minutes']: Math.max(5, Math.min(30, minutes)) })
    }).exec()
  },

  onSave() {
    wx.showToast({ title: '保存成功', icon: 'success' })
  }
})
