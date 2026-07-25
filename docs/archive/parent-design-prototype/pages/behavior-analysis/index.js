Page({
  data: {
    activityAreas: [
      { name: '书桌区域', percent: 55, color: '#316AFD' },
      { name: '客厅', percent: 25, color: '#84A6FD' },
      { name: '卧室', percent: 15, color: '#ACE828' },
      { name: '其他', percent: 5, color: '#FFB547' }
    ],
    suggestions: [
      { id: 1, text: '小明今日专注度较高，建议保持当前学习节奏', color: '#ACE828' },
      { id: 2, text: '检测到坐姿偏差较多，建议每30分钟提醒休息', color: '#FFB547' },
      { id: 3, text: '活动范围集中在书桌区域，建议增加户外活动', color: '#316AFD' }
    ]
  }
})
