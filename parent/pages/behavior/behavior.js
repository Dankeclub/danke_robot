Page({
  data: {
    activeTab: 'focus',
    tabs: [
      { key: 'focus',    label: '专注度' },
      { key: 'pose',     label: '姿态' },
      { key: 'location', label: '位置' }
    ],
    poseRecords: [
      { type: 'good', label: '标准坐姿', desc: '大部分时间保持良好', pct: 78 },
      { type: 'warn', label: '轻微倾斜', desc: '检测到 2 次提醒', pct: 15 },
      { type: 'bad',  label: '明显歪斜', desc: '需关注纠正', pct: 7 }
    ],
    locationRecords: [
      { key: 'living', name: '客厅', icon: '🏠', time: '3.2h', percent: 65 },
      { key: 'study',  name: '书房', icon: '📚', time: '1.2h', percent: 25 },
      { key: 'bed',    name: '卧室', icon: '🛏', time: '30m',  percent: 10 }
    ]
  },

  onSwitchTab(e) {
    this.setData({ activeTab: e.currentTarget.dataset.tab })
  }
})
