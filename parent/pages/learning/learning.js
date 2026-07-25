Page({
  data: {
    modules: [
      { key: 'math',   label: '数学', percent: 92, done: 12, total: 13, unit: '题', color: '#778ccd' },
      { key: 'sci',    label: '科学', percent: 67, done: 4,  total: 6,  unit: '实验', color: '#4F9A5F' },
      { key: 'eng',    label: '英语', percent: 84, done: 16, total: 19, unit: '词', color: '#D97A84' },
      { key: 'poem',   label: '诗歌', percent: 56, done: 3,  total: 5,  unit: '首', color: '#97979C' },
      { key: 'music',  label: '音乐', percent: 77, done: 7,  total: 9,  unit: '首', color: '#D4892E' },
      { key: 'puzzle', label: '思维', percent: 46, done: 3,  total: 6,  unit: '关', color: '#4F9A5F' }
    ],
    recentItems: [
      { key: 'math', name: '心算', percent: 92 },
      { key: 'sci',  name: '实验', percent: 67 },
      { key: 'eng',  name: '单词', percent: 84 }
    ]
  },

  goGoal() {
    wx.navigateTo({ url: '/pages/goal/goal' })
  }
})
