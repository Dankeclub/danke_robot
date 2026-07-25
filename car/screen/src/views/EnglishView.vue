<template>
  <div class="page">
    <StatusBar />
    <div class="nav-row">
      <button class="nav-back" @click="router.back()">←</button>
      <span class="nav-title">英语乐园</span>
      <span class="nav-progress">{{ idx + 1 }}/{{ words.length }}</span>
      <div class="nav-arrows">
        <button class="nav-btn" :disabled="idx === 0" @click="idx--">◀</button>
        <button class="nav-btn" :disabled="idx === words.length - 1" @click="idx++">▶</button>
      </div>
      <button class="nav-home" @click="router.push('/')">首页</button>
    </div>

    <div class="content scroll-y">
      <svg class="scene-bg" viewBox="0 0 1024 500" width="1024" height="500" preserveAspectRatio="none">
        <rect x="60" y="430" width="44" height="52" rx="4" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2"/><text x="82" y="462" font-size="20" font-family="ZCOOL KuaiLe" text-anchor="middle">A</text>
        <rect x="270" y="415" width="44" height="68" rx="4" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="2"/><text x="292" y="457" font-size="20" font-family="ZCOOL KuaiLe" text-anchor="middle">B</text>
        <rect x="900" y="405" width="44" height="78" rx="4" fill="#C0E3F5" stroke="#2D2D2D" stroke-width="2"/><text x="922" y="452" font-size="20" font-family="ZCOOL KuaiLe" text-anchor="middle">D</text>
        <path d="M0 420 Q200 380 400 415 Q600 440 800 410 Q950 395 1024 415 L1024 500 L0 500Z" fill="#AACE7B" stroke="#2D2D2D" stroke-width="1.5" opacity="0.3"/>
        <polygon points="180,40 183,48 192,50 185,55 187,63 180,58 173,63 175,55 168,50 177,48" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="1.5" stroke-linejoin="round"/>
        <path d="M500 40 Q510 28 520 34 Q516 18 532 22 Q538 8 550 18 Q560 8 570 22 Q586 18 584 34 Q594 28 590 40 Q580 44 500 40Z" fill="#fff" stroke="#2D2D2D" stroke-width="1.5" opacity="0.5"/>
      </svg>

      <div class="pb-card card-sketch">
        <div class="card-illust">
          <svg viewBox="0 0 220 140" width="210" height="130">
            <template v-if="idx === 0">
              <ellipse cx="85" cy="75" rx="42" ry="38" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="2.5"/><ellipse cx="85" cy="135" rx="20" ry="6" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="1.5"/><ellipse cx="85" cy="125" rx="25" ry="12" fill="#CCE7E3" stroke="#2D2D2D" stroke-width="2"/>
              <line x1="55" y1="50" x2="30" y2="35" stroke="#2D2D2D" stroke-width="2.5"/><line x1="72" y1="45" x2="78" y2="25" stroke="#2D2D2D" stroke-width="2.5"/>
            </template>
            <template v-else-if="idx === 1">
              <ellipse cx="55" cy="75" rx="26" ry="34" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="2.5" transform="rotate(-12 55 75)"/>
              <ellipse cx="125" cy="75" rx="26" ry="34" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2.5" transform="rotate(12 125 75)"/>
              <line x1="55" y1="40" x2="125" y2="40" stroke="#2D2D2D" stroke-width="1.5"/>
            </template>
            <template v-else-if="idx === 2">
              <circle cx="75" cy="70" r="35" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2.5"/>
              <line x1="75" y1="22" x2="75" y2="12"/><line x1="75" y1="118" x2="75" y2="128"/>
              <line x1="28" y1="70" x2="18" y2="70"/><line x1="122" y1="70" x2="132" y2="70"/>
              <line x1="42" y1="37" x2="35" y2="30"/><line x1="108" y1="37" x2="115" y2="30"/>
            </template>
            <template v-else-if="idx === 3">
              <path d="M45 115 Q60 60 95 50 Q130 42 145 75" fill="none" stroke="#AACE7B" stroke-width="4" stroke-linecap="round"/>
              <rect x="80" y="42" width="38" height="30" rx="3" fill="#C0A070" stroke="#2D2D2D" stroke-width="2"/>
              <rect x="120" y="38" width="38" height="34" rx="3" fill="#C0A070" stroke="#2D2D2D" stroke-width="2"/>
              <ellipse cx="70" cy="95" rx="14" ry="18" fill="#FFB5A0" stroke="#2D2D2D" stroke-width="1.5"/>
            </template>
            <template v-else>
              <path d="M30 60 Q60 25 95 45 Q130 20 155 45 Q175 25 195 50" fill="none" stroke="#F97316" stroke-width="4"/><path d="M30 60 Q60 45 95 65 Q130 40 155 65 Q175 45 195 70" fill="none" stroke="#FFEC8E" stroke-width="3.5"/><path d="M30 60 Q60 65 95 85 Q130 60 155 85 Q175 65 195 90" fill="none" stroke="#AACE7B" stroke-width="3.5"/><path d="M30 60 Q60 85 95 105 Q130 80 155 105 Q175 85 195 110" fill="none" stroke="#C0E3F5" stroke-width="3.5"/>
            </template>
          </svg>
        </div>
        <div class="eng-word">{{ words[idx].en }}</div>
        <div class="eng-phonetic">{{ words[idx].phonetic }}</div>
        <div class="eng-cn">{{ words[idx].cn }}</div>
        <div class="eng-example">"{{ words[idx].example }}"</div>
        <button class="btn-sketch btn-play">播放发音</button>
        <div class="card-meta">
          <span class="meta-label">已学 {{ idx + 1 }} / {{ words.length }} 词</span>
        </div>
      </div>
    </div>

    <DankePet scene="english" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import StatusBar from '../components/StatusBar.vue'
