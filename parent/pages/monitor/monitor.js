Page({
  data: {
    dankeState: 'online',
    states: ['online', 'focused', 'tired', 'offline'],
    childName: '小宇',
    statusLabel: '在线 · 客厅',
    statusDetail: '正在客厅 · 答题中',
    isDragging: false,
    isMoving: false,
    thumbX: 0,
    thumbY: 0,
    directionText: '推摇杆控制方向',
    msgText: '',
    presets: ['真棒！', '继续加油', '休息一下', '坐直哦', '喝点水', '妈妈爱你'],
    showTaskSheet: false,
    taskTabs: ['学习', '生活', '运动'],
    activeTaskTab: 0,
    taskItems: [
      [
        { name: '数学口算 10 题', icon: 'ic-book-pd' },
        { name: '英语单词背诵', icon: 'ic-book-pd' },
        { name: '古诗朗读 3 首', icon: 'ic-book-pd' }
      ],
      [
        { name: '整理书桌', icon: 'ic-clipboard-pd' },
        { name: '帮妈妈浇花', icon: 'ic-heart-rose' },
        { name: '收拾玩具', icon: 'ic-clipboard-pd' }
      ],
      [
        { name: '跳绳 100 下', icon: 'ic-heart-rose' },
        { name: '眼保健操', icon: 'ic-clock-pd' },
        { name: '户外散步 20 分钟', icon: 'ic-heart-rose' }
      ]
    ],
    selectedTasks: [],
    selectedMap: {},
    selectedTabTask: '',
    customTasks: [[], [], []],
    displayTasks: [],
    customInput: '',
    selectAll: false,
    safeBottom: 0
  },

  onLoad() {
    this.setData({ safeBottom: getApp().globalData.safeBottom })
  },

  stateConfig: {
    online:  { statusLabel: '在线 · 客厅',  statusDetail: '正在客厅 · 答题中' },
    focused: { statusLabel: '专注 · 答题中', statusDetail: '数学心算 · 连续答对中' },
    tired:   { statusLabel: '已用 86 分钟',  statusDetail: '使用时长超目标 · 建议休息' },
    offline: { statusLabel: '设备离线',     statusDetail: '设备已断开连接' }
  },

  onReady() {
    // 缓存摇杆基座位置，避免每次拖拽时异步查询
    const query = wx.createSelectorQuery()
    query.select('.mon-joy-base').boundingClientRect()
    query.exec((res) => {
      if (res && res[0]) {
        const r = res[0]
        this._joyRect = {
          cx: r.left + r.width / 2,
          cy: r.top + r.height / 2,
          maxOff: Math.floor(r.width * 5 / 16)
        }
      }
    })
  },

  onSwitchState(e) {
    const state = e.currentTarget.dataset.state
    const cfg = this.stateConfig[state]
    this.setData({
      dankeState: state,
      statusLabel: cfg.statusLabel,
      statusDetail: cfg.statusDetail
    })
  },

  // ===== 摇杆控制 =====

  onJoyStart(e) {
    if (!this._joyRect) return
    this.setData({ isDragging: true })
    this._updateJoy(e.touches[0])
  },

  onJoyMove(e) {
    if (!this.data.isDragging || !this._joyRect) return
    this._updateJoy(e.touches[0])
  },

  _updateJoy(touch) {
    const { cx, cy, maxOff } = this._joyRect
    let dx = touch.pageX - cx
    let dy = touch.pageY - cy
    const dist = Math.sqrt(dx * dx + dy * dy)

    if (dist > maxOff && dist > 0) {
      const ratio = maxOff / dist
      dx = dx * ratio
      dy = dy * ratio
    }

    const capped = Math.min(dist, maxOff)
    const angle = Math.atan2(-dy, dx) * 180 / Math.PI
    const idx = Math.round(((angle + 360) % 360) / 45) % 8
    const dirs = ['右', '右上', '前进', '左上', '左', '左下', '后退', '右下']

    this.setData({
      thumbX: Math.round(dx),
      thumbY: Math.round(dy),
      isMoving: dist > 6,
      directionText: dist < 6 ? '推摇杆控制方向' : dirs[idx] + ' · ' + Math.round(capped / maxOff * 100) + '%'
    })
  },

  onJoyEnd() {
    this.setData({
      isDragging: false,
      isMoving: false,
      thumbX: 0,
      thumbY: 0,
      directionText: '推摇杆控制方向'
    })
  },

  onStop() {
    this.setData({
      isDragging: false,
      isMoving: false,
      thumbX: 0,
      thumbY: 0,
      directionText: '已停止'
    })
  },

  // ===== 消息 =====

  onPresetTap(e) {
    const text = e.currentTarget.dataset.text
    if (text) {
      this.setData({ msgText: text })
    }
  },

  onMsgInput(e) {
    this.setData({ msgText: e.detail.value })
  },

  onSend() {
    const text = this.data.msgText.trim()
    if (!text) return
    wx.showToast({ title: '已发送', icon: 'success' })
    this.setData({ msgText: '' })
  },

  // ===== 派任务面板 =====

  _updateDisplay() {
    const tab = this.data.activeTaskTab
    const presets = this.data.taskItems[tab] || []
    const customs = this.data.customTasks[tab] || []
    const display = [
      ...presets.map((item, i) => ({ ...item, isCustom: false, _idx: i, _key: 'p' + i })),
      ...customs.map((item, i) => ({ ...item, isCustom: true, _idx: i, _key: 'c' + i }))
    ]
    this.setData({ displayTasks: display })
  },

  _syncSelectedMap() {
    var map = {}
    this.data.selectedTasks.forEach(function (i) { map[i] = true })
    this.setData({ selectedMap: map })
  },

  openTask() {
    this._updateDisplay()
    this.setData({ showTaskSheet: true, selectedTasks: [], selectedMap: {}, selectedTabTask: '', customInput: '', selectAll: false })
  },

  closeTaskSheet() {
    this.setData({ showTaskSheet: false })
  },

  onTaskTabTap(e) {
    const idx = Number(e.currentTarget.dataset.index)
    this.setData({ activeTaskTab: idx, selectedTasks: [], selectedMap: {}, selectedTabTask: '', customInput: '', selectAll: false })
    this._updateDisplay()
  },

  onTaskSelect(e) {
    const idx = Number(e.currentTarget.dataset.index)
    if (idx < 0 || idx >= this.data.displayTasks.length) return
    let selected = this.data.selectedTasks.slice()
    const pos = selected.indexOf(idx)
    if (pos >= 0) {
      selected.splice(pos, 1)
    } else {
      selected.push(idx)
    }
    this.setData({ selectedTasks: selected, selectAll: selected.length === this.data.displayTasks.length })
    this._syncSelectedMap()
  },

  onSelectAll() {
    const all = this.data.selectAll
    if (all) {
      this.setData({ selectedTasks: [], selectedMap: {}, selectAll: false })
    } else {
      const allIdx = this.data.displayTasks.map(function (_, i) { return i })
      this.setData({ selectedTasks: allIdx, selectAll: true })
      this._syncSelectedMap()
    }
  },

  onCustomInput(e) {
    this.setData({ customInput: e.detail.value })
  },

  onAddCustomTask() {
    const text = this.data.customInput.trim()
    if (!text) {
      wx.showToast({ title: '请输入任务内容', icon: 'none' })
      return
    }
    const tab = this.data.activeTaskTab
    const customs = JSON.parse(JSON.stringify(this.data.customTasks))
    customs[tab].push({ name: text, icon: 'ic-edit-amber' })
    this.setData({ customTasks: customs, customInput: '' })
    this._updateDisplay()
  },

  onDeleteCustomTask(e) {
    const idx = Number(e.currentTarget.dataset.index)
    const item = this.data.displayTasks[idx]
    if (!item || !item.isCustom) return
    const tab = this.data.activeTaskTab
    const customs = JSON.parse(JSON.stringify(this.data.customTasks))
    customs[tab].splice(item._idx, 1)
    let selected = this.data.selectedTasks.filter(function (i) { return i !== idx })
    selected = selected.map(function (i) { return i > idx ? i - 1 : i })
    this.setData({ customTasks: customs, selectedTasks: selected, selectAll: false })
    this._updateDisplay()
    this._syncSelectedMap()
  },

  onSendTask() {
    if (this.data.selectedTasks.length === 0) {
      wx.showToast({ title: '请先选择任务', icon: 'none' })
      return
    }
    var tasks = []
    var self = this
    this.data.selectedTasks.forEach(function (i) {
      var item = self.data.displayTasks[i]
      if (item) tasks.push({ name: item.name, tab: self.data.activeTaskTab, time: self._now(), date: self._today() })
    })
    // 写入本地存储
    var saved = wx.getStorageSync('dispatchedTasks') || []
    saved.push.apply(saved, tasks)
    wx.setStorageSync('dispatchedTasks', saved)
    // 同步到 globalData
    var app = getApp()
    app.globalData.dispatchedTasks = saved
    wx.showToast({ title: '已派发 ' + tasks.length + ' 个任务', icon: 'success' })
    this.setData({ showTaskSheet: false, selectedTasks: [], selectedMap: {}, selectAll: false })
  },

  _now: function () {
    var d = new Date()
    var pad = function (n) { return n < 10 ? '0' + n : '' + n }
    return pad(d.getHours()) + ':' + pad(d.getMinutes())
  },

  _today: function () {
    var d = new Date()
    return d.getFullYear() + '/' + (d.getMonth() + 1) + '/' + d.getDate()
  },

  noop() {},

  onShow() {
    const app = getApp()
    if (app.globalData.childInfo) {
      this.setData({ childName: app.globalData.childInfo.name })
    }
  }
})
