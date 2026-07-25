<template>
  <div class="page">
    <StatusBar />
    <div class="nav-row">
      <button class="nav-back" @click="router.back()">←</button>
      <span class="nav-title">科学探索</span>
      <span class="nav-progress">{{ idx + 1 }}/{{ cards.length }}</span>
      <div class="nav-arrows">
        <button class="nav-btn" :disabled="idx === 0" @click="idx--">◀</button>
        <button class="nav-btn" :disabled="idx === cards.length - 1" @click="idx++">▶</button>
      </div>
      <button class="nav-home" @click="router.push('/')">首页</button>
    </div>

    <div class="content scroll-y">
      <svg class="scene-bg" viewBox="0 0 1024 500" width="1024" height="500" preserveAspectRatio="none">
        <path d="M-50 520 Q200 430 400 480 Q600 530 800 460 Q950 420 1100 460 L1100 530 L-50 530Z" fill="#8BC34A" stroke="#2D2D2D" stroke-width="1.5" opacity="0.3"/>
        <circle cx="120" cy="440" r="6" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="1.5"/><circle cx="180" cy="455" r="5" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="1.5"/>
        <circle cx="860" cy="445" r="6" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="1.5"/><circle cx="930" cy="460" r="5" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="1.5"/>
        <circle cx="770" cy="130" r="28" fill="none" stroke="#2D2D2D" stroke-width="3"/><circle cx="770" cy="130" r="20" fill="#C0E3F5" opacity="0.35"/><line x1="790" y1="150" x2="818" y2="178" stroke="#2D2D2D" stroke-width="3.5" stroke-linecap="round"/>
        <polygon points="80,70 84,84 98,86 87,96 89,110 80,102 71,110 73,96 62,86 76,84" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/>
        <polygon points="700,50 703,58 712,60 705,65 707,73 700,68 693,73 695,65 688,60 697,58" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="1.5" stroke-linejoin="round"/>
        <polygon points="400,55 403,62 410,64 405,68 406,74 400,70 394,74 395,68 390,64 397,62" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="1.5" stroke-linejoin="round"/>
      </svg>

      <div class="pb-card card-sketch">
        <div class="card-illust">
          <svg viewBox="0 0 280 150" width="260" height="140">
            <template v-if="idx === 0">
              <ellipse cx="60" cy="95" rx="11" ry="6" fill="#AACE7B" stroke="#2D2D2D" stroke-width="2.5"/>
              <path d="M78 95 Q95 78 112 95" fill="none" stroke="#AACE7B" stroke-width="3.5" stroke-linecap="round"/>
              <text x="68" y="120" font-size="12" font-family="ZCOOL KuaiLe" fill="#2D2D2D" text-anchor="middle">叶</text>
              <ellipse cx="185" cy="78" rx="16" ry="13" fill="#C0A080" stroke="#2D2D2D" stroke-width="2.5"/>
              <text x="185" y="108" font-size="12" font-family="ZCOOL KuaiLe" fill="#2D2D2D" text-anchor="middle">蛹</text>
              <ellipse cx="90" cy="135" rx="26" ry="18" fill="#FFB5A0" stroke="#2D2D2D" stroke-width="2.5" transform="rotate(-10 90 135)"/>
              <ellipse cx="160" cy="135" rx="26" ry="18" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2.5" transform="rotate(10 160 135)"/>
              <line x1="125" y1="95" x2="125" y2="145" stroke="#2D2D2D" stroke-width="2.5"/>
            </template>
            <template v-else-if="idx === 1">
              <circle cx="140" cy="75" r="50" fill="#C0E3F5" stroke="#2D2D2D" stroke-width="3"/>
              <path d="M90 55 Q120 45 155 58 Q175 72 155 95 Q130 115 95 100 Q75 82 90 55Z" fill="#AACE7B" stroke="#2D2D2D" stroke-width="2"/>
              <text x="140" y="150" font-size="12" font-family="ZCOOL KuaiLe" fill="#2D2D2D" text-anchor="middle">12742 公里</text>
            </template>
            <template v-else-if="idx === 2">
              <circle cx="140" cy="75" r="38" fill="#FFB300" stroke="#2D2D2D" stroke-width="3"/>
              <line x1="140" y1="25" x2="140" y2="12" stroke="#2D2D2D" stroke-width="2.5"/><line x1="140" y1="125" x2="140" y2="138" stroke="#2D2D2D" stroke-width="2.5"/>
              <line x1="88" y1="75" x2="75" y2="75" stroke="#2D2D2D" stroke-width="2.5"/><line x1="192" y1="75" x2="205" y2="75" stroke="#2D2D2D" stroke-width="2.5"/>
              <polygon points="40,40 43,49 52,51 45,56 47,65 40,60 33,65 35,56 28,51 37,49" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="1.5" stroke-linejoin="round"/>
            </template>
            <template v-else>
              <path d="M55 145 Q90 75 135 65 Q180 55 220 90" fill="none" stroke="#C0E3F5" stroke-width="4.5" stroke-linecap="round"/>
              <path d="M55 145 Q80 130 110 140 Q140 150 180 130" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="2.5"/>
              <path d="M70 115 Q90 95 120 98 Q150 102 180 88" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="1.8"/>
              <path d="M45 155 L55 145 L45 160 L35 150Z" fill="#3B82C6" stroke="#2D2D2D" stroke-width="1.5"/>
              <path d="M90 155 L100 145 L90 160 L80 150Z" fill="#3B82C6" stroke="#2D2D2D" stroke-width="1.5"/>
              <text x="135" y="45" font-size="12" font-family="ZCOOL KuaiLe" fill="#2D2D2D" text-anchor="middle">水循环</text>
            </template>
          </svg>
        </div>
        <h2 class="card-title">{{ cards[idx].title }}</h2>
        <p class="card-body">{{ cards[idx].body }}</p>
        <div class="card-meta">
          <span class="meta-dots">
            <span v-for="n in cards.length" :key="n" class="dot" :class="{ done: n <= idx + 1 }"></span>
          </span>
          <span class="meta-label">探索进度</span>
        </div>
      </div>
    </div>

    <DankePet scene="science" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import StatusBar from '../components/StatusBar.vue'
