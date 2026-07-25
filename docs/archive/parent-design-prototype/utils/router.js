const routes = {
  index: '/pages/index/index',
  monitor: '/pages/monitor/index',
  report: '/pages/report/index',
  mine: '/pages/mine/index',
  learningTrack: '/pages/learning-track/index',
  notification: '/pages/notification/index',
  usageDuration: '/pages/usage-duration/index',
  behaviorAnalysis: '/pages/behavior-analysis/index',
  deviceManage: '/pages/device-manage/index',
  notificationSettings: '/pages/notification-settings/index',
  learningGoal: '/pages/learning-goal/index',
  deviceUnbind: '/pages/device-unbind/index',
  deviceBindstep: '/pages/device-bindstep/index',
  login: '/pages/login/index',
  onboarding: '/pages/onboarding/index',
  bindChild: '/pages/bind-child/index',
  editProfile: '/pages/edit-profile/index',
  reportDetail: '/pages/report-detail/index',
  helpCenter: '/pages/help-center/index',
  about: '/pages/about/index',
  childManage: '/pages/child-manage/index',
  deviceInfo: '/pages/device-info/index',
  connectLog: '/pages/connect-log/index',
  firmwareUpdate: '/pages/firmware-update/index',
  taskDetail: '/pages/task-detail/index',
  behaviorDetail: '/pages/behavior-detail/index',
  subjectDetail: '/pages/subject-detail/index',
  learningRecord: '/pages/learning-record/index',
  scoreDetail: '/pages/score-detail/index',
  allTasks: '/pages/all-tasks/index'
}

const TAB_PAGES = ['index', 'monitor', 'report', 'mine']

module.exports = {
  push(name, params = {}) {
    const url = routes[name]
    if (!url) return console.error('Route not found:', name)
    const query = Object.entries(params).map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&')
    const fullUrl = url + (query ? `?${query}` : '')
    if (TAB_PAGES.includes(name)) {
      wx.switchTab({ url })
    } else {
      wx.navigateTo({ url: fullUrl })
    }
  },

  replace(name, params = {}) {
    const url = routes[name]
    if (!url) return console.error('Route not found:', name)
    const query = Object.entries(params).map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&')
    wx.redirectTo({ url: url + (query ? `?${query}` : '') })
  },

  back(delta = 1) {
    wx.navigateBack({ delta })
  },

  switchTab(name) {
    const url = routes[name]
    if (url) wx.switchTab({ url })
  }
}
