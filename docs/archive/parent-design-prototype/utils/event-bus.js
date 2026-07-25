class EventBus {
  constructor() {
    this._events = {}
  }

  on(event, fn) {
    (this._events[event] || (this._events[event] = [])).push(fn)
  }

  off(event, fn) {
    const fns = this._events[event]
    if (fns) this._events[event] = fns.filter(f => f !== fn)
  }

  emit(event, ...args) {
    (this._events[event] || []).forEach(fn => fn(...args))
  }
}

module.exports = new EventBus()
