Page({
  data: {
    statusBarHeight: 44,
    deviceOnline: true,
    batteryLevel: 85,
    wifiName: 'Home_WiFi',
    message: '',
    messages: [
      { id: 1, type: 'system', content: '蛋仔已连接，开始实时看护' },
      { id: 2, type: 'robot', content: '小明正在认真学习数学哦~' },
      { id: 3, type: 'user', content: '宝贝加油！' }
    ],
    /* Task Sheet */
    showTaskSheet: false,
    sheetTab: 'study',
    showSheetToast: false,
    sheetStudyTasks: [
      { id: 1, name: '阅读《小王子》20分钟', desc: '语文阅读 · 预计20分钟', checked: false },
      { id: 2, name: '数学练习 - 加减法', desc: '数学思维 · 15道题', checked: false },
      { id: 3, name: '英语听力 15分钟', desc: '英语启蒙 · 听读练习', checked: false },
      { id: 4, name: '科学小实验', desc: '动手探索 · 1个实验', checked: false },
      { id: 5, name: '跟蛋仔对话10分钟', desc: '自由对话练习', checked: false }
    ],
    sheetLifeTasks: [
      { id: 6, name: '整理床铺', desc: '好习惯养成', checked: false },
      { id: 7, name: '帮忙摆放碗筷', desc: '家务小帮手', checked: false },
      { id: 8, name: '收拾玩具', desc: '学会分类整理', checked: false }
    ],
    sheetParentTasks: [
      { id: 9, name: '和爸妈一起阅读', desc: '亲子时光 · 20分钟', checked: false },
      { id: 10, name: '给爸爸画一幅画', desc: '亲子互动 · 创意表达', checked: false }
    ],
    sheetTasks: [],
    /* Joystick */
    joyLeft: 60,
    joyTop: 60,
    joyDir: ''
  },

  onLoad() {
    const sysInfo = wx.getWindowInfo()
    this.setData({ statusBarHeight: sysInfo.statusBarHeight || 44 })
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ active: 1 })
    }
  },

  onPlayVideo() { wx.showToast({ title: '视频播放中', icon: 'none' }) },
  onScreenshot() { wx.showToast({ title: '已截图保存', icon: 'success' }) },
  onFullscreen() { wx.showToast({ title: '全屏模式', icon: 'none' }) },
  onVoice() { wx.showToast({ title: '语音对讲开启', icon: 'none' }) },

  onInputMessage(e) { this.setData({ message: e.detail.value }) },

  onSendMessage() {
    if (!this.data.message.trim()) return
    const messages = [...this.data.messages, { id: Date.now(), type: 'user', content: this.data.message }]
    this.setData({ messages, message: '' })
  },

  onSendTask() {
    this.setData({ showTaskSheet: true, sheetTab: 'study' })
    this._filterSheetTasks('study')
  },

  /* ── Joystick ── */

  onJoystickStart(e) {
    const touch = e.touches[0]
    const query = wx.createSelectorQuery().in(this)
    query.select('.joystick-bg').boundingClientRect(rect => {
      if (!rect) return
      this._joyCX = rect.left + rect.width / 2
      this._joyCY = rect.top + rect.height / 2
      this._joyRadius = rect.width / 2
      this._thumbSize = this._joyRadius * 100 / 110 // thumb is 100rpx, bg is 220rpx
      this._updateJoystick(touch.clientX, touch.clientY)
    }).exec()
  },

  onJoystickMove(e) {
    if (this._joyCX == null) return
    const touch = e.touches[0]
    this._updateJoystick(touch.clientX, touch.clientY)
  },

  _updateJoystick(px, py) {
    const dx = px - this._joyCX
    const dy = py - this._joyCY
    const dist = Math.sqrt(dx * dx + dy * dy)
    const maxDist = this._joyRadius * 0.7

    // Clamp to circle
    let clampedDx = dx
    let clampedDy = dy
    if (dist > maxDist && dist > 0) {
      clampedDx = dx / dist * maxDist
      clampedDy = dy / dist * maxDist
    }

    // Convert px offset to rpx offset (center = 60rpx, max offset = 60rpx)
    const ratio = 60 / maxDist
    const leftRpx = 60 + clampedDx * ratio
    const topRpx = 60 + clampedDy * ratio

    // Determine direction
    let dir = ''
    const absDx = Math.abs(dx)
    const absDy = Math.abs(dy)
    if (dist < 8) dir = ''
    else if (absDx > absDy) dir = dx > 0 ? 'right' : 'left'
    else dir = dy > 0 ? 'down' : 'up'

    this.setData({
      joyLeft: Math.round(Math.max(0, Math.min(120, leftRpx))),
      joyTop: Math.round(Math.max(0, Math.min(120, topRpx))),
      joyDir: dir
    })
  },

  onJoystickEnd() {
    this._joyCX = null
    this.setData({ joyLeft: 60, joyTop: 60, joyDir: '' })
  },

  /* ── Task Sheet ── */
  preventBubble() {},

  onSheetClose() { this.setData({ showTaskSheet: false }) },

  onSheetTab(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({ sheetTab: tab })
    this._filterSheetTasks(tab)
  },

  _filterSheetTasks(tab) {
    const key = tab === 'study' ? 'sheetStudyTasks' : tab === 'life' ? 'sheetLifeTasks' : 'sheetParentTasks'
    this.setData({ sheetTasks: this.data[key] })
  },

  onSheetToggle(e) {
    const id = e.currentTarget.dataset.id
    const tab = this.data.sheetTab
    const key = tab === 'study' ? 'sheetStudyTasks' : tab === 'life' ? 'sheetLifeTasks' : 'sheetParentTasks'
    const tasks = this.data[key].map(t => t.id === id ? { ...t, checked: !t.checked } : t)
    this.setData({ [key]: tasks })
    this._filterSheetTasks(tab)
  },

  onSheetSend() {
    const tab = this.data.sheetTab
    const key = tab === 'study' ? 'sheetStudyTasks' : tab === 'life' ? 'sheetLifeTasks' : 'sheetParentTasks'
    const checked = this.data[key].filter(t => t.checked)
    if (checked.length === 0) {
      wx.showToast({ title: '请先选择任务', icon: 'none' })
      return
    }
    this.setData({ showSheetToast: true })
    setTimeout(() => { this.setData({ showSheetToast: false, showTaskSheet: false }) }, 2000)
  }
})
