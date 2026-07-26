Page({
  data: {
    dankeState: 'online',
    states: ['online', 'focused', 'tired', 'offline'],
    childName: '小宇',
    statusText: '在线 · 正在解答数学题',
    todayItems: [],
    timelineItems: [
      { time: '10:42', text: '专注时段 · 连续 25 分钟', tag: '优秀', tagColor: 'mint', color: 'mint' },
      { time: '10:20', text: '坐姿不良提醒', tag: '已纠正', tagColor: 'amber', color: 'amber' },
      { time: '09:55', text: '回到学习区域', tag: '', tagColor: '', color: 'sky' }
    ],
    taskSectionTitle: '今日任务',
    // 派任务面板
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
    online:  { statusText: '在线 · 正在解答数学题' },
    focused: { statusText: '专注 · 答题中' },
    tired:   { statusText: '今日已用 86 分钟，休息一下吧' },
    offline: { statusText: '设备已离线' }
  },

  onSwitchState(e) {
    const state = e.currentTarget.dataset.state
    const cfg = this.stateConfig[state]
    this.setData({
      dankeState: state,
      statusText: cfg.statusText
    })
  },

  goUsage()    { wx.navigateTo({ url: '/pages/usage/usage' }) },
  goBehavior() { wx.navigateTo({ url: '/pages/behavior/behavior' }) },
  goLearning() { wx.navigateTo({ url: '/pages/learning/learning' }) },
  goReport()   { wx.navigateTo({ url: '/pages/report/report' }) },
  goDevice()   { wx.navigateTo({ url: '/pages/device/device' }) },

  goNotifs() {
    wx.navigateTo({ url: '/pages/notifications/notifications' })
  },

  onShow() {
    var app = getApp()
    if (app.globalData.childInfo) {
      this.setData({ childName: app.globalData.childInfo.name })
    }
    this._loadTasks()
  },

  _loadTasks: function () {
    var dt = new Date()
    var today = dt.getFullYear() + '/' + (dt.getMonth() + 1) + '/' + dt.getDate()
    var saved = wx.getStorageSync('dispatchedTasks') || []
    var todaysTasks = saved.filter(function (t) { return t.date === today })
    if (todaysTasks.length === 0) {
      this.setData({ todayItems: [] })
      return
    }
    var items = todaysTasks.map(function (t) {
      return { text: t.name, sub: t.time + ' 派发', done: false }
    })
    this.setData({ todayItems: items, taskSectionTitle: '今日任务' })
  },

  // ===== 派任务面板 =====

  _updateDisplay() {
    var tab = this.data.activeTaskTab
    var presets = this.data.taskItems[tab] || []
    var customs = this.data.customTasks[tab] || []
    var display = [
      ...presets.map(function (item, i) { return { ...item, isCustom: false, _idx: i, _key: 'p' + i } }),
      ...customs.map(function (item, i) { return { ...item, isCustom: true, _idx: i, _key: 'c' + i } })
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
    this.setData({ showTaskSheet: true, selectedTasks: [], selectedMap: {}, customInput: '', selectAll: false })
  },

  closeTaskSheet() {
    this.setData({ showTaskSheet: false })
  },

  onTaskTabTap(e) {
    var idx = Number(e.currentTarget.dataset.index)
    this.setData({ activeTaskTab: idx, selectedTasks: [], selectedMap: {}, customInput: '', selectAll: false })
    this._updateDisplay()
  },

  onTaskSelect(e) {
    var idx = Number(e.currentTarget.dataset.index)
    if (idx < 0 || idx >= this.data.displayTasks.length) return
    var selected = this.data.selectedTasks.slice()
    var pos = selected.indexOf(idx)
    if (pos >= 0) {
      selected.splice(pos, 1)
    } else {
      selected.push(idx)
    }
    this.setData({ selectedTasks: selected, selectAll: selected.length === this.data.displayTasks.length })
    this._syncSelectedMap()
  },

  onSelectAll() {
    var all = this.data.selectAll
    if (all) {
      this.setData({ selectedTasks: [], selectedMap: {}, selectAll: false })
    } else {
      var allIdx = this.data.displayTasks.map(function (_, i) { return i })
      this.setData({ selectedTasks: allIdx, selectAll: true })
      this._syncSelectedMap()
    }
  },

  onCustomInput(e) {
    this.setData({ customInput: e.detail.value })
  },

  onAddCustomTask() {
    var text = this.data.customInput.trim()
    if (!text) {
      wx.showToast({ title: '请输入任务内容', icon: 'none' })
      return
    }
    var tab = this.data.activeTaskTab
    var customs = JSON.parse(JSON.stringify(this.data.customTasks))
    customs[tab].push({ name: text, icon: 'ic-edit-amber' })
    this.setData({ customTasks: customs, customInput: '' })
    this._updateDisplay()
  },

  onDeleteCustomTask(e) {
    var idx = Number(e.currentTarget.dataset.index)
    var item = this.data.displayTasks[idx]
    if (!item || !item.isCustom) return
    var tab = this.data.activeTaskTab
    var customs = JSON.parse(JSON.stringify(this.data.customTasks))
    customs[tab].splice(item._idx, 1)
    var selected = this.data.selectedTasks.filter(function (i) { return i !== idx })
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
    var saved = wx.getStorageSync('dispatchedTasks') || []
    saved.push.apply(saved, tasks)
    wx.setStorageSync('dispatchedTasks', saved)
    var app = getApp()
    app.globalData.dispatchedTasks = saved
    wx.showToast({ title: '已派发 ' + tasks.length + ' 个任务', icon: 'success' })
    this.setData({ showTaskSheet: false, selectedTasks: [], selectedMap: {}, selectAll: false })
    this._loadTasks()
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

  noop() {}
})
