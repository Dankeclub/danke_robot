<template>
  <div class="page">
    <StatusBar />
    <div class="nav-row">
      <button class="nav-back" @click="router.back()">←</button>
      <span class="nav-title">诗词儿歌</span>
      <span class="nav-progress">{{ idx + 1 }}/{{ poems.length }}</span>
      <div class="nav-arrows">
        <button class="nav-btn" :disabled="idx === 0" @click="idx--">◀</button>
        <button class="nav-btn" :disabled="idx === poems.length - 1" @click="idx++">▶</button>
      </div>
      <button class="nav-home" @click="router.push('/')">首页</button>
    </div>

    <div class="content scroll-y">
      <svg class="scene-bg" viewBox="0 0 1024 530" width="1024" height="530" preserveAspectRatio="none">
        <path d="M100 280 Q180 230 250 260 Q320 240 380 270 Q450 230 500 260 Q580 220 650 250 Q720 230 780 258 Q850 240 920 260 L950 530 L0 530Z" fill="none" stroke="#2D2D2D" stroke-width="1.2" opacity="0.2"/>
        <polygon points="100,350 180,220 260,350" fill="none" stroke="#2D2D2D" stroke-width="2" opacity="0.5"/>
        <polygon points="700,360 780,240 860,360" fill="none" stroke="#2D2D2D" stroke-width="2" opacity="0.5"/>
        <polygon points="350,370 410,280 470,370" fill="none" stroke="#2D2D2D" stroke-width="1.5" opacity="0.4"/>
        <path d="M850 80 Q880 60 880 90 Q860 100 850 80Z" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2"/>
        <line x1="60" y1="380" x2="60" y2="300" stroke="#5C3D2E" stroke-width="3.5" stroke-linecap="round"/>
        <path d="M60 300 Q40 310 30 340 M60 310 Q50 330 45 350 M60 310 Q80 320 85 340 M60 320 Q70 340 75 355" fill="none" stroke="#AACE7B" stroke-width="1.8" stroke-linecap="round"/>
        <path d="M0 400 Q150 360 300 390 Q450 410 600 380 Q750 360 900 385 Q1000 395 1024 390 L1024 530 L0 530Z" fill="#AACE7B" stroke="#2D2D2D" stroke-width="1.5" opacity="0.25"/>
        <polygon points="120,60 122,66 129,68 124,72 125,78 120,74 115,78 116,72 111,68 118,66" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="1.5" stroke-linejoin="round"/>
      </svg>

      <div class="pb-card card-sketch">
        <div class="card-illust">
          <svg viewBox="0 0 240 120" width="200" height="100">
            <template v-if="idx === 0">
              <circle cx="160" cy="40" r="22" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2.5"/>
              <rect x="30" y="70" width="60" height="30" rx="3" fill="#FFF" stroke="#2D2D2D" stroke-width="2.5"/>
              <ellipse cx="60" cy="105" rx="26" ry="7" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="1.5"/>
              <line x1="60" y1="75" x2="60" y2="105" stroke="#2D2D2D" stroke-width="1.5"/>
            </template>
            <template v-else-if="idx === 1">
              <path d="M40 110 Q80 55 120 110" fill="none" stroke="#AACE7B" stroke-width="3.5" stroke-linecap="round"/>
              <circle cx="70" cy="55" r="20" fill="#FFB5A0" stroke="#2D2D2D" stroke-width="2.5"/>
              <circle cx="52" cy="48" r="14" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2"/>
              <circle cx="90" cy="44" r="11" fill="#FFB5A0" stroke="#2D2D2D" stroke-width="2"/>
              <path d="M130 110 Q150 85 170 110" fill="none" stroke="#AACE7B" stroke-width="2.5" stroke-linecap="round"/>
            </template>
            <template v-else-if="idx === 2">
              <polygon points="60,24 63,38 78,40 66,49 69,63 60,55 51,63 54,49 42,40 57,38" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2" stroke-linejoin="round"/>
              <polygon points="100,16 102,24 110,26 104,31 105,39 100,34 95,39 96,31 90,26 98,24" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="1.5" stroke-linejoin="round"/>
              <polygon points="140,28 142,34 148,36 143,40 144,46 140,42 136,46 137,40 132,36 138,34" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="1.5" stroke-linejoin="round"/>
              <path d="M40 110 Q70 85 100 100 Q130 115 170 95" fill="none" stroke="#AACE7B" stroke-width="2.5" stroke-linejoin="round"/>
            </template>
            <template v-else>
              <ellipse cx="100" cy="60" rx="30" ry="24" fill="#FFF" stroke="#2D2D2D" stroke-width="2.5"/>
              <ellipse cx="100" cy="82" rx="10" ry="5" fill="#FFB300" stroke="#2D2D2D" stroke-width="2"/>
              <circle cx="92" cy="56" r="2.5" fill="#2D2D2D"/>
              <path d="M40 110 Q70 85 100 100 Q130 115 170 95" fill="none" stroke="#C0E3F5" stroke-width="3.5" stroke-linejoin="round"/>
            </template>
          </svg>
        </div>
        <h2 class="card-title">{{ poems[idx].title }}</h2>
        <p class="card-author">{{ poems[idx].author }}</p>
        <div class="card-lines">
          <p v-for="l in poems[idx].lines" :key="l" class="card-line">{{ l }}</p>
        </div>
        <div class="card-actions">
          <button class="btn-sketch"><i class="ri-play-fill"></i> 播放</button>
          <button class="btn-sketch"><i class="ri-mic-line"></i> 跟读</button>
        </div>
        <div class="card-meta">
          <span class="meta-dot" :class="{ done: true }"></span>
          <span class="meta-label">诵读 {{ idx + 1 }}/{{ poems.length }}</span>
        </div>
      </div>
    </div>

    <DankePet scene="poems" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import StatusBar from '../components/StatusBar.vue'
