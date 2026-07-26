const AVATAR_COLORS = ['#FDEDDD', '#dff6e6', '#c1d6f1', '#fed4d8', '#F7E6D4']

function buildYears() {
  const years = []
  for (let y = 2026; y >= 2014; y--) years.push(y)
  return years
}
function buildMonths() {
  const months = []
  for (let m = 1; m <= 12; m++) months.push(m)
  return months
}

Page({
  data: {
    mode: 'create',
    form: {
      name: '小宇',
      birthYear: 2019,
      birthMonth: 6,
      gender: 'boy'
    },
    avatarColor: AVATAR_COLORS[0],
    avatarColorIdx: 0,
    showPicker: false,
    pickerValue: [0, 0],
    years: buildYears(),
    months: buildMonths()
  },

  onLoad(options) {
    const app = getApp()
    const saved = app.globalData.childInfo
    if (saved) {
      this.setData({
        form: {
          name: saved.name || '小宇',
          birthYear: saved.birthYear || 2019,
          birthMonth: saved.birthMonth || 6,
          gender: saved.gender || 'boy'
        }
      })
    }
    const { birthYear, birthMonth } = this.data.form
    const yearIdx = this.data.years.indexOf(birthYear)
    const monthIdx = birthMonth - 1
    if (options.mode) this.setData({ mode: options.mode })
    this.setData({
      pickerValue: [yearIdx >= 0 ? yearIdx : 7, monthIdx >= 0 ? monthIdx : 5]
    })
    this._updateDerived(birthYear, birthMonth, this.data.form.gender)
  },

  // 根据年月+性别更新显示文字
  _updateDerived(birthYear, birthMonth, gender) {
    const age = new Date().getFullYear() - birthYear
    const genderText = gender === 'boy' ? '男孩' : '女孩'
    this.setData({
      ageText: `${age} 岁 · ${genderText}`
    })
  },

  // ===== 表单输入 =====

  onInputName(e) {
    this.setData({ 'form.name': e.detail.value })
  },

  onSelectGender(e) {
    const gender = e.currentTarget.dataset.gender
    this.setData({ 'form.gender': gender })
    this._updateDerived(this.data.form.birthYear, this.data.form.birthMonth, gender)
  },

  // ===== 日期选择器 =====

  onPickBirth() {
    const { birthYear, birthMonth } = this.data.form
    const yearIdx = this.data.years.indexOf(birthYear)
    const monthIdx = birthMonth - 1
    this.setData({
      showPicker: true,
      pickerValue: [yearIdx >= 0 ? yearIdx : 7, monthIdx >= 0 ? monthIdx : 5]
    })
  },

  onClosePicker() {
    this.setData({ showPicker: false })
  },

  onPickerChange(e) {
    this.setData({ pickerValue: e.detail.value })
  },

  onConfirmPicker() {
    const [yi, mi] = this.data.pickerValue
    const birthYear = this.data.years[yi]
    const birthMonth = this.data.months[mi]
    // 先用新值更新显示（同步），再 setData 持久化（异步）
    this._updateDerived(birthYear, birthMonth, this.data.form.gender)
    this.setData({
      'form.birthYear': birthYear,
      'form.birthMonth': birthMonth,
      showPicker: false
    })
  },

  // ===== 头像颜色 =====

  onChangeAvatar() {
    const next = (this.data.avatarColorIdx + 1) % AVATAR_COLORS.length
    this.setData({ avatarColor: AVATAR_COLORS[next], avatarColorIdx: next })
  },

  // ===== 导航 & 保存 & 解绑 =====

  goDevice() {
    wx.navigateTo({ url: '/pages/device/device' })
  },

  onSave() {
    const name = (this.data.form.name || '').trim()
    if (!name) {
      wx.showToast({ title: '请输入孩子昵称', icon: 'none' })
      return
    }
    const childInfo = {
      name: name,
      birthYear: this.data.form.birthYear,
      birthMonth: this.data.form.birthMonth,
      gender: this.data.form.gender
    }
    const app = getApp()
    app.globalData.childInfo = childInfo
    wx.setStorageSync('childInfo', childInfo)
    wx.showToast({ title: '保存成功', icon: 'success' })
    setTimeout(() => {
      if (this.data.mode === 'create') {
        wx.switchTab({ url: '/pages/home/home' })
      } else {
        wx.navigateBack()
      }
    }, 1500)
  },

  onUnbind() {
    wx.showModal({
      title: '解绑孩子',
      content: '确定要解绑当前孩子吗？此操作不可撤销。',
      confirmColor: '#C77974',
      success: (res) => {
        if (res.confirm) {
          wx.showToast({ title: '已解绑', icon: 'success' })
        }
      }
    })
  }
})
