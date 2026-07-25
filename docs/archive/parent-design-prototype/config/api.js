const env = require('./env')

const API_BASE_MAP = {
  development: 'http://localhost:3000/api',
  staging: 'https://staging-api.example.com/api',
  production: 'https://api.example.com/api'
}

module.exports = {
  API_BASE_URL: API_BASE_MAP[env.ENV]
}
