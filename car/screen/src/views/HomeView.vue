<template>
  <div class="home">
    <StatusBar />

    <!-- Welcome -->
    <div class="home__welcome">
      <h1>嗨！今天想做什么？</h1>
      <p>选一个开始吧 ~</p>
    </div>

    <!-- Alert test bar -->
  <div class="alert-test-bar">
    <button class="btn-sketch btn-test" @click="testAlert('attention')">走神提醒</button>
    <button class="btn-sketch btn-test" @click="testAlert('posture')">坐姿提醒</button>
  </div>

  <!-- Sky decorations -->
    <svg class="cloud cloud--1" viewBox="0 0 100 50" width="55" height="28">
      <path d="M18 40 Q12 28 20 22 Q16 8 32 12 Q38 -2 52 10 Q62 -2 72 14 Q88 8 86 24 Q96 28 86 40 Q76 44 58 42Z" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="2" opacity="0.55"/>
    </svg>
    <svg class="cloud cloud--2" viewBox="0 0 100 50" width="45" height="23">
      <path d="M15 35 Q10 22 18 16 Q14 4 30 10 Q36 0 48 8 Q58 -2 68 12 Q82 6 78 22 Q88 26 80 36 Q70 40 54 38Z" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="2" opacity="0.45"/>
    </svg>
    <svg class="cloud cloud--3" viewBox="0 0 100 50" width="50" height="25">
      <path d="M16 38 Q10 24 18 18 Q14 6 30 10 Q36 0 48 8 Q58 -2 68 10 Q82 6 78 22 Q88 26 80 36 Z" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="2" opacity="0.5"/>
    </svg>

    <svg class="doodle-star s1" viewBox="0 0 30 30" width="20" height="20"><path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/></svg>
    <svg class="doodle-star s2" viewBox="0 0 30 30" width="16" height="16"><path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/></svg>
    <svg class="doodle-star s3" viewBox="0 0 30 30" width="18" height="18"><path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/></svg>
    <svg class="doodle-star s4" viewBox="0 0 30 30" width="14" height="14"><path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/></svg>
    <svg class="doodle-star s5" viewBox="0 0 30 30" width="17" height="17"><path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/></svg>

    <svg class="bird b1" viewBox="0 0 30 16" width="24" height="13"><path d="M2 12 Q8 2 15 6 Q22 2 28 12" fill="none" stroke="#2D2D2D" stroke-width="2" stroke-linecap="round"/></svg>
    <svg class="bird b2" viewBox="0 0 24 12" width="18" height="9"><path d="M2 10 Q7 2 12 5 Q17 2 22 10" fill="none" stroke="#2D2D2D" stroke-width="2" stroke-linecap="round"/></svg>

    <!-- ══════════ Two-Column Card Area ══════════ -->
    <div class="home__content">
      <!-- Left column -->
      <div class="col-left">
        <SceneCard theme="learn" icon="ri-book-open-line" label="学习乐园"
                   subtitle="数学 · 英语 · 科学 · 古诗 · 音乐"
                   size="wide" :tilt-index="2"
                   @click="go('/learning')">
          <template #extra>
            <span class="card-arrow">→</span>
          </template>
        </SceneCard>

        <SceneCard theme="chat" icon="ri-chat-smile-3-line" label="跟蛋仔聊天"
                   subtitle="想聊什么我都陪你 ~"
                   size="wide" :tilt-index="1"
                   @click="go('/chat')">
          <template #extra>
            <span class="btn-sketch btn-sketch--primary card-cta">开始聊天</span>
          </template>
        </SceneCard>
      </div>

      <!-- Right column -->
      <div class="col-right">
        <SceneCard theme="task" icon="ri-gamepad-line" label="今日任务"
                   size="side" :tilt-index="0" @click="go('/tasks')" />
        <SceneCard theme="qa" icon="ri-question-line" label="问答百宝箱"
                   size="side" :tilt-index="3" @click="go('/qabox')" />
        <SceneCard theme="message" icon="ri-hearts-line" label="家长消息"
                   badge="3" size="side" :tilt-index="4" @click="go('/messages')" />
      </div>
    </div>

    <!-- Ground decorations -->
    <svg class="ground" viewBox="0 0 1024 100" width="1024" height="100" preserveAspectRatio="none">
      <path d="M0 70 Q60 30 140 50 Q220 70 300 40 Q380 10 460 45 Q540 70 620 35 Q700 5 780 40 Q860 65 940 30 Q1000 10 1024 25 L1024 100 L0 100Z"
            fill="#AACE7B" stroke="#2D2D2D" stroke-width="2" opacity="0.6"/>
      <rect x="0" y="75" width="1024" height="25" fill="#D4A76A" stroke="#2D2D2D" stroke-width="1.5" opacity="0.4"/>
    </svg>
    <svg class="grass" viewBox="0 0 1024 30" width="1024" height="30" preserveAspectRatio="none">
      <g stroke="#6B9B37" stroke-width="2" stroke-linecap="round" fill="none" opacity="0.6">
        <path d="M0 30 Q12 12 4 0"/><path d="M18 30 Q26 14 22 0"/>
        <path d="M36 30 Q44 16 40 2"/><path d="M56 30 Q64 18 60 4"/>
        <path d="M78 30 Q86 14 82 0"/><path d="M98 30 Q106 18 102 4"/>
        <path d="M120 30 Q128 14 124 0"/><path d="M142 30 Q150 18 146 4"/>
        <path d="M166 30 Q174 14 170 0"/><path d="M190 30 Q198 18 194 4"/>
        <path d="M216 30 Q224 14 220 0"/><path d="M240 30 Q248 18 244 4"/>
        <path d="M266 30 Q274 14 270 0"/><path d="M290 30 Q298 18 294 4"/>
      </g>
    </svg>

    <svg class="bush" viewBox="0 0 120 60" width="80" height="40">
      <ellipse cx="30" cy="45" rx="28" ry="22" fill="#8BC34A" stroke="#2D2D2D" stroke-width="2" opacity="0.6"/>
      <ellipse cx="60" cy="40" rx="32" ry="25" fill="#AACE7B" stroke="#2D2D2D" stroke-width="2" opacity="0.65"/>
      <ellipse cx="90" cy="45" rx="26" ry="20" fill="#8BC34A" stroke="#2D2D2D" stroke-width="2" opacity="0.6"/>
    </svg>

    <svg class="flower f1" viewBox="0 0 20 20" width="18" height="18"><circle cx="10" cy="6" r="4.5" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2"/><circle cx="10" cy="14" r="2.5" fill="#AACE7B" stroke="#2D2D2D" stroke-width="1.5"/></svg>
    <svg class="flower f4" viewBox="0 0 20 20" width="14" height="14"><circle cx="10" cy="6" r="4.5" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="2"/><circle cx="10" cy="14" r="2.5" fill="#AACE7B" stroke="#2D2D2D" stroke-width="1.5"/></svg>
    <svg class="flower f5" viewBox="0 0 20 20" width="15" height="15"><circle cx="10" cy="6" r="4.5" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2"/><circle cx="10" cy="14" r="2.5" fill="#AACE7B" stroke="#2D2D2D" stroke-width="1.5"/></svg>

    <DankePet scene="home" />
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import StatusBar from '../components/StatusBar.vue'
import SceneCard from '../components/SceneCard.vue'
import DankePet from '../components/DankePet.vue'
import { useAlertPopup } from '../utils/alert-popup.js'

