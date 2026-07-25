function delay(ms = 300) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

module.exports = {
  async get(url, data) {
    await delay()
    return { code: 0, data: null, msg: 'ok' }
  },
  async post(url, data) {
    await delay()
    return { code: 0, data: null, msg: 'ok' }
  },
  async put(url, data) {
    await delay()
    return { code: 0, data: null, msg: 'ok' }
  },
  async del(url, data) {
    await delay()
    return { code: 0, data: null, msg: 'ok' }
  }
}
