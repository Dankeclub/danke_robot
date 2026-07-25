<template>
  <div class="page">
    <StatusBar />
    <div class="page__header"><BackButton /><span class="page__title">跟蛋仔聊天</span></div>

    <!-- decorations -->
    <svg class="cloud c1" viewBox="0 0 100 50" width="42" height="21"><path d="M18 40 Q12 28 20 22 Q16 8 32 12 Q38 -2 52 10 Q62 -2 72 14 Q88 8 86 24 Q96 28 86 40 Q76 44 58 42Z" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="2" opacity="0.45"/></svg>
    <svg class="doodle-star s1" viewBox="0 0 30 30" width="14" height="14"><path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/></svg>
    <svg class="chat-doodle" viewBox="0 0 40 36" width="22" height="20"><path d="M4 4 H28 Q32 4 32 8 V20 Q32 24 28 24 H16 L10 32 L12 24 H4 Q0 24 0 20 V8 Q0 4 4 4Z" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="2.5"/></svg>

    <div class="chat-area scroll-y">
      <div v-for="(m, i) in messages" :key="i" class="chat-row" :class="m.role === 'pet' ? 'chat-row--pet' : 'chat-row--child'">
        <div v-if="m.role === 'pet'" class="chat-avatar">
          <svg viewBox="0 0 36 36" width="34" height="34"><ellipse cx="18" cy="20" rx="14" ry="16" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="2.5"/><circle cx="12" cy="16" r="2" fill="#2D2D2D"/><circle cx="24" cy="16" r="2" fill="#2D2D2D"/><path d="M12 25 Q18 30 24 25" fill="none" stroke="#2D2D2D" stroke-width="2" stroke-linecap="round"/></svg>
        </div>
        <div class="chat-bubble" :class="m.role === 'pet' ? 'bubble--pet' : 'bubble--child'">{{ m.text }}</div>
      </div>
    </div>
    <div class="quick-prompts">
      <span v-for="p in prompts" :key="p" class="quick-prompt" @click="send(p)">{{ p }}</span>
    </div>
    <div class="chat-bar">
      <input class="chat-input" placeholder="想说什么就说吧..." type="text" v-model="inputText" @keyup.enter="send">
      <button class="voice-btn" :class="{ 'voice-btn--recording': isRecording }" @click="toggleVoice" :title="isRecording ? '点击停止' : '按住说话'">
        <i :class="isRecording ? 'ri-mic-fill' : 'ri-mic-line'"></i>
      </button>
      <button class="send-btn" @click="send"><i class="ri-send-plane-fill"></i></button>
    </div>

    <svg class="ground" viewBox="0 0 1024 50" width="1024" height="50" preserveAspectRatio="none"><path d="M0 28 Q100 12 200 24 Q300 36 400 16 Q500 4 600 22 Q700 34 800 14 Q900 4 1024 12 L1024 50 L0 50Z" fill="#AACE7B" stroke="#2D2D2D" stroke-width="2" opacity="0.25"/></svg>

    <DankePet scene="chat" />
  </div>
</template>

<script setup>
import { ref, nextTick, onUnmounted } from 'vue'
import StatusBar from '../components/StatusBar.vue'
import BackButton from '../components/BackButton.vue'
import DankePet from '../components/DankePet.vue'
import { startListening, stopListening, matchReply, speak, stopSpeaking } from '../utils/voice.js'

const inputText = ref('')
const messages = ref([
  { role: 'pet', text: '嗨！今天过得怎么样呀？有什么想跟我说的吗~' },
  { role: 'child', text: '今天数学考了95分！' },
  { role: 'pet', text: '哇！95分！太厉害了吧！你怎么做到的？嘿嘿，是不是偷偷努力了~' },
  { role: 'child', text: '就是每天做练习呀' },
  { role: 'pet', text: '果然！坚持就是最大的超能力。明天继续加油哦，我陪着你~' },
])
const prompts = ['给我讲个笑话', '今天天气怎么样', '我有点无聊', '推荐一本书']
const isRecording = ref(false)
const isPetSpeaking = ref(false)

function scrollToBottom() {
  nextTick(() => {
    const area = document.querySelector('.chat-area')
    if (area) area.scrollTop = area.scrollHeight
  })
}

function addPetReply(text) {
  messages.value.push({ role: 'pet', text })
  scrollToBottom()
  isPetSpeaking.value = true
  speak(text, {
    onEnd: () => { isPetSpeaking.value = false },
  })
}

function send(text) {
  const trimmed = (typeof text === 'string' ? text : inputText.value).trim()
  if (!trimmed) return

  messages.value.push({ role: 'child', text: trimmed })
  inputText.value = ''
  scrollToBottom()

  const reply = matchReply(trimmed)
  setTimeout(() => {
    addPetReply(reply)
  }, 500)
}

