Page({
  data: {
    activeTab: 'all',
    notificationGroups: [
      {
        date: 'today',
        dateLabel: '今天',
        notifs: [
          { id: 1, title: '学习完成提醒', time: '14:30', desc: '小明完成了今日数学练习，正确率95%', icon: 'qi-book', iconBg: '#EBF0FF', type: 'study', read: false },
          { id: 2, title: '行为提醒', time: '13:15', desc: '检测到小明坐姿不端正，已持续10分钟', icon: 'activity', iconBg: '#FFF4E0', type: 'behavior', read: false },
          { id: 3, title: '设备提醒', time: '11:00', desc: '机器人电量低于20%，请及时充电', icon: 'battery', iconBg: '#EBF0FF', type: 'device', read: true },
          { id: 4, title: '任务完成', time: '10:20', desc: '小明完成了今日亲子任务「给爸爸画一幅画」', icon: 'circle-check-green', iconBg: '#F0F9E0', type: 'task', read: true }
        ]
      },
      {
        date: 'yesterday',
        dateLabel: '昨天',
        notifs: [
          { id: 5, title: '学习完成提醒', time: '16:00', desc: '小明完成了英语单词跟读练习', icon: 'qi-book', iconBg: '#EBF0FF', type: 'study', read: true }
        ]
      }
    ],
    filteredNotifs: []
  },

  onLoad() {
    this.filterNotifs('all')
  },

  onTabChange(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({ activeTab: tab })
    this.filterNotifs(tab)
  },

  filterNotifs(tab) {
    const groups = this.data.notificationGroups
    if (tab === 'all') {
      this.setData({ filteredNotifs: groups })
      return
    }
    const filtered = groups.map(g => ({
      ...g,
      notifs: g.notifs.filter(n => n.type === tab)
    })).filter(g => g.notifs.length > 0)
    this.setData({ filteredNotifs: filtered })
  },

  onMarkAllRead() {
    const groups = this.data.notificationGroups.map(g => ({
      ...g,
      notifs: g.notifs.map(n => ({ ...n, read: true }))
    }))
    this.setData({ notificationGroups: groups })
    this.filterNotifs(this.data.activeTab)
  }
})
