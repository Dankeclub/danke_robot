const router = require('../../utils/router')

Page({
  data: {
    statusBarHeight: 44,
    activeTab: 'daily',

    /* Daily data */
    aiTitle: 'AI 日报总结 · 6月21日',
    aiText: '小明今天学习状态良好，完成了3项任务。数学正确率提升至92%，阅读专注时间增加10分钟。建议增加英语听力练习时间。',
    scores: [
      { label: '学习', val: 92, color: 'var(--color-primary)' },
      { label: '专注', val: 85, color: 'var(--color-secondary)' },
      { label: '互动', val: 78, color: 'var(--color-light-blue)' },
      { label: '运动', val: 65, color: 'var(--color-accent-green)' }
    ],
    historyList: [
      { id: 1, tag: '今日学习概览', date: '6月20日', desc: '完成4项任务，专注度88分', type: 'daily' },
      { id: 2, tag: '本周成长周报', date: '6月14-20日', desc: '本周学习时长累计5.2h，进步明显', type: 'weekly' },
      { id: 3, tag: '今日学习概览', date: '6月19日', desc: '完成2项任务，需加强英语练习', type: 'daily' }
    ],
    filteredHistory: []
  },

  onLoad() {
    const sysInfo = wx.getWindowInfo()
    this.setData({ statusBarHeight: sysInfo.statusBarHeight || 44 })
    this._filterHistory()
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ active: 2 })
    }
  },

  onTabChange(e) {
    const tab = e.currentTarget.dataset.tab
    if (tab === this.data.activeTab) return

    if (tab === 'daily') {
      this.setData({
        activeTab: 'daily',
        aiTitle: 'AI 日报总结 · 6月21日',
        aiText: '小明今天学习状态良好，完成了3项任务。数学正确率提升至92%，阅读专注时间增加10分钟。建议增加英语听力练习时间。',
        scores: [
          { label: '学习', val: 92, color: 'var(--color-primary)' },
          { label: '专注', val: 85, color: 'var(--color-secondary)' },
          { label: '互动', val: 78, color: 'var(--color-light-blue)' },
          { label: '运动', val: 65, color: 'var(--color-accent-green)' }
        ]
      })
    } else {
      this.setData({
        activeTab: 'weekly',
        aiTitle: 'AI 周报总结 · 第24周',
        aiText: '本周小明学习表现优秀，累计学习5.2小时。数学和阅读进步明显，专注度稳定。周末亲子互动活跃，运动完成指标。下周建议加强英语听力训练。',
        scores: [
          { label: '学习', val: 88, color: 'var(--color-primary)' },
          { label: '专注', val: 82, color: 'var(--color-secondary)' },
          { label: '互动', val: 90, color: 'var(--color-light-blue)' },
          { label: '运动', val: 72, color: 'var(--color-accent-green)' }
        ]
      })
    }
    this._filterHistory()
  },

  _filterHistory() {
    const type = this.data.activeTab === 'daily' ? 'daily' : 'weekly'
    const filtered = this.data.historyList.filter(h => h.type === type)
    this.setData({ filteredHistory: filtered })
  },

  onHistoryTap(e) {
    router.push('reportDetail', { id: e.currentTarget.dataset.id })
  }
})