function toggleVoice() {
  if (isRecording.value) {
    stopListening()
    isRecording.value = false
    if (inputText.value.trim()) {
      send(inputText.value)
    }
    return
  }
  const ok = startListening({
    onResult: (text) => {
      inputText.value = text
    },
    onEnd: () => {
      isRecording.value = false
      if (inputText.value.trim()) {
        send(inputText.value)
      }
    },
    onError: () => {
      isRecording.value = false
    },
  })
  if (!ok) {
    alert('当前浏览器不支持语音识别，请在 Chrome 或 Edge 中打开')
    return
  }
  isRecording.value = true
  inputText.value = ''
}

onUnmounted(() => {
  stopListening()
  stopSpeaking()
})
</script>

<style scoped>
.page { width: 100%; height: 100%; display: flex; flex-direction: column; position: relative; overflow: hidden; background: var(--bg-sky); }
.page__header { height: 50px; display: flex; align-items: center; padding: 0 var(--space-5); gap: var(--space-3); position: relative; z-index: 5; }
.page__title { font-family: var(--font-heading); font-size: 26px; color: #3B82C6; }
.chat-area { flex: 1; padding: var(--space-3) var(--space-6); display: flex; flex-direction: column; gap: var(--space-3); overflow-y: auto; min-height: 0; position: relative; z-index: 5; }
.chat-row { display: flex; align-items: flex-end; gap: var(--space-2); }
.chat-row--pet { justify-content: flex-start; }
.chat-row--child { justify-content: flex-end; }
.chat-avatar { width: 38px; height: 38px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.chat-bubble { max-width: 62%; padding: var(--space-3) var(--space-4); font-family: var(--font-body); font-size: 16px; line-height: 1.5; }
.bubble--pet { background: var(--bg-card); border: 2.5px solid var(--ink-black); border-radius: 18px 18px 18px 6px; box-shadow: 2px 2px 0 var(--ink-black); animation: popIn 0.25s ease-out; }
.bubble--child { background: #C0E3F5; color: var(--ink-black); border: 2.5px solid var(--ink-black); border-radius: 18px 18px 6px 18px; box-shadow: 2px 2px 0 var(--ink-black); animation: popIn 0.25s ease-out; }
@keyframes popIn { 0% { transform: scale(0.85); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
.quick-prompts { display: flex; gap: var(--space-2); padding: var(--space-2) var(--space-5); overflow-x: auto; flex-shrink: 0; position: relative; z-index: 5; }
.quick-prompt { flex-shrink: 0; padding: 8px 18px; border: 2px solid var(--ink-black); border-radius: 16px; background: var(--bg-card); font-family: var(--font-body); font-size: 15px; cursor: pointer; box-shadow: 1.5px 1.5px 0 var(--ink-black); transition: 0.12s; }
.quick-prompt:active { transform: scale(0.93); }
.chat-bar { height: 58px; display: flex; align-items: center; padding: 0 var(--space-5); gap: var(--space-3); border-top: 2px dashed var(--ink-muted); flex-shrink: 0; position: relative; z-index: 5; }
.chat-input { flex: 1; height: 44px; padding: 0 var(--space-4); border: 2.5px solid var(--ink-black); border-radius: 20px; background: var(--bg-card); font-family: var(--font-body); font-size: 16px; outline: none; }
.send-btn { width: 44px; height: 44px; border: 2.5px solid var(--ink-black); border-radius: 50%; background: #3B82C6; color: #fff; font-size: 20px; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 2px 2px 0 var(--ink-black); transition: 0.12s; }
.send-btn:active { transform: scale(0.88); }

.voice-btn { width: 44px; height: 44px; border: 2.5px solid var(--ink-black); border-radius: 50%; background: var(--bg-card); color: #3B82C6; font-size: 20px; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 2px 2px 0 var(--ink-black); transition: 0.12s; flex-shrink: 0; }
.voice-btn:active { transform: scale(0.88); }
.voice-btn--recording { background: #EF4444; color: #fff; animation: pulse-record 0.8s ease-in-out infinite; }
@keyframes pulse-record { 0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.5); } 50% { box-shadow: 0 0 0 10px rgba(239,68,68,0); } }

.doodle-star { position: absolute; z-index: 1; }
.s1 { top: 10px; right: 40px; transform: rotate(10deg); }
.cloud { position: absolute; z-index: 1; }
.c1 { top: 6px; left: 200px; }
.chat-doodle { position: absolute; bottom: 50px; right: 80px; z-index: 1; transform: rotate(-8deg); }
.ground { position: absolute; bottom: 0; left: 0; z-index: 2; }
</style>
