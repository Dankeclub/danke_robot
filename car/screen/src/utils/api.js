/**
 * Network layer for car screen.
 *
 * - Wraps fetch() with automatic Bearer token injection
 * - Auto-refreshes on 401 using refresh_token
 * - Exports login() for phone authentication
 */

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

// ── Token storage ────────────────────────────────────────

export function getToken() {
  return localStorage.getItem('access_token')
}

export function getRefreshToken() {
  return localStorage.getItem('refresh_token')
}

export function saveToken(accessToken, refreshToken) {
  localStorage.setItem('access_token', accessToken)
  localStorage.setItem('refresh_token', refreshToken)
}

export function clearToken() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

// ── API helpers ──────────────────────────────────────────

async function refreshAccessToken() {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    clearToken()
    throw new Error('no_refresh_token')
  }

  const res = await fetch(`${API_BASE}/v1/api/car/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })

  if (!res.ok) {
    clearToken()
    throw new Error('refresh_failed')
  }

  const body = await res.json()
  saveToken(body.data.access_token, body.data.refresh_token)
  return body.data.access_token
}

/**
 * Authenticated fetch wrapper.
 *
 * Automatically injects Authorization header. On 401, attempts a
 * one-time token refresh and retries. If refresh fails, clears
 * token and redirects to login.
 */
export async function apiFetch(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  let res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  // Auto-refresh on 401
  if (res.status === 401 && token) {
    try {
      const newToken = await refreshAccessToken()
      headers['Authorization'] = `Bearer ${newToken}`
      res = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers,
      })
    } catch {
      clearToken()
      window.location.hash = '#/login'
      throw new Error('auth_lost')
    }
  }

  return res
}

// ── Auth API ─────────────────────────────────────────────

/**
 * Login with phone number.
 *
 * @param {string} phone - E.164 formatted phone number
 * @returns {Promise<object>} { access_token, refresh_token, expires_in, child_profile }
 */
export async function login(phone) {
  // Simple device ID: use a stored ID or generate one
  let deviceId = localStorage.getItem('device_id')
  if (!deviceId) {
    deviceId = 'car-' + crypto.randomUUID()
    localStorage.setItem('device_id', deviceId)
  }

  const res = await fetch(`${API_BASE}/v1/api/car/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      phone,
      device_id: deviceId,
      device_name: '蛋仔机器人',
      device_type: 'car',
    }),
  })

  const body = await res.json()

  if (!res.ok || body.code !== 0) {
    throw new Error(body.msg || 'login_failed')
  }

  return body.data
}