import DankePet from '../components/DankePet.vue'

const router = useRouter()
const idx = ref(0)
const words = [
  { en: 'elephant', cn: '大象', phonetic: '/ˈel.ɪ.fənt/', example: 'The elephant is very big and strong.' },
  { en: 'butterfly', cn: '蝴蝶', phonetic: '/ˈbʌt.ɚ.flaɪ/', example: 'A beautiful butterfly can fly high.' },
  { en: 'sunshine', cn: '阳光', phonetic: '/ˈsʌn.ʃaɪn/', example: 'I love playing in the warm sunshine.' },
  { en: 'adventure', cn: '冒险', phonetic: '/ədˈven.tʃɚ/', example: 'Let\'s go on a fun adventure together!' },
  { en: 'rainbow', cn: '彩虹', phonetic: '/ˈreɪn.boʊ/', example: 'After the rain, we saw a rainbow.' },
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

.pb-card { width: 460px; padding: var(--space-3) var(--space-5); display: flex; flex-direction: column; align-items: center; gap: 2px; background: var(--bg-card); position: relative; z-index: 2; margin-top: var(--space-1); }
.card-illust { margin-bottom: 2px; }
.eng-word { font-family: var(--font-heading); font-size: 30px; color: #2D6DA1; letter-spacing: 1px; }
.eng-phonetic { font-family: var(--font-body); font-size: var(--text-sm); color: var(--ink-muted); }
.eng-cn { font-family: var(--font-heading); font-size: var(--text-lg); }
.eng-example { font-family: var(--font-body); font-size: 15px; color: var(--ink-brown); font-style: italic; padding: var(--space-1) var(--space-3); background: #F0F8FF; border-radius: 8px; }
.btn-play { background: #3B82C6; color: #fff; font-size: 14px; height: 38px; padding: 0 18px; }
.card-meta { margin-top: 2px; }
.meta-label { font-family: var(--font-body); font-size: 14px; color: var(--ink-muted); }
</style>
