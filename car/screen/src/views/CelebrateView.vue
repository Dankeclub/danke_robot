<template>
  <div class="page">
    <StatusBar />
    <div class="page__header"><BackButton /><span class="page__title">庆祝时刻</span></div>

    <!-- decorations -->
    <svg class="doodle-star s1" viewBox="0 0 30 30" width="22" height="22"><path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/></svg>
    <svg class="doodle-star s2" viewBox="0 0 30 30" width="18" height="18"><path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/></svg>
    <svg class="doodle-star s3" viewBox="0 0 30 30" width="16" height="16"><path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/></svg>
    <svg class="cloud c1" viewBox="0 0 100 50" width="42" height="21"><path d="M18 40 Q12 28 20 22 Q16 8 32 12 Q38 -2 52 10 Q62 -2 72 14 Q88 8 86 24 Q96 28 86 40 Q76 44 58 42Z" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="2" opacity="0.45"/></svg>
    <svg class="flower f1" viewBox="0 0 20 20" width="18" height="18"><circle cx="10" cy="6" r="4.5" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2"/><circle cx="10" cy="14" r="2.5" fill="#8BC34A" stroke="#2D2D2D" stroke-width="1.5"/></svg>
    <svg class="flower f2" viewBox="0 0 20 20" width="14" height="14"><circle cx="10" cy="6" r="4.5" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="2"/><circle cx="10" cy="14" r="2.5" fill="#8BC34A" stroke="#2D2D2D" stroke-width="1.5"/></svg>

    <div class="celebration scroll-y">
      <div class="cele__stars">
        <svg viewBox="0 0 120 36" width="120" height="36">
          <polygon points="18,3 21,14 33,16 23,24 25,36 18,30 11,36 13,24 3,16 15,14" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/>
          <polygon points="60,3 63,14 75,16 65,24 67,36 60,30 53,36 55,24 45,16 57,14" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/>
          <polygon points="102,3 105,14 117,16 107,24 109,36 102,30 95,36 97,24 87,16 99,14" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/>
        </svg>
      </div>
      <h1 class="cele__title">太棒了！</h1>
      <p class="cele__sub">任务完成！获得 3 颗星星</p>
      <div class="cele__cards">
        <div class="cele-card card-sketch"><span class="cele-card__num">2</span><span>连续天数</span></div>
        <div class="cele-card card-sketch"><span class="cele-card__num">98</span><span>总分</span></div>
        <div class="cele-card card-sketch"><span class="cele-card__num">#5</span><span>本周排名</span></div>
      </div>
      <div class="cele__actions">
        <button class="btn-sketch" @click="$router.push('/')">回首页</button>
        <button class="btn-sketch" @click="$router.push('/tasks')">返回任务</button>
        <button class="btn-sketch" style="background:#FFB300;color:#fff" @click="$router.push('/challenge')">下一关 →</button>
      </div>
    </div>

    <svg class="ground" viewBox="0 0 1024 60" width="1024" height="60" preserveAspectRatio="none"><path d="M0 35 Q100 15 200 30 Q300 45 400 22 Q500 5 600 28 Q700 42 800 18 Q900 5 1024 16 L1024 60 L0 60Z" fill="#AACE7B" stroke="#2D2D2D" stroke-width="2" opacity="0.35"/></svg>

    <DankePet scene="celebrate" />
  </div>
</template>

<script setup>
import StatusBar from '../components/StatusBar.vue'
import BackButton from '../components/BackButton.vue'
import DankePet from '../components/DankePet.vue'
</script>

<style scoped>
.page { width: 100%; height: 100%; display: flex; flex-direction: column; position: relative; overflow: hidden; background: var(--bg-paper); }
.page__header { height: 50px; display: flex; align-items: center; padding: 0 var(--space-5); gap: var(--space-3); position: relative; z-index: 5; }
.page__title { font-family: var(--font-heading); font-size: 26px; color: #B8780A; }
.celebration { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: var(--space-4); padding: var(--space-6); position: relative; z-index: 5; }
.cele__stars { animation: bounce 0.6s ease-out; }
.cele__title { font-family: var(--font-heading); font-size: 48px; color: #B8780A; animation: bounce 0.8s ease-out; }
.cele__sub { font-family: var(--font-body); font-size: var(--text-xl); color: var(--ink-brown); }
.cele__cards { display: flex; gap: var(--space-5); }
.cele-card { background: var(--bg-card); padding: var(--space-5) var(--space-7); display: flex; flex-direction: column; align-items: center; gap: 4px; min-width: 120px; border-radius: 20px 22px 18px 24px; }
.cele-card span:last-child { font-family: var(--font-body); font-size: var(--text-base); color: var(--ink-muted); }
.cele-card__num { font-family: var(--font-heading); font-size: 36px; color: #B8780A; line-height: 1.1; }
.cele__actions { display: flex; gap: var(--space-4); margin-top: var(--space-2); }

@keyframes bounce { 0% { transform: scale(0.3); opacity: 0; } 50% { transform: scale(1.15); } 100% { transform: scale(1); opacity: 1; } }

.doodle-star { position: absolute; z-index: 1; }
.s1 { top: 10px; left: 80px; transform: rotate(8deg); }
.s2 { top: 16px; right: 100px; transform: rotate(-12deg); }
.s3 { bottom: 50px; right: 60px; transform: rotate(15deg); }
.cloud { position: absolute; z-index: 1; }
.c1 { top: 6px; left: 200px; }
.flower { position: absolute; z-index: 1; }
.f1 { bottom: 30px; left: 60px; }
.f2 { bottom: 40px; right: 180px; }
.ground { position: absolute; bottom: 0; left: 0; z-index: 2; }
</style>
