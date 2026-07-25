Page({
  data: {
    activeSeg: '日',
    segments: ['日', '周', '月'],
    chartBars: [
      { label: '一', value: 78, height: 78, color: '#778ccd' },
      { label: '二', value: 86, height: 86, color: '#778ccd' },
      { label: '三', value: 72, height: 72, color: '#778ccd' },
      { label: '四', value: 96, height: 96, color: '#5B6AB0' },
      { label: '五', value: 66, height: 66, color: '#778ccd' },
      { label: '六', value: 54, height: 54, color: '#778ccd' },
      { label: '日', value: 46, height: 46, color: '#9AACDE' }
    ],
    modules: [
      { key: 'math', name: '数学', icon: '∑', time: 36, percent: 90 },
      { key: 'sci',  name: '科学', icon: '🔍', time: 26, percent: 65 },
      { key: 'eng',  name: '英语', icon: '💻', time: 14, percent: 35 },
      { key: 'poem', name: '诗歌', icon: '📖', time: 10, percent: 25 }
    ]
  },

  onSwitchSeg(e) {
    this.setData({ activeSeg: e.currentTarget.dataset.seg })
  }
})
