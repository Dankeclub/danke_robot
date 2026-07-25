Page({
  data: {
    activeFilter: '全部',
    filters: ['全部', '未读', '行为', '学习'],
    allNotifs: [
      { id: 1, type: 'amber', icon: '⚠', title: '坐姿不良提醒', desc: '检测到小宇坐姿倾斜超过 15°，已提醒纠正', time: '10:20', date: '今天', unread: true },
      { id: 2, type: 'mint', icon: '★', title: '学习目标达成', desc: '小宇完成了今日数学目标！连续答对 12 道心算题', time: '09:45', date: '今天', unread: true },
      { id: 3, type: 'sky', icon: '📱', title: '设备已上线', desc: '蛋仔机器人重新连接，电量 80%', time: '08:10', date: '今天', unread: false },
      { id: 4, type: 'mint', icon: '📖', title: '英语单词完成', desc: '20 个新单词练习完成，正确率 87%', time: '16:30', date: '昨天', unread: false },
      { id: 5, type: 'amber', icon: '⚠', title: '离屏幕太近', desc: '检测到小宇距离屏幕不足 20cm，持续 3 分钟', time: '15:10', date: '昨天', unread: false },
      { id: 6, type: 'sky', icon: '⏰', title: '使用时长提醒', desc: '今日累计使用 45 分钟，距离每日限额还有 15 分钟', time: '19:55', date: '6月21日', unread: false },
      { id: 7, type: 'sky', icon: '📄', title: '周报已生成', desc: '小宇本周学习周报已生成，数学进步明显', time: '09:00', date: '6月21日', unread: false },
      { id: 8, type: 'mint', icon: '📦', title: '系统更新完成', desc: '蛋仔系统已更新至 v2.4.1，新增情绪识别功能', time: '22:30', date: '6月20日', unread: false }
    ],
    groupedNotifs: []
  },

  onLoad() {
    this.applyFilter()
  },

  onFilter(e) {
    this.setData({ activeFilter: e.currentTarget.dataset.filter })
    this.applyFilter()
  },

  applyFilter() {
    const { activeFilter, allNotifs } = this.data
    let filtered = allNotifs

    if (activeFilter === '未读') {
      filtered = allNotifs.filter(n => n.unread)
    } else if (activeFilter === '行为') {
      filtered = allNotifs.filter(n => n.type === 'amber')
    } else if (activeFilter === '学习') {
      filtered = allNotifs.filter(n => n.type === 'mint' || n.type === 'sky')
    }

    // 按日期分组
    const groups = {}
    filtered.forEach(n => {
      if (!groups[n.date]) groups[n.date] = []
      groups[n.date].push(n)
    })

    const groupedNotifs = Object.keys(groups).map(date => ({
      date,
      items: groups[date]
    }))

    this.setData({ groupedNotifs })
  },

  onTapNotif(e) {
    const id = e.currentTarget.dataset.id
    // 标记为已读
    const allNotifs = this.data.allNotifs.map(n => {
      if (n.id === id) n.unread = false
      return n
    })
    this.setData({ allNotifs })
    this.applyFilter()
    // TODO: 跳转对应详情页
  }
})
