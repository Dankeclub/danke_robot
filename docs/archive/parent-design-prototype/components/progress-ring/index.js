Component({
  properties: {
    percent: { type: Number, value: 0 },
    size: { type: Number, value: 120 },
    strokeWidth: { type: Number, value: 8 },
    label: { type: String, value: '' },
    color: { type: String, value: '#316AFD' }
  },
  data: {
    dashArray: '',
    radius: 0,
    circumference: 0
  },
  observers: {
    'percent,size,strokeWidth': function(percent, size, strokeWidth) {
      const radius = (size - strokeWidth) / 2
      const circumference = 2 * Math.PI * radius
      const offset = circumference * (1 - percent / 100)
      this.setData({
        radius,
        circumference,
        dashOffset: offset
      })
    }
  }
})
