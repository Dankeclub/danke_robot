module.exports = {
  get(key) {
    try {
      return wx.getStorageSync(key)
    } catch (e) {
      return null
    }
  },

  set(key, value) {
    try {
      wx.setStorageSync(key, value)
    } catch (e) {
      console.error('Storage set error:', e)
    }
  },

  remove(key) {
    try {
      wx.removeStorageSync(key)
    } catch (e) {
      console.error('Storage remove error:', e)
    }
  },

  clear() {
    try {
      wx.clearStorageSync()
    } catch (e) {
      console.error('Storage clear error:', e)
    }
  }
}
