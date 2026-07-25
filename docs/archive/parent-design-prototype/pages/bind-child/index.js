Page({
  data: {
    childName: '',
    selectedAge: '',
    selectedGrade: '',
    ages: ['3岁', '4岁', '5岁', '6岁', '7岁', '8岁', '9岁', '10岁', '11岁', '12岁'],
    grades: ['幼儿园小班', '幼儿园中班', '幼儿园大班', '一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
  },

  onChildNameInput(e) {
    this.setData({ childName: e.detail.value })
  },

  onAgeChange(e) {
    const idx = e.detail.value
    this.setData({ selectedAge: this.data.ages[idx] })
  },

  onGradeChange(e) {
    const idx = e.detail.value
    this.setData({ selectedGrade: this.data.grades[idx] })
  },

  onBind() {
    if (!this.data.childName) {
      wx.showToast({ title: '请输入孩子昵称', icon: 'none' })
      return
    }
    wx.redirectTo({ url: '/pages/edit-profile/index' })
  },

  onSkip() {
    wx.redirectTo({ url: '/pages/edit-profile/index' })
  }
})
