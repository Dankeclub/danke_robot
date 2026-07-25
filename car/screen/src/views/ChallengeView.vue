<template>
  <div class="page">
    <StatusBar />
    <div class="page__header"><BackButton /><span class="page__title">闯关进行中</span></div>

    <!-- decorations -->
    <svg class="doodle-star s1" viewBox="0 0 30 30" width="16" height="16"><path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/></svg>
    <svg class="cloud c1" viewBox="0 0 100 50" width="38" height="19"><path d="M18 40 Q12 28 20 22 Q16 8 32 12 Q38 -2 52 10 Q62 -2 72 14 Q88 8 86 24 Q96 28 86 40 Q76 44 58 42Z" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="2" opacity="0.4"/></svg>

    <div class="page__body scroll-y">
      <div class="wrapper">
        <div class="challenge-card card-sketch">
          <div class="ch-progress">
            <span class="ch-progress__label">闯关进度</span>
            <div class="ch-progress__bar"><div class="ch-progress__fill" :style="{ width: '40%' }"></div></div>
            <span class="ch-progress__pct">40%</span>
          </div>
          <div class="ch-question">妈妈每天去公园走多少步？</div>
          <div class="ch-hint">
            <svg viewBox="0 0 20 20" width="18" height="18" style="vertical-align:middle;margin-right:4px"><circle cx="10" cy="10" r="8" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2"/><circle cx="8" cy="9" r="1.5" fill="#2D2D2D"/><circle cx="13" cy="9" r="1.5" fill="#2D2D2D"/><path d="M7 14 Q10 17 13 14" fill="none" stroke="#2D2D2D" stroke-width="2" stroke-linecap="round"/></svg>
            蛋仔提示：想一想平时妈妈在公园里走路的步数~ 生活中观察到的数字往往就是答案！
          </div>
          <div class="ch-options">
            <button v-for="o in ['3000步', '5000步', '8000步', '10000步以上']" :key="o" class="opt-btn btn-sketch">{{ o }}</button>
          </div>
          <div class="ch-actions">
            <button class="btn-sketch">跳过</button>
            <button class="btn-sketch btn-sketch--primary" style="background:#FFB300">提交答案</button>
          </div>
        </div>
        <div class="challenge-card card-sketch" style="margin-top:12px">
          <div class="ch-progress">
            <span class="ch-progress__label">闯关进度</span>
            <div class="ch-progress__bar"><div class="ch-progress__fill" :style="{ width: '80%' }"></div></div>
            <span class="ch-progress__pct">80%</span>
          </div>
          <div class="ch-question">爸爸每天早上跑步多少分钟？</div>
          <div class="ch-hint">
            <svg viewBox="0 0 20 20" width="18" height="18" style="vertical-align:middle;margin-right:4px"><circle cx="10" cy="10" r="8" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2"/><circle cx="8" cy="9" r="1.5" fill="#2D2D2D"/><circle cx="13" cy="9" r="1.5" fill="#2D2D2D"/><path d="M7 14 Q10 17 13 14" fill="none" stroke="#2D2D2D" stroke-width="2" stroke-linecap="round"/></svg>
            蛋仔提示：记得爸爸说过他每天跑半小时左右~
          </div>
          <div class="ch-options">
            <button v-for="o in ['15分钟', '30分钟', '45分钟', '60分钟']" :key="o" class="opt-btn btn-sketch">{{ o }}</button>
          </div>
          <div class="ch-actions">
            <button class="btn-sketch">跳过</button>
            <button class="btn-sketch btn-sketch--primary" style="background:#FFB300">提交答案</button>
          </div>
        </div>
      </div>
      <div class="bottom-nav">
        <button class="btn-sketch" @click="$router.push('/')">回首页</button>
        <button class="btn-sketch" style="background:#FFB300;color:#fff" @click="$router.push('/tasks')">查看今日任务 →</button>
      </div>
    </div>

    <svg class="ground" viewBox="0 0 1024 50" width="1024" height="50" preserveAspectRatio="none"><path d="M0 28 Q100 12 200 24 Q300 36 400 16 Q500 4 600 22 Q700 34 800 14 Q900 4 1024 12 L1024 50 L0 50Z" fill="#AACE7B" stroke="#2D2D2D" stroke-width="2" opacity="0.3"/></svg>

    <DankePet scene="challenge" />
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
.page__body { flex: 1; padding: var(--space-3) var(--space-6); display: flex; flex-direction: column; align-items: center; position: relative; z-index: 5; }
.wrapper { display: flex; flex-direction: column; align-items: center; }
.challenge-card { width: 580px; padding: var(--space-6); display: flex; flex-direction: column; gap: var(--space-4); background: var(--bg-card); }
.ch-progress { display: flex; align-items: center; gap: var(--space-3); }
.ch-progress__label { font-family: var(--font-body); font-size: var(--text-sm); color: var(--ink-muted); white-space: nowrap; }
.ch-progress__bar { flex: 1; height: 14px; background: #FFF8E1; border: 2px solid var(--ink-black); border-radius: 10px; overflow: hidden; }
.ch-progress__fill { height: 100%; background: #FFB300; border-radius: 8px; }
.ch-progress__pct { font-family: var(--font-heading); font-size: var(--text-base); min-width: 40px; text-align: right; }
.ch-question { font-family: var(--font-heading); font-size: 28px; text-align: center; line-height: 1.4; }
.ch-hint { font-family: var(--font-body); font-size: 15px; color: var(--brand-coral); text-align: center; padding: var(--space-3); background: rgba(232,130,107,0.06); border-radius: 10px; border: 1.5px dashed var(--brand-coral); line-height: 1.5; }
.ch-options { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); }
.opt-btn { height: 56px; font-family: var(--font-heading); font-size: var(--text-lg); }
.ch-actions { display: flex; gap: var(--space-3); justify-content: center; margin-top: var(--space-1); }

.bottom-nav { display: flex; gap: var(--space-4); margin-top: var(--space-3); padding-bottom: var(--space-3); }
.bottom-nav .btn-sketch { height: 44px; padding: 0 var(--space-5); font-size: 15px; }

.doodle-star { position: absolute; z-index: 1; }
.s1 { top: 10px; right: 50px; transform: rotate(12deg); }
.cloud { position: absolute; z-index: 1; }
.c1 { top: 6px; right: 150px; }
.ground { position: absolute; bottom: 0; left: 0; z-index: 2; }
</style>
