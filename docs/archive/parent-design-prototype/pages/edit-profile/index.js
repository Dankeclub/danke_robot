Page({
  data: {
    formData: {
      nickname: '张妈妈',
      phone: '138****5678',
      childName: '小明',
      childAge: '7岁',
      childGrade: '二年级'
    },
    ages: ['3岁','4岁','5岁','6岁','7岁','8岁','9岁','10岁','11岁','12岁'],
    grades: ['幼儿园小班','幼儿园中班','幼儿园大班','一年级','二年级','三年级','四年级','五年级','六年级']
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ ['formData.' + field]: e.detail.value })
  },

  onAgeChange(e) {
    const idx = e.detail.value
    this.setData({ 'formData.childAge': this.data.ages[idx] })
  },

  onGradeChange(e) {
    const idx = e.detail.value
    this.setData({ 'formData.childGrade': this.data.grades[idx] })
  },

  onAvatarTap() {
    wx.showToast({ title: '更换头像', icon: 'none' })
  },

  onSave() {
    wx.showToast({ title: '保存成功', icon: 'success' })
    setTimeout(() => wx.switchTab({ url: '/pages/index/index' }), 1500)
  }
})
