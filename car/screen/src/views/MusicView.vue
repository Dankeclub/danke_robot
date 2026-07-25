<template>
  <div class="page">
    <StatusBar />
    <div class="nav-row">
      <button class="nav-back" @click="router.back()">←</button>
      <span class="nav-title">音乐律动</span>
      <span class="nav-progress">{{ idx + 1 }}/{{ songs.length }}</span>
      <div class="nav-arrows">
        <button class="nav-btn" :disabled="idx === 0" @click="idx--">◀</button>
        <button class="nav-btn" :disabled="idx === songs.length - 1" @click="idx++">▶</button>
      </div>
      <button class="nav-home" @click="router.push('/')">首页</button>
    </div>

    <div class="content scroll-y">
      <svg class="scene-bg" viewBox="0 0 1024 480" width="1024" height="480" preserveAspectRatio="none">
        <circle cx="120" cy="360" rx="8" ry="6" fill="#6B5CE7" stroke="#2D2D2D" stroke-width="2"/><line x1="128" y1="360" x2="128" y2="335" stroke="#2D2D2D" stroke-width="2"/>
        <circle cx="300" cy="320" rx="7" ry="5" fill="#AACE7B" stroke="#2D2D2D" stroke-width="1.5"/><line x1="307" y1="320" x2="307" y2="298" stroke="#2D2D2D" stroke-width="1.5"/>
        <circle cx="550" cy="370" rx="8" ry="6" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2"/><line x1="558" y1="370" x2="558" y2="345" stroke="#2D2D2D" stroke-width="2"/>
        <circle cx="780" cy="330" rx="7" ry="5" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="1.5"/><line x1="787" y1="330" x2="787" y2="308" stroke="#2D2D2D" stroke-width="1.5"/>
        <path d="M30 260 Q80 255 140 260 Q200 265 260 260 Q320 255 380 260 Q440 265 500 260 Q560 255 620 260 Q680 265 740 260 Q800 255 860 260 Q920 265 980 260" fill="none" stroke="#6B5CE7" stroke-width="1.2" opacity="0.2"/>
        <path d="M30 280 Q80 275 140 280 Q200 285 260 280 Q320 275 380 280 Q440 285 500 280 Q560 275 620 280 Q680 285 740 280 Q800 275 860 280 Q920 285 980 280" fill="none" stroke="#6B5CE7" stroke-width="1.2" opacity="0.15"/>
        <path d="M0 440 Q200 390 400 430 Q600 460 800 420 Q950 400 1024 425 L1024 500 L0 500Z" fill="#AACE7B" stroke="#2D2D2D" stroke-width="1.5" opacity="0.25"/>
        <polygon points="200,40 203,48 212,50 205,55 207,63 200,58 193,63 195,55 188,50 197,48" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="1.5" stroke-linejoin="round"/>
      </svg>

      <div class="pb-card card-sketch">
        <div class="card-illust">
          <svg viewBox="0 0 240 160" width="260" height="173">
            <template v-if="idx === 0"><polygon points="50,35 55,58 76,61 60,74 64,96 50,83 36,96 40,74 24,61 45,58" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="3" stroke-linejoin="round"/><text x="120" y="85" font-size="18" font-family="ZCOOL KuaiLe" fill="#2D2D2D">颗颗闪亮</text></template>
            <template v-else-if="idx === 1"><ellipse cx="120" cy="70" rx="50" ry="32" fill="#FFF" stroke="#2D2D2D" stroke-width="3"/><circle cx="108" cy="63" r="4" fill="#2D2D2D"/><circle cx="132" cy="63" r="4" fill="#2D2D2D"/><ellipse cx="120" cy="100" rx="18" ry="7" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="2"/></template>
            <template v-else-if="idx === 2"><path d="M60 115 Q100 55 140 115" fill="none" stroke="#2D2D2D" stroke-width="3"/><path d="M90 80 Q130 35 170 80" fill="none" stroke="#2D2D2D" stroke-width="3"/><path d="M140 115 Q180 70 220 115" fill="none" stroke="#2D2D2D" stroke-width="3"/><text x="140" y="145" font-size="16" font-family="ZCOOL KuaiLe" fill="#2D2D2D" text-anchor="middle">燕子归来</text></template>
            <template v-else-if="idx === 3"><ellipse cx="75" cy="85" rx="30" ry="36" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="3"/><ellipse cx="75" cy="118" rx="18" ry="8" fill="#FFB5A0" stroke="#2D2D2D" stroke-width="2"/><ellipse cx="165" cy="85" rx="30" ry="36" fill="#FCF3B9" stroke="#2D2D2D" stroke-width="3"/><ellipse cx="165" cy="118" rx="18" ry="8" fill="#FFB5A0" stroke="#2D2D2D" stroke-width="2"/><text x="120" y="145" font-size="16" font-family="ZCOOL KuaiLe" fill="#2D2D2D" text-anchor="middle">两只老虎</text></template>
            <template v-else-if="idx === 4"><ellipse cx="120" cy="70" rx="48" ry="42" fill="#C0A070" stroke="#2D2D2D" stroke-width="3"/><line x1="120" y1="63" x2="120" y2="42" stroke="#2D2D2D" stroke-width="3.5"/><ellipse cx="120" cy="52" rx="24" ry="11" fill="#AACE7B" stroke="#2D2D2D" stroke-width="2"/><circle cx="108" cy="65" r="3.5" fill="#2D2D2D"/><circle cx="132" cy="65" r="3.5" fill="#2D2D2D"/><text x="120" y="130" font-size="16" font-family="ZCOOL KuaiLe" fill="#2D2D2D" text-anchor="middle">嘿哟嘿哟</text></template>
            <template v-else><circle cx="120" cy="70" r="42" fill="#FFF" stroke="#2D2D2D" stroke-width="3"/><ellipse cx="95" cy="62" rx="14" ry="22" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2"/><ellipse cx="145" cy="62" rx="14" ry="22" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2"/><circle cx="112" cy="72" r="3.5" fill="#2D2D2D"/><circle cx="128" cy="72" r="3.5" fill="#2D2D2D"/><text x="120" y="130" font-size="16" font-family="ZCOOL KuaiLe" fill="#2D2D2D" text-anchor="middle">乖乖开门</text></template>
          </svg>
        </div>
        <h2 class="card-title">{{ songs[idx].title }}</h2>
        <p class="card-artist">{{ songs[idx].artist }}</p>
        <div class="card-bar"><div class="card-progress" :style="{ width: ((idx + 1) / songs.length * 100) + '%' }"></div></div>
        <div class="card-actions">
          <button class="btn-sketch" style="height:44px;padding:0 16px" @click="idx = Math.max(0, idx - 1)"><i class="ri-skip-back-fill"></i></button>
          <button class="btn-sketch btn-play"><i class="ri-play-fill"></i></button>
          <button class="btn-sketch" style="height:44px;padding:0 16px" @click="idx = Math.min(songs.length - 1, idx + 1)"><i class="ri-skip-forward-fill"></i></button>
        </div>
        <div class="card-meta">
          <svg v-for="n in 3" :key="n" viewBox="0 0 30 30" width="22" height="22"><path d="M15 3 L18 11 L26 13 L19 19 L21 27 L15 23 L9 27 L11 19 L4 13 L12 11Z" :fill="n <= Math.ceil((idx + 1) / 2) ? '#FFB300' : '#DDD'" stroke="#2D2D2D" stroke-width="1.5" stroke-linejoin="round"/></svg>
        </div>
      </div>
    </div>

    <DankePet scene="music" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import StatusBar from '../components/StatusBar.vue'
