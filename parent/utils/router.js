// 页面路由工具

const TAB_PAGES = ['pages/home/home', 'pages/report/report', 'pages/monitor/monitor', 'pages/learning/learning', 'pages/profile/profile']

/**
 * 导航到指定页面
 * @param {string} url - 页面路径
 * @param {boolean} isTab - 是否为 TabBar 页面
 */
function navigateTo(url, isTab) {
  if (isTab) {
    wx.switchTab({ url })
  } else {
    wx.navigateTo({ url })
  }
}

/**
 * 返回上一页
 */
function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    wx.navigateBack()
  } else {
    wx.switchTab({ url: '/pages/home/home' })
  }
}

/**
 * 切换到 TabBar 页面
 * @param {number} index - Tab 索引 0-4
 */
function switchTab(index) {
  if (index >= 0 && index < TAB_PAGES.length) {
    wx.switchTab({ url: '/' + TAB_PAGES[index] })
  }
}

module.exports = {
  TAB_PAGES,
  navigateTo,
  goBack,
  switchTab
}