import DankePet from '../components/DankePet.vue'

const router = useRouter()
const idx = ref(0)
const cards = [
  { title: '蝴蝶怎么变成的？', body: '蝴蝶小时候是一条毛毛虫！它先吃掉很多叶子，然后把自己包成蛹。在蛹里面，它的身体会重新组合，最后变成漂亮的蝴蝶飞出来。这是一个叫"变态发育"的神奇过程！' },
  { title: '地球是圆的吗？', body: '是的！地球是一个巨大的球体，但我们感觉不到因为太大了。从太空中看地球是蓝色的，因为大部分表面都是海洋。地球的直径大约是12742公里，如果开车绕一圈要整整一年！' },
  { title: '星星为什么会发光？', body: '星星是巨大的火球！它们由很热很热的气体组成，中心的温度高达几千万度，发生一种叫"核聚变"的反应，把氢变成氦，同时发出光和热。太阳也是一颗星星哦！' },
  { title: '为什么会下雨？', body: '太阳把大地和海洋上的水晒热变成水蒸气，水蒸气上升到高空遇冷变成小水滴聚成云，水滴越聚越大太重了就落下来变成雨。这就是水循环，非常重要！' },
]
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

.pb-card { width: 560px; min-height: 380px; padding: var(--space-4) var(--space-6); display: flex; flex-direction: column; align-items: center; gap: var(--space-2); background: var(--bg-card); position: relative; z-index: 2; margin-top: var(--space-1); }
.card-illust { min-height: 140px; display: flex; align-items: center; justify-content: center; margin-bottom: 2px; }
.card-title { font-family: var(--font-heading); font-size: 24px; color: var(--ink-black); }
.card-body { font-family: var(--font-body); font-size: var(--text-lg); line-height: 1.6; text-align: center; color: var(--ink-brown); max-width: 470px; min-height: 80px; }
.card-meta { display: flex; align-items: center; gap: var(--space-2); margin-top: 2px; }
.meta-dots { display: flex; gap: 4px; }
.dot { width: 9px; height: 9px; border-radius: 50%; border: 2px solid #DDD; }
.dot.done { background: #AACE7B; border-color: #6B9B37; }
.meta-label { font-family: var(--font-body); font-size: 14px; color: var(--ink-muted); }
</style>
