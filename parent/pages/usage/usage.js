Page({
  data: {
    activeSeg: '日',
    segments: ['日', '周', '月'],
    chartTitle: '每日使用时长 · 本周',
    dayBars: [
      { label: '一', value: 78, height: 78, color: '#8899D5' },
      { label: '二', value: 86, height: 86, color: '#8899D5' },
      { label: '三', value: 72, height: 72, color: '#8899D5' },
      { label: '四', value: 96, height: 96, color: '#7780BF' },
      { label: '五', value: 66, height: 66, color: '#8899D5' },
      { label: '六', value: 54, height: 54, color: '#8899D5' },
      { label: '日', value: 46, height: 46, color: '#A3B5E0' }
    ],
    weekBars: [
      { label: 'W1', value: 420, height: 84, color: '#8899D5' },
      { label: 'W2', value: 456, height: 91, color: '#8899D5' },
      { label: 'W3', value: 398, height: 80, color: '#8899D5' },
      { label: 'W4', value: 482, height: 96, color: '#7780BF' }
    ],
    monthBars: [
      { label: '1月', value: 1820, height: 76, color: '#8899D5' },
      { label: '2月', value: 1680, height: 70, color: '#8899D5' },
      { label: '3月', value: 2040, height: 85, color: '#8899D5' },
      { label: '4月', value: 1920, height: 80, color: '#8899D5' },
      { label: '5月', value: 2160, height: 90, color: '#7780BF' },
      { label: '6月', value: 2064, height: 86, color: '#8899D5' }
    ],
    chartBars: [
      { label: '一', value: 78, height: 78, color: '#8899D5' },
      { label: '二', value: 86, height: 86, color: '#8899D5' },
      { label: '三', value: 72, height: 72, color: '#8899D5' },
      { label: '四', value: 96, height: 96, color: '#7780BF' },
      { label: '五', value: 66, height: 66, color: '#8899D5' },
      { label: '六', value: 54, height: 54, color: '#8899D5' },
      { label: '日', value: 46, height: 46, color: '#A3B5E0' }
    ],
    modules: [
      { key: 'math', name: '数学', icon: '数', time: 36, percent: 90 },
      { key: 'sci',  name: '科学', icon: '科', time: 26, percent: 65 },
      { key: 'eng',  name: '英语', icon: '英', time: 14, percent: 35 },
      { key: 'poem', name: '诗歌', icon: '诗', time: 10, percent: 25 }
    ]
  },

  onSwitchSeg(e) {
    const seg = e.currentTarget.dataset.seg
    const titles = { '日': '每日使用时长 · 本周', '周': '每周使用时长 · 本月', '月': '每月使用时长 · 本年' }
    const bars = { '日': this.data.dayBars, '周': this.data.weekBars, '月': this.data.monthBars }
    this.setData({
      activeSeg: seg,
      chartTitle: titles[seg],
      chartBars: bars[seg]
    })
  }
})
