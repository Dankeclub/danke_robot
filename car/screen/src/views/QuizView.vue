<template>
  <div class="page">
    <StatusBar />
    <div class="nav-row">
      <button class="nav-back" @click="router.back()">←</button>
      <span class="nav-title">益智问答</span>
      <span class="nav-progress">{{ Math.min(qIdx + 1, questions.length) }}/{{ questions.length }}</span>
      <div class="nav-arrows">
        <button class="nav-btn" :disabled="qIdx === 0 || done" @click="navPrev">◀</button>
        <button class="nav-btn" :disabled="qIdx >= questions.length - 1 || done" @click="navNext">▶</button>
      </div>
      <button class="nav-home" @click="router.push('/')">首页</button>
    </div>

    <div class="content scroll-y">
      <svg class="scene-bg" viewBox="0 0 1024 500" width="1024" height="500" preserveAspectRatio="none">
        <rect x="100" y="410" width="52" height="34" rx="3" fill="#C0A070" stroke="#2D2D2D" stroke-width="2"/><path d="M100 410 L126 392 L152 410" fill="#AACE7B" stroke="#2D2D2D" stroke-width="2"/>
        <rect x="700" y="400" width="60" height="40" rx="3" fill="#C0A070" stroke="#2D2D2D" stroke-width="2"/><path d="M700 400 L730 380 L760 400" fill="#8BC34A" stroke="#2D2D2D" stroke-width="2"/>
        <rect x="480" y="385" width="8" height="50" rx="3" fill="#8B7E74" stroke="#2D2D2D" stroke-width="1.5"/><circle cx="484" cy="370" r="22" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="2"/><text x="484" y="377" font-size="20" font-family="ZCOOL KuaiLe" text-anchor="middle">?</text>
        <path d="M0 450 Q200 400 400 440 Q600 470 800 430 Q950 405 1024 440 L1024 500 L0 500Z" fill="#AACE7B" stroke="#2D2D2D" stroke-width="1.5" opacity="0.3"/>
        <polygon points="200,50 203,58 212,60 205,65 207,73 200,68 193,73 195,65 188,60 197,58" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="1.5" stroke-linejoin="round"/>
      </svg>

      <div v-if="!done" class="pb-card card-sketch">
        <div class="card-illust">
          <svg viewBox="0 0 200 120" width="180" height="108">
            <template v-if="qIdx === 0">
              <ellipse cx="80" cy="65" rx="32" ry="28" fill="#C0E3F5" stroke="#2D2D2D" stroke-width="2.5"/><ellipse cx="95" cy="85" rx="14" ry="6" fill="#C0E3F5" stroke="#2D2D2D" stroke-width="1.5"/>
            </template>
            <template v-else-if="qIdx === 1">
              <circle cx="100" cy="55" r="26" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2.5"/>
              <line x1="100" y1="17" x2="100" y2="6"/><line x1="58" y1="55" x2="47" y2="55"/><line x1="142" y1="55" x2="153" y2="55"/>
              <rect x="45" y="88" width="50" height="17" rx="2" fill="#AACE7B" stroke="#2D2D2D" stroke-width="1.5"/><text x="70" y="100" font-size="10" font-family="ZCOOL KuaiLe" text-anchor="middle">东</text>
            </template>
            <template v-else-if="qIdx === 2">
              <circle cx="100" cy="65" r="32" fill="#FFF" stroke="#2D2D2D" stroke-width="2.5"/>
              <text x="100" y="50" font-size="13" font-family="ZCOOL KuaiLe" text-anchor="middle">1月2月</text><text x="100" y="75" font-size="13" font-family="ZCOOL KuaiLe" text-anchor="middle">···12月</text>
            </template>
            <template v-else>
              <path d="M40 65 L75 35 L110 95 L150 55" fill="none" stroke="#C0E3F5" stroke-width="3.5"/>
              <circle cx="75" cy="35" r="8" fill="#FFB5A0" stroke="#2D2D2D" stroke-width="1.5"/>
              <circle cx="150" cy="55" r="10" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="1.5"/>
            </template>
          </svg>
        </div>
        <span class="card-tag">第 {{ qIdx + 1 }} / {{ questions.length }} 题</span>
        <div class="card-q">{{ questions[qIdx].q }}</div>
        <div class="card-opts">
          <button v-for="(o, i) in questions[qIdx].options" :key="i" class="opt-btn btn-sketch" :class="ansClass(i)" @click="pick(i)">{{ o }}</button>
        </div>
        <div v-if="answered !== null" class="card-feedback" :class="answered === questions[qIdx].answer ? 'fb-correct' : 'fb-wrong'">
          {{ answered === questions[qIdx].answer ? '答对啦！' : '差一点点~' }}
        </div>
        <div class="card-meta">
          <span class="meta-dots">
            <span v-for="n in questions.length" :key="n" class="dot" :class="{ done: n <= qIdx }"></span>
          </span>
          <span class="meta-label">已答 {{ score }} / {{ qIdx + 1 }}</span>
        </div>
      </div>

      <div v-else class="pb-card card-sketch card-done">
        <svg viewBox="0 0 70 70" width="60" height="60"><circle cx="35" cy="35" r="30" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2.5"/><circle cx="28" cy="30" r="2.5" fill="#2D2D2D"/><circle cx="42" cy="30" r="2.5" fill="#2D2D2D"/><path d="M22 46 Q35 55 48 46" fill="none" stroke="#2D2D2D" stroke-width="2.5" stroke-linecap="round"/></svg>
        <h2 class="done-title">全部完成！</h2>
        <p class="done-sub">共答对 {{ score }} 题</p>
        <button class="btn-sketch btn-sketch--primary" @click="reset">再来一次</button>
      </div>
    </div>

    <DankePet scene="quiz" />
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import StatusBar from '../components/StatusBar.vue'
import DankePet from '../components/DankePet.vue'

