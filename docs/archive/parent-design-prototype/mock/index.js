module.exports = {
  user: {
    nickName: '张妈妈',
    avatarUrl: '',
    phone: '138****8888'
  },

  child: {
    name: '小明',
    age: 6,
    gender: 'male',
    grade: '一年级',
    avatarUrl: '',
    birthday: '2020-03-15'
  },

  device: {
    id: 'DZ-001',
    name: 'AI陪伴机器人',
    model: 'DanZai Pro',
    firmware: 'v2.1.3',
    battery: 85,
    online: true,
    wifi: 'Home_WiFi',
    signal: 4,
    lastConnected: '2024-01-15 09:30:00',
    bindTime: '2023-09-01 10:00:00'
  },

  tasks: {
    today: [
      { id: 1, title: '完成数学口算练习', category: '学习', status: 'completed', time: '09:30' },
      { id: 2, title: '英语单词跟读20个', category: '学习', status: 'in_progress', time: '10:15' },
      { id: 3, title: '整理书桌', category: '生活', status: 'pending', time: '' },
      { id: 4, title: '和爸爸下一盘棋', category: '亲子', status: 'pending', time: '' },
      { id: 5, title: '阅读绘本30分钟', category: '学习', status: 'completed', time: '08:00' }
    ],
    completedCount: 2,
    totalCount: 5
  },

  learning: {
    todayMinutes: 145,
    weekMinutes: 680,
    subjects: [
      { name: '数学思维', percent: 78, todayMinutes: 45, totalLessons: 24, completedLessons: 18 },
      { name: '英语启蒙', percent: 62, todayMinutes: 35, totalLessons: 30, completedLessons: 18 },
      { name: '科学探索', percent: 45, todayMinutes: 20, totalLessons: 20, completedLessons: 9 }
    ],
    records: [
      { id: 1, title: '加减法练习', subject: '数学思维', duration: 25, score: 95, time: '09:30' },
      { id: 2, title: '单词跟读', subject: '英语启蒙', duration: 20, score: 88, time: '10:15' }
    ],
    weekData: [120, 135, 90, 145, 110, 160, 145]
  },

  behavior: {
    behaviors: [
      { id: 1, type: 'focus', title: '专注学习', desc: '连续专注25分钟', time: '10:30', icon: 'target' },
      { id: 2, type: 'posture', title: '坐姿提醒', desc: '检测到弯腰驼背', time: '09:45', icon: 'alert-triangle' },
      { id: 3, type: 'activity', title: '活动区域', desc: '主要在书房活动', time: '09:00', icon: 'map-pin' }
    ],
    focusScore: 82,
    postureScore: 75,
    interactionCount: 12
  },

  reports: {
    weekly: {
      title: '本周成长报告',
      date: '2024.1.8 - 2024.1.14',
      summary: '小明本周学习表现优秀，数学思维提升明显，专注力有所增强。建议增加户外运动时间，保持良好的作息习惯。',
      scores: { learning: 92, focus: 85, interaction: 78, exercise: 65 }
    },
    history: [
      { id: 1, title: '1月第2周报告', date: '2024.1.8 - 2024.1.14', score: 85 },
      { id: 2, title: '1月第1周报告', date: '2024.1.1 - 2024.1.7', score: 80 },
      { id: 3, title: '12月第4周报告', date: '2023.12.25 - 2023.12.31', score: 82 }
    ]
  },

  notifications: {
    notifications: [
      { id: 1, type: 'learning', title: '学习提醒', content: '小明已完成今日数学口算练习，正确率95%', time: '10:30', read: false },
      { id: 2, type: 'behavior', title: '行为提醒', content: '小明坐姿不端正，已持续15分钟', time: '09:45', read: false },
      { id: 3, type: 'device', title: '设备通知', content: '蛋仔电量低于20%，请及时充电', time: '08:20', read: false },
      { id: 4, type: 'task', title: '任务通知', content: '小明已完成任务「阅读绘本30分钟」', time: '昨天 16:00', read: true },
      { id: 5, type: 'learning', title: '学习提醒', content: '小明英语跟读完成，发音准确度提升5%', time: '昨天 11:20', read: true }
    ]
  }
}
