Component({
  properties: {
    text: { type: String, value: '按钮' },
    icon: { type: String, value: '' },
    disabled: { type: Boolean, value: false },
    block: { type: Boolean, value: false },
    type: { type: String, value: 'primary' }
  },
  methods: {
    handleTap() {
      if (!this.data.disabled) {
        this.triggerEvent('tap')
      }
    }
  }
})