const router = useRouter()
const qIdx = ref(0)
const answered = ref(null)
const score = ref(0)
const done = ref(false)
const questions = reactive([
  { q: '世界上最大的哺乳动物是什么？', options: ['大象', '蓝鲸', '长颈鹿', '河马'], answer: 1 },
  { q: '太阳从哪个方向升起？', options: ['东边', '西边', '南边', '北边'], answer: 0 },
  { q: '一年有多少个月？', options: ['10个月', '11个月', '12个月', '13个月'], answer: 2 },
  { q: '中国的首都是哪个城市？', options: ['上海', '广州', '北京', '深圳'], answer: 2 },
])
function pick(i) {
  if (answered.value !== null) return
  answered.value = i
  if (i === questions[qIdx.value].answer) score.value++
  setTimeout(() => {
    if (qIdx.value < questions.length - 1) { qIdx.value++; answered.value = null }
    else { done.value = true }
  }, 1500)
}
function ansClass(i) {
  if (answered.value === null) return ''
  if (i === questions[qIdx.value].answer) return 'opt-correct'
  if (i === answered.value) return 'opt-wrong'
  return ''
}
function navPrev() { if (!done.value) qIdx.value = Math.max(0, qIdx.value - 1) }
function navNext() { if (!done.value) qIdx.value = Math.min(questions.length - 1, qIdx.value + 1) }
function reset() { qIdx.value = 0; answered.value = null; score.value = 0; done.value = false }
</script>

