Component({
  properties: {
    count: { type: Number, value: 0 }
  },
  data: {
    display: ''
  },
  observers: {
    'count': function(val) {
      this.setData({ display: val > 99 ? '99+' : String(val) })
    }
  }
})
