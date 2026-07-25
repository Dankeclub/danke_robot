<template>
  <div class="page">
    <StatusBar />
    <div class="page__header"><BackButton /><span class="page__title">家长消息</span><span v-if="unread" class="msg-badge">{{ unread }}</span></div>

    <!-- decorations -->
    <svg class="doodle-star s1" viewBox="0 0 30 30" width="14" height="14"><path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/></svg>
    <svg class="envelope-doodle" viewBox="0 0 40 30" width="24" height="18"><rect x="3" y="4" width="34" height="22" rx="3" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="2.5"/><path d="M3 4 L20 18 L37 4" fill="none" stroke="#2D2D2D" stroke-width="2.5" stroke-linejoin="round"/></svg>
    <svg class="flower f1" viewBox="0 0 20 20" width="15" height="15"><circle cx="10" cy="6" r="4.5" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2"/><circle cx="10" cy="14" r="2.5" fill="#8BC34A" stroke="#2D2D2D" stroke-width="1.5"/></svg>

    <div class="msg-area scroll-y">
      <div v-for="(m, i) in messages" :key="i" class="msg-card card-sketch" :class="m.unread ? 'msg--unread' : ''">
        <div class="msg-avatar">
          <svg viewBox="0 0 36 36" width="32" height="32"><circle cx="18" cy="14" r="10" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="2.5"/><ellipse cx="18" cy="34" rx="14" ry="8" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="2"/></svg>
        </div>
        <div class="msg-body">
          <div class="msg-from">{{ m.from }}<span v-if="m.unread" class="msg-dot-inline"></span></div>
          <div class="msg-text">{{ m.text }}</div>
        </div>
        <div class="msg-right">
          <span class="msg-time">{{ m.time }}</span>
          <i v-if="m.hasTask" class="ri-gamepad-line msg-task-icon"></i>
        </div>
      </div>
      <div class="bottom-nav">
        <button class="btn-sketch" @click="$router.push('/')">回首页</button>
      </div>
    </div>

    <svg class="ground" viewBox="0 0 1024 50" width="1024" height="50" preserveAspectRatio="none"><path d="M0 28 Q100 12 200 24 Q300 36 400 16 Q500 4 600 22 Q700 34 800 14 Q900 4 1024 12 L1024 50 L0 50Z" fill="#AACE7B" stroke="#2D2D2D" stroke-width="2" opacity="0.3"/></svg>

    <DankePet scene="messages" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import StatusBar from '../components/StatusBar.vue'
import BackButton from '../components/BackButton.vue'
import DankePet from '../components/DankePet.vue'
const messages = [
  { from: '妈妈', text: '宝贝记得做完数学作业哦，晚上回来检查~', time: '10分钟前', unread: true, hasTask: true },
  { from: '爸爸', text: '今天放学我们去踢球！准备好球鞋', time: '30分钟前', unread: true, hasTask: false },
  { from: '奶奶', text: '冰箱里有你最爱吃的草莓蛋糕', time: '1小时前', unread: false, hasTask: false },
  { from: '妈妈', text: '昨天的作业写得很好，继续加油！老师也表扬你了', time: '昨天 16:30', unread: false, hasTask: false },
  { from: '爸爸', text: '周末带你去科技馆，记得提前预习一下', time: '昨天 09:00', unread: false, hasTask: true },
]
const unread = computed(() => messages.filter(m => m.unread).length)
</script>

<style scoped>
.page { width: 100%; height: 100%; display: flex; flex-direction: column; position: relative; overflow: hidden; background: var(--bg-cream); }
.page__header { height: 50px; display: flex; align-items: center; padding: 0 var(--space-5); gap: var(--space-3); position: relative; z-index: 5; }
.page__title { font-family: var(--font-heading); font-size: 26px; color: #E8826B; }
.msg-badge { background: #E8826B; color: #fff; font-family: var(--font-heading); font-size: 13px; padding: 2px 8px; border-radius: 10px; border: 2px solid var(--ink-black); }
.msg-area { flex: 1; padding: var(--space-4) var(--space-6); display: flex; flex-direction: column; gap: var(--space-3); overflow-y: auto; min-height: 0; position: relative; z-index: 5; }
.msg-card { display: flex; align-items: center; gap: var(--space-4); padding: var(--space-4) var(--space-5); background: var(--bg-card); }
.msg--unread { background: #FFF5F8; }
.msg-avatar { width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; border: 2px solid var(--ink-black); border-radius: 14px 16px 12px 18px; background: #FCF3B9; flex-shrink: 0; }
.msg-body { flex: 1; }
.msg-from { font-family: var(--font-heading); font-size: var(--text-base); display: flex; align-items: center; gap: 8px; }
.msg-dot-inline { display: inline-block; width: 8px; height: 8px; background: #E8826B; border-radius: 50%; }
.msg-text { font-family: var(--font-body); font-size: 15px; color: var(--ink-brown); margin-top: 3px; line-height: 1.4; }
.msg-right { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; flex-shrink: 0; }
.msg-time { font-family: var(--font-body); font-size: var(--text-xs); color: var(--ink-muted); white-space: nowrap; }
.msg-task-icon { font-size: 18px; color: #FFB300; }

.bottom-nav { display: flex; justify-content: center; margin-top: var(--space-2); }
.bottom-nav .btn-sketch { height: 44px; padding: 0 var(--space-5); font-size: 15px; }

.doodle-star { position: absolute; z-index: 1; }
.s1 { top: 10px; right: 50px; transform: rotate(10deg); }
.envelope-doodle { position: absolute; top: 40px; right: 110px; z-index: 1; transform: rotate(8deg); }
.flower { position: absolute; z-index: 1; }
.f1 { bottom: 40px; right: 60px; }
.ground { position: absolute; bottom: 0; left: 0; z-index: 2; }
</style>
