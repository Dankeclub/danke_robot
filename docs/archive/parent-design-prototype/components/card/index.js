Component({
  properties: {
    title: { type: String, value: '' },
    showArrow: { type: Boolean, value: false },
    padding: { type: String, value: '32rpx' }
  },
  methods: {
    onHeaderTap() {
      this.triggerEvent('headertap')
    }
  }
})