import DankePet from '../components/DankePet.vue'

const router = useRouter()
const idx = ref(0)
const poems = [
  { title: '静夜思', author: '唐 · 李白', lines: ['床前明月光，', '疑是地上霜。', '举头望明月，', '低头思故乡。'] },
  { title: '春晓', author: '唐 · 孟浩然', lines: ['春眠不觉晓，', '处处闻啼鸟。', '夜来风雨声，', '花落知多少。'] },
  { title: '小星星', author: '经典儿歌', lines: ['一闪一闪亮晶晶，', '满天都是小星星。', '挂在天上放光明，', '好像许多小眼睛。'] },
  { title: '咏鹅', author: '唐 · 骆宾王', lines: ['鹅，鹅，鹅，', '曲项向天歌。', '白毛浮绿水，', '红掌拨清波。'] },
]
</script>

<style scoped>
.page { width: 100%; height: 100%; display: flex; flex-direction: column; position: relative; overflow: hidden; background: var(--bg-mint); }
.nav-row { height: 48px; display: flex; align-items: center; padding: 0 var(--space-2); gap: 6px; flex-shrink: 0; position: relative; z-index: 10; }
.nav-back { width: 38px; height: 38px; border: 2.5px solid var(--ink-black); border-radius: 10px 12px 9px 11px; background: var(--bg-card); font-family: var(--font-heading); font-size: 17px; cursor: pointer; box-shadow: 2px 2px 0 var(--ink-black); display: flex; align-items: center; justify-content: center; transition: 0.12s; flex-shrink: 0; }
.nav-back:active { transform: scale(0.9); }
.nav-title { font-family: var(--font-heading); font-size: 22px; color: #3B7F8F; flex: 1; text-align: center; white-space: nowrap; min-width: 0; overflow: hidden; text-overflow: ellipsis; }
.nav-progress { font-family: var(--font-heading); font-size: 15px; color: var(--ink-muted); flex-shrink: 0; }
.nav-arrows { display: flex; gap: 4px; flex-shrink: 0; }
.nav-btn { width: 34px; height: 34px; border: 2.5px solid var(--ink-black); border-radius: 10px 12px 9px 11px; background: var(--bg-card); font-family: var(--font-heading); font-size: 16px; cursor: pointer; box-shadow: 2px 2px 0 var(--ink-black); display: flex; align-items: center; justify-content: center; transition: 0.12s; }
.nav-btn:active { transform: scale(0.9); }
.nav-btn:disabled { opacity: 0.3; cursor: default; }
.nav-home { height: 34px; padding: 0 var(--space-3); border: 2.5px solid var(--ink-black); border-radius: 12px 14px 10px 13px; background: var(--bg-card); font-family: var(--font-heading); font-size: 14px; cursor: pointer; box-shadow: 2px 2px 0 var(--ink-black); transition: 0.12s; white-space: nowrap; flex-shrink: 0; }
.nav-home:active { transform: scale(0.92); }

.content { flex: 1; display: flex; flex-direction: column; align-items: center; padding: var(--space-2) var(--space-6) var(--space-3); position: relative; z-index: 5; }
.scene-bg { position: absolute; bottom: 0; left: 0; z-index: 0; pointer-events: none; }

.pb-card { width: 440px; padding: var(--space-3) var(--space-5); display: flex; flex-direction: column; align-items: center; gap: 2px; background: var(--bg-card); position: relative; z-index: 2; margin-top: var(--space-1); }
.card-title { font-family: var(--font-heading); font-size: 22px; }
.card-author { font-family: var(--font-body); font-size: 15px; color: var(--ink-muted); }
.card-lines { margin: 2px 0; }
.card-line { font-family: var(--font-heading); font-size: 22px; line-height: 1.6; text-align: center; letter-spacing: 1px; }
.card-actions { display: flex; gap: var(--space-3); margin-top: 2px; }
.card-meta { display: flex; align-items: center; gap: var(--space-1); margin-top: 2px; }
.meta-dot { width: 8px; height: 8px; border-radius: 50%; border: 2px solid #DDD; }
.meta-dot.done { background: #AACE7B; border-color: #6B9B37; }
.meta-label { font-family: var(--font-body); font-size: 14px; color: var(--ink-muted); }
</style>