<style scoped>
.page { width: 100%; height: 100%; display: flex; flex-direction: column; position: relative; overflow: hidden; background: var(--bg-mint); }
.nav-row { height: 48px; display: flex; align-items: center; padding: 0 var(--space-2); gap: 6px; flex-shrink: 0; position: relative; z-index: 10; }
.nav-back { width: 38px; height: 38px; border: 2.5px solid var(--ink-black); border-radius: 10px 12px 9px 11px; background: var(--bg-card); font-family: var(--font-heading); font-size: 17px; cursor: pointer; box-shadow: 2px 2px 0 var(--ink-black); display: flex; align-items: center; justify-content: center; transition: 0.12s; flex-shrink: 0; }
.nav-back:active { transform: scale(0.9); }
.nav-title { font-family: var(--font-heading); font-size: 22px; color: #3B7F8F; flex: 1; text-align: center; white-space: nowrap; min-width: 0; }
.nav-progress { font-family: var(--font-heading); font-size: 15px; color: var(--ink-muted); flex-shrink: 0; }
.nav-arrows { display: flex; gap: 4px; flex-shrink: 0; }
.nav-btn { width: 34px; height: 34px; border: 2.5px solid var(--ink-black); border-radius: 10px 12px 9px 11px; background: var(--bg-card); font-family: var(--font-heading); font-size: 16px; cursor: pointer; box-shadow: 2px 2px 0 var(--ink-black); display: flex; align-items: center; justify-content: center; transition: 0.12s; }
.nav-btn:active { transform: scale(0.9); }
.nav-btn:disabled { opacity: 0.3; cursor: default; }
.nav-home { height: 34px; padding: 0 var(--space-3); border: 2.5px solid var(--ink-black); border-radius: 12px 14px 10px 13px; background: var(--bg-card); font-family: var(--font-heading); font-size: 14px; cursor: pointer; box-shadow: 2px 2px 0 var(--ink-black); transition: 0.12s; white-space: nowrap; flex-shrink: 0; }
.nav-home:active { transform: scale(0.92); }

.content { flex: 1; display: flex; flex-direction: column; align-items: center; padding: var(--space-2) var(--space-6) var(--space-3); position: relative; z-index: 5; }
.scene-bg { position: absolute; bottom: 0; left: 0; z-index: 0; pointer-events: none; }

.pb-card { width: 520px; padding: var(--space-3) var(--space-5); display: flex; flex-direction: column; align-items: center; gap: var(--space-1); background: var(--bg-card); position: relative; z-index: 2; margin-top: var(--space-1); }
.card-illust { margin-bottom: 2px; }
.card-tag { font-family: var(--font-heading); font-size: var(--text-sm); color: #D97706; background: #FFF7ED; padding: 3px 12px; border-radius: 10px; border: 2px solid #D97706; }
.card-q { font-family: var(--font-heading); font-size: 24px; text-align: center; line-height: 1.4; max-width: 460px; }
.card-opts { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2); width: 100%; margin-top: 2px; }
.opt-btn { font-family: var(--font-heading); font-size: var(--text-lg); height: 48px; transition: 0.15s; }
.opt-correct { background: #AACE7B; color: #fff; border-color: #6B9B37; }
.opt-wrong { background: #FFB5B5; color: #fff; }
.card-feedback { font-family: var(--font-heading); font-size: var(--text-xl); animation: popIn 0.3s ease-out; }
.fb-correct { color: #4B7A1F; } .fb-wrong { color: #E8826B; }
@keyframes popIn { 0% { transform: scale(0.5); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
.card-meta { display: flex; align-items: center; gap: var(--space-2); margin-top: 2px; }
.meta-dots { display: flex; gap: 4px; }
.dot { width: 9px; height: 9px; border-radius: 50%; border: 2px solid #DDD; }
.dot.done { background: #AACE7B; border-color: #6B9B37; }
.meta-label { font-family: var(--font-body); font-size: 14px; color: var(--ink-muted); }

.card-done { width: 380px; padding: var(--space-6); display: flex; flex-direction: column; align-items: center; gap: var(--space-3); }
.done-title { font-family: var(--font-heading); font-size: 26px; }
.done-sub { font-family: var(--font-body); font-size: var(--text-lg); color: var(--ink-muted); }
</style>
