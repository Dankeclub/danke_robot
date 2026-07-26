<template>
  <div class="login">
    <!-- Status bar -->
    <div class="status-bar">
      <span>蛋仔机器人</span>
      <span>🔒 家长登录</span>
    </div>

    <!-- Card -->
    <div class="login__card card-sketch">
      <!-- Tape decoration -->
      <svg class="doodle-tape" viewBox="0 0 40 18" width="40" height="18"
           style="top: -8px; left: 50%; transform: translateX(-50%) rotate(-6deg);">
        <rect x="2" y="0" width="36" height="18" rx="3" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="1.5" opacity="0.7"/>
      </svg>

      <h2 class="login__title">家长登录</h2>
      <p class="login__desc">输入绑定手机号激活设备</p>

      <!-- Phone display -->
      <div class="login__phone-display">
        <span class="login__phone-text">{{ phoneNumber || '请输入手机号' }}</span>
        <span class="login__cursor" v-if="phoneNumber.length < 11">|</span>
      </div>

      <!-- Error message -->
      <div class="login__error" v-if="errorMsg">{{ errorMsg }}</div>

      <!-- Number keypad -->
      <div class="login__keypad">
        <button class="login__key" v-for="n in 9" :key="n" @click="addDigit(n)">{{ n }}</button>
        <button class="login__key login__key--empty" disabled></button>
        <button class="login__key" @click="addDigit(0)">0</button>
        <button class="login__key login__key--del" @click="removeDigit">
          <i class="ri-delete-back-line"></i>
        </button>
      </div>

      <!-- Submit -->
      <button
        class="btn-sketch btn-sketch--primary login__submit"
        :disabled="phoneNumber.length < 11 || loading"
        @click="submitLogin"
      >
        {{ loading ? '绑定中...' : '开始使用 →' }}
      </button>
    </div>

    <!-- Doodle decorations -->
    <svg class="doodle-star login__star" viewBox="0 0 30 30" width="20" height="20">
      <path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z"
            fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/>
    </svg>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login, saveToken } from '../utils/api.js'

const router = useRouter()
const phoneNumber = ref('')
const loading = ref(false)
const errorMsg = ref('')

function addDigit(n) {
  if (phoneNumber.value.length < 11) {
    phoneNumber.value += String(n)
    errorMsg.value = ''
  }
}

function removeDigit() {
  phoneNumber.value = phoneNumber.value.slice(0, -1)
  errorMsg.value = ''
}

async function submitLogin() {
  if (phoneNumber.value.length < 11) return

  // Format to E.164: assume Chinese number, prepend +86
  const rawPhone = phoneNumber.value
  const e164Phone = rawPhone.startsWith('+86')
    ? rawPhone
    : `+86${rawPhone}`

  loading.value = true
  errorMsg.value = ''

  try {
    const result = await login(e164Phone)
    saveToken(result.access_token, result.refresh_token)
    router.push('/')
  } catch (err) {
    if (err.message === 'phone_not_bound') {
      errorMsg.value = '该手机号未绑定，请先在家长小程序中注册'
    } else if (err.message === 'rate_limit_exceeded') {
      errorMsg.value = '操作太频繁，请稍后再试'
    } else {
      errorMsg.value = '网络出小差了，请检查连接后重试'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login {
  width: var(--screen-w);
  height: var(--screen-h);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  background: var(--bg-sky);
}

.login__card {
  width: 420px;
  padding: var(--space-8) var(--space-8) var(--space-6);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  position: relative;
  z-index: var(--z-card);
}

.login__title {
  font-family: var(--font-heading);
  font-size: var(--text-2xl);
  color: var(--ink-black);
  font-weight: 400;
}

.login__desc {
  font-family: var(--font-body);
  font-size: var(--text-sm);
  color: var(--ink-muted);
}

.login__phone-display {
  width: 100%;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: var(--border-w) solid var(--ink-black);
  border-radius: 14px 18px 14px 16px;
  background: var(--bg-cream);
  box-shadow: 2px 2px 0 var(--ink-black);
}

.login__phone-text {
  font-family: var(--font-heading);
  font-size: var(--text-xl);
  color: var(--ink-black);
  letter-spacing: 3px;
}

.login__cursor {
  font-size: var(--text-xl);
  color: var(--brand-coral);
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.login__error {
  font-family: var(--font-body);
  font-size: var(--text-sm);
  color: var(--marker-red);
  text-align: center;
  min-height: 20px;
}

.login__keypad {
  display: grid;
  grid-template-columns: repeat(3, 80px);
  gap: var(--space-3);
  justify-content: center;
  padding-top: var(--space-2);
}

.login__key {
  width: 80px;
  height: var(--touch-btn);
  border: var(--border-w) solid var(--ink-black);
  border-radius: 16px 20px 14px 18px;
  background: var(--bg-card);
  font-family: var(--font-heading);
  font-size: var(--text-xl);
  color: var(--ink-black);
  cursor: pointer;
  box-shadow: 3px 3px 0 var(--ink-black);
  transition: transform var(--dur-fast) var(--ease-bounce);
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.login__key:active {
  transform: scale(0.9) translate(2px, 2px);
  box-shadow: 1px 1px 0 var(--ink-black);
}

.login__key--empty {
  visibility: hidden;
}

.login__key--del {
  font-size: var(--text-lg);
  background: var(--bg-mint);
}

.login__submit {
  width: 100%;
  margin-top: var(--space-2);
}

.login__submit:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.login__star {
  position: absolute;
  top: 30px;
  right: 60px;
  z-index: var(--z-base);
}
</style>
