<template>
  <div class="page">
    <StatusBar />
    <div class="page__header"><BackButton /><span class="page__title">问答百宝箱</span></div>

    <!-- decorations -->
    <svg class="doodle-star s1" viewBox="0 0 30 30" width="14" height="14"><path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/></svg>
    <svg class="question-doodle" viewBox="0 0 32 36" width="18" height="20"><circle cx="16" cy="14" r="12" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="2.5"/><path d="M12 10 Q16 6 20 10 Q22 12 19 15 Q16 18 16 20" fill="none" stroke="#2D2D2D" stroke-width="2.5" stroke-linecap="round"/><circle cx="16" cy="26" r="2.5" fill="#2D2D2D"/></svg>
    <svg class="cloud c1" viewBox="0 0 100 50" width="36" height="18"><path d="M18 40 Q12 28 20 22 Q16 8 32 12 Q38 -2 52 10 Q62 -2 72 14 Q88 8 86 24 Q96 28 86 40 Q76 44 58 42Z" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="2" opacity="0.4"/></svg>

    <div class="qa-area scroll-y">
      <div v-if="answer" class="qa-answer card-sketch">
        <div class="qa-answer__q">Q: {{ lastQ }}</div>
        <div class="qa-answer__a">A: {{ answer }}</div>
      </div>
      <div v-else class="qa-placeholder card-sketch">
        <svg viewBox="0 0 60 60" width="60" height="60"><circle cx="30" cy="30" r="24" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="2.5"/><path d="M20 24 Q30 18 40 24 Q43 26 40 29 Q36 32 30 34 Q24 32 21 29 Q18 26 20 24Z" fill="#2D2D2D"/><circle cx="24" cy="38" r="2.5" fill="#2D2D2D"/><circle cx="36" cy="38" r="2.5" fill="#2D2D2D"/><path d="M24 42 Q30 46 36 42" fill="none" stroke="#2D2D2D" stroke-width="2" stroke-linecap="round"/></svg>
        <p>问我任何问题吧！</p>
        <p class="qa-sub">点击下方或输入你想问的~</p>
      </div>
      <div class="qa-prompts">
        <span v-for="p in prompts" :key="p" class="qa-prompt" @click="ask(p)">{{ p }}</span>
      </div>
      <div class="qa-bar">
        <input class="qa-input" placeholder="想问什么就写下来..." v-model="inputText" @keyup.enter="ask(inputText)">
        <button class="send-btn" @click="ask(inputText)"><i class="ri-send-plane-fill"></i></button>
      </div>
      <div class="bottom-nav">
        <button class="btn-sketch" @click="$router.push('/')">回首页</button>
      </div>
    </div>

    <svg class="ground" viewBox="0 0 1024 50" width="1024" height="50" preserveAspectRatio="none"><path d="M0 28 Q100 12 200 24 Q300 36 400 16 Q500 4 600 22 Q700 34 800 14 Q900 4 1024 12 L1024 50 L0 50Z" fill="#AACE7B" stroke="#2D2D2D" stroke-width="2" opacity="0.3"/></svg>

    <DankePet scene="qabox" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import StatusBar from '../components/StatusBar.vue'
import BackButton from '../components/BackButton.vue'
import DankePet from '../components/DankePet.vue'
const inputText = ref('')
const answer = ref('')
const lastQ = ref('')
const prompts = ['恐龙是怎么灭绝的？', '为什么天是蓝的？', '最大的动物是什么？', '彩虹是怎么来的？']
function ask(q) {
  if (!q.trim()) return
  lastQ.value = q
  answer.value = '让我想想... 这个问题很有趣！其实，这背后有很多科学知识可以探索。你可以先观察一下周围，看看有什么线索吗？我们可以一起查阅资料来找到答案！'
  inputText.value = ''
}
</script>

<style scoped>
.page { width: 100%; height: 100%; display: flex; flex-direction: column; position: relative; overflow: hidden; background: var(--bg-grass); }
.page__header { height: 50px; display: flex; align-items: center; padding: 0 var(--space-5); gap: var(--space-3); position: relative; z-index: 5; }
.page__title { font-family: var(--font-heading); font-size: 26px; color: #4B7A1F; }
.qa-area { flex: 1; display: flex; flex-direction: column; align-items: center; padding: var(--space-4) var(--space-6); gap: var(--space-3); overflow-y: auto; min-height: 0; position: relative; z-index: 5; }
.qa-answer { width: 100%; max-width: 660px; padding: var(--space-5); background: var(--bg-card); }
.qa-answer__q { font-family: var(--font-heading); font-size: var(--text-lg); margin-bottom: var(--space-4); color: #4B7A1F; }
.qa-answer__a { font-family: var(--font-body); font-size: var(--text-lg); line-height: 1.7; }
.qa-placeholder { width: 100%; max-width: 400px; padding: var(--space-8) var(--space-6); display: flex; flex-direction: column; align-items: center; gap: var(--space-2); background: var(--bg-card); }
.qa-placeholder p { font-family: var(--font-body); font-size: var(--text-lg); color: var(--ink-black); }
.qa-sub { font-size: var(--text-sm) !important; color: var(--ink-muted) !important; margin-top: 4px; }
.qa-prompts { display: flex; gap: var(--space-3); flex-wrap: wrap; justify-content: center; }
.qa-prompt { padding: 10px 20px; border: 2px solid var(--ink-black); border-radius: 16px; background: var(--bg-card); font-family: var(--font-body); font-size: 15px; cursor: pointer; box-shadow: 1.5px 1.5px 0 var(--ink-black); transition: 0.12s; }
.qa-prompt:active { transform: scale(0.93); }
.qa-bar { display: flex; width: 100%; max-width: 660px; gap: var(--space-3); align-items: center; }
.qa-input { flex: 1; height: 50px; padding: 0 var(--space-4); border: 2.5px solid var(--ink-black); border-radius: 20px; font-family: var(--font-body); font-size: 16px; background: var(--bg-card); outline: none; }
.send-btn { width: 50px; height: 50px; border: 2.5px solid var(--ink-black); border-radius: 50%; background: #4B7A1F; color: #fff; font-size: 22px; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 2px 2px 0 var(--ink-black); transition: 0.12s; }
.send-btn:active { transform: scale(0.88); }

.bottom-nav { display: flex; gap: var(--space-4); margin-top: var(--space-1); }
.bottom-nav .btn-sketch { height: 44px; padding: 0 var(--space-5); font-size: 15px; }

.doodle-star { position: absolute; z-index: 1; }
.s1 { top: 10px; right: 50px; transform: rotate(10deg); }
.question-doodle { position: absolute; bottom: 60px; right: 60px; z-index: 1; transform: rotate(-5deg); }
.cloud { position: absolute; z-index: 1; }
.c1 { top: 4px; right: 150px; }
.ground { position: absolute; bottom: 0; left: 0; z-index: 2; }
</style>
