<template>
  <div class="page">
    <StatusBar />
    <div class="nav-row">
      <button class="nav-back" @click="router.back()">←</button>
      <span class="nav-title">数学妙算</span>
      <span class="nav-progress">{{ idx + 1 }}/{{ questions.length }}</span>
      <div class="nav-arrows">
        <button class="nav-btn" :disabled="idx === 0" @click="idx--">◀</button>
        <button class="nav-btn" :disabled="idx === questions.length - 1" @click="idx++">▶</button>
      </div>
      <button class="nav-home" @click="router.push('/')">首页</button>
    </div>

    <div class="content scroll-y">
      <svg class="scene-bg" viewBox="0 0 1024 500" width="1024" height="500" preserveAspectRatio="none">
        <rect x="80" y="390" width="14" height="70" rx="3" fill="#C0A070" stroke="#2D2D2D" stroke-width="2"/>
        <circle cx="87" cy="370" r="28" fill="#AACE7B" stroke="#2D2D2D" stroke-width="2"/><text x="87" y="378" font-size="18" font-family="ZCOOL KuaiLe" text-anchor="middle">1</text>
        <rect x="420" y="395" width="12" height="60" rx="3" fill="#C0A070" stroke="#2D2D2D" stroke-width="2"/>
        <circle cx="426" cy="380" r="24" fill="#8BC34A" stroke="#2D2D2D" stroke-width="2"/><text x="426" y="387" font-size="16" font-family="ZCOOL KuaiLe" text-anchor="middle">5</text>
        <rect x="850" y="380" width="16" height="80" rx="3" fill="#C0A070" stroke="#2D2D2D" stroke-width="2"/>
        <circle cx="858" cy="360" r="32" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2"/><text x="858" y="370" font-size="20" font-family="ZCOOL KuaiLe" text-anchor="middle">+</text>
        <path d="M0 450 Q200 400 400 440 Q600 470 800 430 Q950 405 1024 440 L1024 500 L0 500Z" fill="#AACE7B" stroke="#2D2D2D" stroke-width="1.5" opacity="0.3"/>
        <polygon points="600,50 603,58 612,60 605,65 607,73 600,68 593,73 595,65 588,60 597,58" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="1.5" stroke-linejoin="round"/>
        <rect x="200" y="430" width="26" height="26" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="2" transform="rotate(10 213 443)"/>
        <polygon points="680,430 698,456 662,456" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2"/>
      </svg>

      <div class="pb-card card-sketch">
        <div class="card-illust">
          <svg viewBox="0 0 280 130" width="260" height="120">
            <template v-if="idx === 0">
              <rect x="25" y="40" width="42" height="36" rx="4" fill="#FFB5A0" stroke="#2D2D2D" stroke-width="2.5"/>
              <rect x="30" y="45" width="10" height="10" rx="1.5" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="1.2"/>
              <rect x="43" y="45" width="10" height="10" rx="1.5" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="1.2"/>
              <rect x="30" y="60" width="10" height="10" rx="1.5" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="1.2"/>
              <text x="68" y="63" font-size="24" font-family="ZCOOL KuaiLe">- 3</text>
              <rect x="115" y="40" width="42" height="36" rx="4" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2.5"/>
              <rect x="120" y="45" width="10" height="10" rx="1.5" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="1.2"/>
              <rect x="133" y="60" width="10" height="10" rx="1.5" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="1.2"/>
              <text x="160" y="63" font-size="24" font-family="ZCOOL KuaiLe">+ 5</text>
              <text x="100" y="108" font-size="16" font-family="ZCOOL KuaiLe" text-anchor="middle">= ? 颗糖</text>
            </template>
            <template v-else-if="idx === 1">
              <rect x="35" y="45" width="90" height="50" rx="3" fill="#AACE7B" stroke="#2D2D2D" stroke-width="2.5"/>
              <text x="80" y="76" font-size="13" font-family="ZCOOL KuaiLe" text-anchor="middle">8 cm</text>
              <line x1="35" y1="112" x2="140" y2="112" stroke="#2D2D2D" stroke-width="2"/><text x="80" y="128" font-size="13" font-family="ZCOOL KuaiLe" text-anchor="middle">5 cm</text>
              <text x="190" y="80" font-size="16" font-family="ZCOOL KuaiLe">面积 = ?</text>
            </template>
            <template v-else-if="idx === 2">
              <rect x="25" y="32" width="36" height="22" rx="3" fill="#C0E3F5" stroke="#2D2D2D" stroke-width="2"/><text x="43" y="47" font-size="12" font-family="ZCOOL KuaiLe" text-anchor="middle">书 9</text>
              <rect x="25" y="64" width="36" height="20" rx="3" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2"/><text x="43" y="78" font-size="12" font-family="ZCOOL KuaiLe" text-anchor="middle">笔 6</text>
              <text x="100" y="55" font-size="16" font-family="ZCOOL KuaiLe">25元</text>
              <text x="110" y="90" font-size="26" font-family="ZCOOL KuaiLe">- ?</text>
            </template>
            <template v-else>
              <rect x="55" y="25" width="58" height="44" rx="4" fill="#C0A070" stroke="#2D2D2D" stroke-width="2.5"/>
              <rect x="60" y="30" width="10" height="10" rx="1.5" fill="#F5DEB3" stroke="#2D2D2D" stroke-width="1"/><rect x="73" y="30" width="10" height="10" rx="1.5" fill="#F5DEB3" stroke="#2D2D2D" stroke-width="1"/><rect x="86" y="30" width="10" height="10" rx="1.5" fill="#F5DEB3" stroke="#2D2D2D" stroke-width="1"/>
              <rect x="60" y="43" width="10" height="10" rx="1.5" fill="#F5DEB3" stroke="#2D2D2D" stroke-width="1"/><rect x="73" y="43" width="10" height="10" rx="1.5" fill="#F5DEB3" stroke="#2D2D2D" stroke-width="1"/><rect x="86" y="43" width="10" height="10" rx="1.5" fill="#F5DEB3" stroke="#2D2D2D" stroke-width="1"/>
              <text x="185" y="38" font-size="15" font-family="ZCOOL KuaiLe">24颗</text>
              <text x="185" y="60" font-size="15" font-family="ZCOOL KuaiLe">÷ 6人</text>
              <text x="140" y="100" font-size="26" font-family="ZCOOL KuaiLe">= ? 颗/人</text>
            </template>
          </svg>
        </div>
        <div class="card-tag">第 {{ idx + 1 }} 题 · 数学</div>
        <div class="card-q">{{ questions[idx].q }}</div>
        <div class="card-opts">
          <button v-for="(o, i) in questions[idx].options" :key="i" class="opt-btn btn-sketch" @click="pick(i)" :class="{ 'opt-correct': picked === i && i === questions[idx].answer, 'opt-wrong': picked === i && i !== questions[idx].answer }">{{ o }}</button>
        </div>
        <div class="card-meta">
          <span class="meta-stars">
            <svg v-for="n in 3" :key="n" viewBox="0 0 30 30" width="18" height="18"><path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z" :fill="n <= (idx + 1) ? '#FFB300' : '#DDD'" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/></svg>
          </span>
          <span class="meta-label">{{ idx + 1 }}/{{ questions.length }} 题</span>
        </div>
      </div>
    </div>

    <DankePet scene="math" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import StatusBar from '../components/StatusBar.vue'
