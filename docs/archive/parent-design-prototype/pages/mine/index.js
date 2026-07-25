const router = require('../../utils/router')
const mock = require('../../mock/index')
const user = mock.user
const child = mock.child
const device = mock.device

Page({
  data: {
    statusBarHeight: 44,
    userInfo: user,
    childInfo: child,
    deviceInfo: device,
    showLogoutDialog: false,
    menuItems: [
      { key: 'deviceManage', icon: 'smartphone-blue', label: '设备管理' },
      { key: 'notificationSettings', icon: 'bell-blue', label: '通知设置' },
      { key: 'learningGoal', icon: 'target-blue', label: '学习目标' },
      { key: 'helpCenter', icon: 'life-buoy-blue', label: '帮助中心' },
      { key: 'about', icon: 'info-blue', label: '关于我们' }
    ]
  },

  onLoad() {
    const sysInfo = wx.getWindowInfo()
    this.setData({ statusBarHeight: sysInfo.statusBarHeight || 44 })
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ active: 3 })
    }
  },

  goEditProfile() {
    router.push('editProfile')
  },

  goChildManage() {
    router.push('childManage')
  },

  goDeviceManage() {
    router.push('deviceManage')
  },

  onMenuTap(e) {
    const { key } = e.currentTarget.dataset
    router.push(key)
  },

  showLogout() {
    this.setData({ showLogoutDialog: true })
  },

  onLogoutCancel() {
    this.setData({ showLogoutDialog: false })
  },

  onLogoutConfirm() {
    this.setData({ showLogoutDialog: false })
    wx.clearStorageSync()
    router.replace('login')
  }
})
