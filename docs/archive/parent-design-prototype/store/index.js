const eventBus = require('../utils/event-bus')

const store = {
  state: {
    userInfo: null,
    childInfo: null,
    deviceInfo: null,
    deviceOnline: true,
    unreadCount: 3
  },

  setState(key, value) {
    this.state[key] = value
    eventBus.emit(`store:${key}`, value)
  },

  getState(key) {
    return this.state[key]
  },

  subscribe(key, fn) {
    eventBus.on(`store:${key}`, fn)
    return () => eventBus.off(`store:${key}`, fn)
  }
}

module.exports = store