import DankePet from '../components/DankePet.vue'

const router = useRouter()
const idx = ref(0)
const picked = ref(null)
const questions = [
  { q: '小明有12颗糖，吃了3颗，又买了5颗，现在有几颗？', options: ['10颗', '14颗', '15颗', '17颗'], answer: 1 },
  { q: '一个长方形长8厘米，宽5厘米，它的面积是多少？', options: ['26平方厘米', '40平方厘米', '13平方厘米', '30平方厘米'], answer: 1 },
  { q: '小红有25元，买了一本书花了9元，又买了一支笔花了6元，还剩多少钱？', options: ['10元', '9元', '11元', '16元'], answer: 0 },
  { q: '一盒巧克力有24颗，平均分给6个小朋友，每人几颗？', options: ['4颗', '6颗', '3颗', '5颗'], answer: 0 },
]
function pick(i) {
  if (picked.value !== null) return
  picked.value = i
  setTimeout(() => {
    if (idx.value < questions.length - 1) { idx.value++; picked.value = null }
  }, 1500)
}
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

.pb-card { width: 520px; min-height: 370px; padding: var(--space-3) var(--space-6); display: flex; flex-direction: column; align-items: center; gap: var(--space-1); background: var(--bg-card); position: relative; z-index: 2; margin-top: var(--space-1); }
.card-illust { min-height: 120px; display: flex; align-items: center; justify-content: center; margin-bottom: 2px; }
.card-tag { font-family: var(--font-heading); font-size: var(--text-sm); color: #3B7F8F; background: #CCE7E3; padding: 3px 12px; border-radius: 10px; border: 2px solid var(--ink-black); }
.card-q { font-family: var(--font-heading); font-size: 22px; text-align: center; line-height: 1.4; margin-top: 1px; min-height: 56px; }
.card-opts { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2); width: 100%; margin-top: 2px; }
.opt-btn { font-family: var(--font-heading); font-size: var(--text-lg); height: 48px; }
.opt-correct { background: #AACE7B; color: #fff; border-color: #6B9B37; }
.opt-wrong { background: #FFB5B5; color: #fff; }
.card-meta { display: flex; align-items: center; gap: var(--space-2); margin-top: 2px; }
.meta-stars { display: flex; gap: 1px; }
.meta-label { font-family: var(--font-body); font-size: 14px; color: var(--ink-muted); }
</style>