import DankePet from '../components/DankePet.vue'

const router = useRouter()
const idx = ref(0)
const songs = [
  { title: '小星星', artist: '经典儿歌' },
  { title: '玛丽有只小羊羔', artist: '英文儿歌' },
  { title: '小燕子', artist: '经典儿歌' },
  { title: '两只老虎', artist: '中文儿歌' },
  { title: '拔萝卜', artist: '经典儿歌' },
  { title: '小兔子乖乖', artist: '中文儿歌' },
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

.pb-card { width: 500px; padding: var(--space-5) var(--space-6); display: flex; flex-direction: column; align-items: center; gap: var(--space-2); background: var(--bg-card); position: relative; z-index: 2; margin-top: var(--space-1); }
.card-illust { margin-bottom: 4px; }
.card-title { font-family: var(--font-heading); font-size: 28px; }
.card-artist { font-family: var(--font-body); font-size: var(--text-lg); color: var(--ink-muted); }
.card-bar { width: 80%; height: 12px; background: #E8E0F0; border: 2.5px solid var(--ink-black); border-radius: 8px; overflow: hidden; margin-top: 4px; }
.card-progress { height: 100%; background: #6B5CE7; border-radius: 6px; }
.card-actions { display: flex; align-items: center; gap: var(--space-4); margin-top: 6px; }
.btn-play { background: #6B5CE7; color: #fff; width: 56px; height: 56px; border-radius: 50%; font-size: 26px; }
.card-meta { display: flex; gap: 3px; margin-top: 4px; }
</style>