const { show: showAlert } = useAlertPopup()
const router = useRouter()
function go(route) { router.push(route) }

function testAlert(type) {
  if (type === 'attention') {
    showAlert({ type: 'attention', message: '嘿，你好像有点走神了哦~ 要不要先休息一下，站起来动一动？' })
  } else {
    showAlert({ type: 'posture', message: '你的坐姿有点歪啦！快坐好，背挺直，像一棵小树苗一样~' })
  }
}
</script>

<style scoped>
.home { width: 100%; height: 100%; display: flex; flex-direction: column; position: relative; overflow: hidden; }

/* ─── Welcome ─── */
.home__welcome { text-align: center; padding-top: 6px; padding-bottom: 2px; position: relative; z-index: 5; }
.home__welcome h1 { font-family: var(--font-heading); font-size: 28px; font-weight: 400; color: var(--ink-black); letter-spacing: 1.5px; }
.home__welcome p { font-family: var(--font-body); font-size: var(--text-sm); color: var(--ink-brown); margin-top: 0; }

.alert-test-bar { display: flex; justify-content: center; gap: var(--space-4); position: relative; z-index: 5; }
.btn-test { height: 36px; padding: 0 var(--space-4); font-size: 13px; background: #FFF5F5; border-color: #EF4444; color: #EF4444; }

/* ─── Two-column area ─── */
.home__content {
  flex: 1;
  display: flex;
  gap: 32px;
  justify-content: center;
  align-items: center;
  padding: 0 var(--space-8) 14px;
  position: relative;
  z-index: 5;
}

.col-left {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.col-right {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* ─── Left card extras ─── */
.card-arrow {
  font-family: var(--font-heading);
  font-size: 28px;
  color: var(--ink-muted);
  margin-left: auto;
}
.card-cta {
  font-size: var(--text-sm);
  height: 42px;
  padding: 0 var(--space-6);
  align-self: flex-end;
  margin-top: auto;
}

/* ─── Star / Bird / Cloud positions ─── */
.doodle-star { position: absolute; z-index: 1; }
.s1 { top: 38px;  left: 130px; transform: rotate(10deg); }
.s2 { top: 50px;  right: 260px; transform: rotate(-8deg); }
.s3 { top: 18px;  right: 50px;  transform: rotate(15deg); }
.s4 { top: 56px;  left: 280px; transform: rotate(22deg); }
.s5 { top: 16px;  left: 50px;  transform: rotate(-14deg); }

.cloud { position: absolute; z-index: 1; }
.cloud--1 { top: 16px;  left: 340px; }
.cloud--2 { top: 44px;  right: 140px; }
.cloud--3 { top: 6px;   left: 460px; }

.bird { position: absolute; z-index: 1; }
.b1 { top: 26px; left: 520px; }
.b2 { top: 32px; left: 555px; }

/* ─── Ground ─── */
.ground { position: absolute; bottom: 0; left: 0; z-index: 3; }
.grass  { position: absolute; bottom: -2px; left: 0; z-index: 4; }
.bush   { position: absolute; bottom: 34px; right: 40px; z-index: 4; }

.flower { position: absolute; z-index: 5; }
.f1 { bottom: 40px; left: 40px; }
.f4 { bottom: 28px; right: 220px; }
.f5 { bottom: 36px; right: 30px; }
</style>
