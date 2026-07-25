<template>
  <div class="page">
    <StatusBar />
    <div class="page__header"><BackButton /><span class="page__title">今日任务</span></div>

    <!-- decorations -->
    <svg class="doodle-star s1" viewBox="0 0 30 30" width="18" height="18"><path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/></svg>
    <svg class="doodle-star s2" viewBox="0 0 30 30" width="14" height="14"><path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/></svg>
    <svg class="flower f1" viewBox="0 0 20 20" width="16" height="16"><circle cx="10" cy="6" r="4.5" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2"/><circle cx="10" cy="14" r="2.5" fill="#8BC34A" stroke="#2D2D2D" stroke-width="1.5"/></svg>

    <div class="page__body scroll-y">
      <div class="task-card card-sketch" v-for="(t, i) in tasks" :key="i" :class="['card-tilt-' + ((i%3)+1), t.done ? 'task--done' : '']">
        <div class="task-top">
          <span class="task-card__tag">{{ t.category }}</span>
          <div class="task-card__stars">
            <span v-for="s in t.total" :key="s" class="star" :class="{ earned: s <= t.stars }">
              <svg viewBox="0 0 30 30" width="22" height="22"><path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z" fill="currentColor" stroke="none"/></svg>
            </span>
            <span class="star-count">{{ t.stars }}/{{ t.total }}</span>
          </div>
        </div>
        <div class="task-card__title">{{ t.title }}</div>
        <div class="task-card__desc">{{ t.desc }}</div>
        <div v-if="t.note" class="task-card__note">{{ t.note }}</div>
        <button class="btn-sketch" :style="t.done ? 'background:#AACE7B' : 'background:#FFB300;color:#fff'">
          {{ t.done ? '已完成' : '开始闯关 →' }}
        </button>
      </div>
      <div class="bottom-nav">
        <button class="btn-sketch" @click="$router.push('/')">回首页</button>
        <button class="btn-sketch" style="background:#FFB300;color:#fff" @click="$router.push('/challenge')">去闯关挑战 →</button>
      </div>
    </div>

    <svg class="ground" viewBox="0 0 1024 50" width="1024" height="50" preserveAspectRatio="none"><path d="M0 28 Q100 12 200 24 Q300 36 400 16 Q500 4 600 22 Q700 34 800 14 Q900 4 1024 12 L1024 50 L0 50Z" fill="#AACE7B" stroke="#2D2D2D" stroke-width="2" opacity="0.3"/></svg>

    <DankePet scene="tasks" />
  </div>
</template>

<script setup>
import StatusBar from '../components/StatusBar.vue'
import BackButton from '../components/BackButton.vue'
import DankePet from '../components/DankePet.vue'
const tasks = [
  { category: '数学', title: '完成数学练习册第3页', desc: '妈妈布置的 · 5道题', stars: 2, total: 5, note: '妈妈说：加油宝贝，做完一起去公园！', done: false },
  { category: '英语', title: '学5个新单词', desc: '爸爸布置的 · 跟读练习', stars: 0, total: 3, note: '', done: false },
  { category: '阅读', title: '读一篇故事', desc: '已完成 · 用时12分钟', stars: 3, total: 3, note: '', done: true },
]
</script>

<style scoped>
.page { width: 100%; height: 100%; display: flex; flex-direction: column; position: relative; overflow: hidden; background: var(--bg-paper); }
.page__header { height: 50px; display: flex; align-items: center; padding: 0 var(--space-5); gap: var(--space-3); position: relative; z-index: 5; }
.page__title { font-family: var(--font-heading); font-size: 26px; color: #B8780A; }
.page__body { flex: 1; padding: var(--space-4) var(--space-6) var(--space-2); display: flex; gap: var(--space-5); overflow-x: auto; align-items: stretch; position: relative; z-index: 5; }
.task-card { flex-shrink: 0; width: 270px; padding: var(--space-5); display: flex; flex-direction: column; gap: var(--space-3); background: var(--bg-card); }
.task-top { display: flex; justify-content: space-between; align-items: center; }
.task-card__tag { font-family: var(--font-heading); font-size: 14px; color: #B8780A; background: #FFEC8E; padding: 4px 12px; border-radius: 12px 14px 10px 13px; border: 2px solid var(--ink-black); }
.task-card__title { font-family: var(--font-heading); font-size: var(--text-lg); line-height: 1.3; }
.task-card__desc { font-family: var(--font-body); font-size: var(--text-sm); color: var(--ink-muted); }
.task-card__stars { display: flex; align-items: center; gap: 1px; }
.star { color: #DDD; display: inline-flex; }
.star.earned { color: #FFB300; }
.star-count { font-family: var(--font-body); font-size: var(--text-sm); color: var(--ink-muted); margin-left: 6px; }
.task-card__note { font-family: var(--font-body); font-size: var(--text-sm); color: var(--brand-coral); padding: var(--space-2); background: rgba(232,130,107,0.06); border: 1.5px dashed var(--brand-coral); line-height: 1.4; border-radius: 10px; }
.task--done { opacity: 0.55; }

.bottom-nav { display: flex; gap: var(--space-4); margin-top: auto; padding-top: var(--space-3); flex-shrink: 0; }
.bottom-nav .btn-sketch { height: 44px; padding: 0 var(--space-5); font-size: 15px; flex-shrink: 0; }

.doodle-star { position: absolute; z-index: 1; }
.s1 { top: 10px; right: 50px; transform: rotate(10deg); }
.s2 { bottom: 40px; right: 100px; transform: rotate(-8deg); }
.flower { position: absolute; z-index: 1; }
.f1 { bottom: 30px; left: 50px; }
.ground { position: absolute; bottom: 0; left: 0; z-index: 2; }
</style>
