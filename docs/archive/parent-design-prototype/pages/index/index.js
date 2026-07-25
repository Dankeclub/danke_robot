const store = require('../../store/index')
const router = require('../../utils/router')
const mock = require('../../mock/index')

Page({
  data: {
    statusBarHeight: 44,
    childInfo: mock.child,
    deviceOnline: true,
    todayData: {
      studyMinutes: 45,
      taskDone: 3,
      taskTotal: 5,
      interaction: 12
    },
    quickRow1: [
      { key: 'monitor', icon: 'qi-video', label: '实时看护', bgColor: 'rgba(49,106,253,0.08)' },
      { key: 'learningTrack', icon: 'qi-book', label: '学习追踪', bgColor: 'rgba(64,117,255,0.08)' },
      { key: 'report', icon: 'qi-chart', label: '成长报告', bgColor: 'rgba(132,166,253,0.08)' }
    ],
    quickRow2: [
      { key: 'usageDuration', icon: 'qi-timer', label: '使用时长', bgColor: 'rgba(255,181,71,0.08)' },
      { key: 'behaviorAnalysis', icon: 'qi-brain', label: '行为分析', bgColor: 'rgba(172,232,40,0.08)' },
      { key: 'taskSheet', icon: 'qi-send', label: '派任务', bgColor: 'rgba(255,107,107,0.08)' }
    ],
    tasks: [
      { id: 1, title: '阅读《小王子》20分钟', status: 'completed' },
      { id: 2, title: '数学练习 - 加减法', status: 'in_progress' },
      { id: 3, title: '英语听力 15分钟', status: 'pending' }
    ],
    recentBehaviors: [
      { time: '14:30', icon: 'bh-check', text: '完成了数学练习，正确率 92%' },
      { time: '13:15', icon: 'bh-book', text: '开始阅读《小王子》' },
      { time: '11:00', icon: 'bh-message', text: '与蛋仔互动了15分钟' }
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
    sheetTasks: []
  },

  onLoad() {
    const sysInfo = wx.getWindowInfo()
    this.setData({ statusBarHeight: sysInfo.statusBarHeight || 44 })
    this._unsub = store.subscribe('deviceOnline', (online) => {
      this.setData({ deviceOnline: online })
    })
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ active: 0 })
    }
  },

  onUnload() {
    this._unsub && this._unsub()
  },

  goNotification() {
    router.push('notification')
  },

  goChildManage() {
    router.push('childManage')
  },

  onQuickEntry(e) {
    const { key } = e.currentTarget.dataset
    if (key === 'taskSheet') {
      this.setData({ showTaskSheet: true, sheetTab: 'study' })
      this._filterSheetTasks('study')
      return
    }
    router.push(key)
  },

  /* ── Task Sheet Methods ── */

  preventBubble() {},

  onSheetClose() {
    this.setData({ showTaskSheet: false })
  },

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
    setTimeout(() => {
      this.setData({ showSheetToast: false, showTaskSheet: false })
    }, 2000)
  },

  goAllTasks() {
    router.push('allTasks')
  },

  goBehaviorAnalysis() {
    router.push('behaviorAnalysis')
  },

  goTaskDetail(e) {
    const { id } = e.currentTarget.dataset
    router.push('taskDetail', { id })
  }
})
