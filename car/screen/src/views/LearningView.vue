<template>
  <div class="page">
    <StatusBar />
    <div class="page__header"><BackButton /><span class="page__title">学习乐园</span></div>

    <!-- Sky decorations -->
    <svg class="cloud c1" viewBox="0 0 100 50" width="50" height="25"><path d="M18 40 Q12 28 20 22 Q16 8 32 12 Q38 -2 52 10 Q62 -2 72 14 Q88 8 86 24 Q96 28 86 40 Q76 44 58 42Z" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="2" opacity="0.5"/></svg>
    <svg class="doodle-star s1" viewBox="0 0 30 30" width="18" height="18"><path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/></svg>
    <svg class="doodle-star s2" viewBox="0 0 30 30" width="14" height="14"><path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/></svg>

    <div class="module-grid scroll-y">
      <div v-for="m in modules" :key="m.label" class="module-card card-sketch" @click="$router.push(m.route)">
        <div class="module-icon" :style="{ background: m.bg, color: m.color }"><i :class="m.icon"></i></div>
        <span class="module-label">{{ m.label }}</span>
        <span class="module-desc">{{ m.desc }}</span>
      </div>
    </div>

    <!-- Bottom decorations -->
    <svg class="ground" viewBox="0 0 1024 80" width="1024" height="80" preserveAspectRatio="none"><path d="M0 50 Q80 20 160 40 Q240 55 320 30 Q400 10 480 40 Q560 55 640 28 Q720 5 800 35 Q880 50 960 22 Q1000 10 1024 20 L1024 80 L0 80Z" fill="#AACE7B" stroke="#2D2D2D" stroke-width="2" opacity="0.4"/></svg>
    <svg class="flower f1" viewBox="0 0 20 20" width="16" height="16"><circle cx="10" cy="6" r="4.5" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2"/><circle cx="10" cy="14" r="2.5" fill="#AACE7B" stroke="#2D2D2D" stroke-width="1.5"/></svg>
    <svg class="flower f2" viewBox="0 0 20 20" width="13" height="13"><circle cx="10" cy="6" r="4.5" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="2"/><circle cx="10" cy="14" r="2.5" fill="#AACE7B" stroke="#2D2D2D" stroke-width="1.5"/></svg>

    <DankePet scene="learning" />
  </div>
</template>

<script setup>
import StatusBar from '../components/StatusBar.vue'
import BackButton from '../components/BackButton.vue'
import DankePet from '../components/DankePet.vue'
const modules = [
  { label: '科学探索', desc: '探索奇妙世界', icon: 'ri-flask-line', route: '/science', bg: '#CCE7E3', color: '#3B7F8F' },
  { label: '数学妙算', desc: '脑力大挑战', icon: 'ri-calculator-line', route: '/math', bg: '#FFEC8E', color: '#B8780A' },
  { label: '英语乐园', desc: '快乐学单词', icon: 'ri-english-input', route: '/english', bg: '#C0E3F5', color: '#2D6DA1' },
  { label: '诗词儿歌', desc: '经典诵读', icon: 'ri-book-2-line', route: '/poems', bg: '#FCF3B9', color: '#B8780A' },
  { label: '音乐律动', desc: '跟着节奏摇摆', icon: 'ri-music-2-line', route: '/music', bg: '#F5F3FF', color: '#6B5CE7' },
  { label: '益智问答', desc: '小脑筋转起来', icon: 'ri-question-answer-line', route: '/quiz', bg: '#FFF7ED', color: '#D97706' },
]
</script>

<style scoped>
.page { width: 100%; height: 100%; display: flex; flex-direction: column; position: relative; overflow: hidden; background: var(--bg-sky); }
.page__header { height: 50px; display: flex; align-items: center; padding: 0 var(--space-5); gap: var(--space-3); position: relative; z-index: 5; }
.page__title { font-family: var(--font-heading); font-size: 26px; color: var(--ink-black); }
.module-grid { flex: 1; display: grid; grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(2, 1fr); gap: var(--space-5); padding: var(--space-4) var(--space-12) var(--space-5); position: relative; z-index: 5; }
.module-card { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: var(--space-2); cursor: pointer; background: var(--bg-card); padding: var(--space-4); }
.module-icon { width: 72px; height: 72px; border: 2.5px solid var(--ink-black); border-radius: 18px 20px 16px 14px; display: flex; align-items: center; justify-content: center; font-size: 34px; box-shadow: 2px 2px 0 var(--ink-black); }
.module-label { font-family: var(--font-heading); font-size: var(--text-lg); margin-top: 4px; }
.module-desc { font-family: var(--font-body); font-size: var(--text-sm); color: var(--ink-muted); }

/* decorations */
.doodle-star { position: absolute; z-index: 1; }
.s1 { top: 12px; right: 40px; transform: rotate(12deg); }
.s2 { bottom: 60px; right: 90px; transform: rotate(-8deg); }
.cloud { position: absolute; z-index: 1; }
.c1 { top: 8px; right: 100px; }
.ground { position: absolute; bottom: 0; left: 0; z-index: 2; }
.flower { position: absolute; z-index: 3; }
.f1 { bottom: 24px; left: 60px; }
.f2 { bottom: 30px; right: 60px; }
</style>
