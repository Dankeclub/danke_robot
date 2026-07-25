<template>
  <div class="idle-page" @click="wakeUp">
    <div v-for="s in stars" :key="s.key" class="idle-star" :style="s.style"></div>
    <svg class="idle-moon" viewBox="0 0 80 80" width="90" height="90">
      <circle cx="40" cy="40" r="30" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2.5"/>
      <circle cx="54" cy="35" r="22" fill="#1a1a2e"/>
    </svg>
    <div class="idle-center">
      <div class="zzz" :class="{ 'zzz--hidden': waking }"><span>z</span><span>Z</span><span>z</span></div>
      <div class="wake-bubble" :class="{ 'wake-bubble--show': waking }">
        唔哇~ 你醒啦！<br>等你好久啦，咱们快去大厅玩吧！
        <svg class="wake-bubble-tail" viewBox="0 0 20 12" width="20" height="12"><path d="M2 0 Q10 14 18 0" fill="#FFFFFF" stroke="#2D2D2D" stroke-width="2"/></svg>
      </div>
      <DankePet scene="idle" />
    </div>
    <div class="idle-hint" :class="{ 'idle-hint--hidden': waking }">轻轻触碰屏幕唤醒蛋仔…</div>
    <!-- Decorative stars on ground -->
    <div class="ground-stars">
      <span v-for="i in 10" :key="i" class="gstar" :style="{ left: (i*90 + Math.random()*60) + 'px', bottom: (20 + Math.random()*50) + 'px', animationDelay: (i*0.3) + 's', opacity: 0.15 + Math.random()*0.15 }"></span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import DankePet from '../components/DankePet.vue'
const router = useRouter(); const waking = ref(false)
const stars = Array.from({ length: 12 }, (_, i) => ({ key: i, style: { top: (15 + Math.random()*200)+'px', left: (40+Math.random()*900)+'px', width: (2+Math.random()*4)+'px', height: (2+Math.random()*4)+'px', animationDelay: (Math.random()*2)+'s', animationDuration: (1.5+Math.random()*2)+'s' } }))
function wakeUp() { if (waking.value) return; waking.value = true; setTimeout(() => router.push('/'), 1800) }
</script>

<style scoped>
.idle-page { width: 100%; height: 100%; background: linear-gradient(180deg, #1a1a2e 0%, #2d2d5e 100%); position: relative; cursor: pointer; overflow: hidden; }
.idle-star { position: absolute; border-radius: 50%; background: #fff; animation: twink 2s ease-in-out infinite alternate; }
@keyframes twink { from { opacity: 0.2; transform: scale(0.8); } to { opacity: 1; transform: scale(1.3); } }
.idle-moon { position: absolute; top: 40px; right: 120px; opacity: 0.85; }
.idle-center { position: absolute; top: 32%; left: 50%; transform: translateX(-50%); display: flex; flex-direction: column; align-items: center; }
.zzz { position: absolute; top: -70px; right: -40px; display: flex; gap: 4px; font-family: var(--font-heading); font-weight: 700; }
.zzz span { display: inline-block; animation: floatZ 2.5s ease-in infinite; color: rgba(255,255,255,0.5); }
.zzz span:nth-child(1) { font-size: 20px; } .zzz span:nth-child(2) { font-size: 28px; animation-delay: 0.4s; } .zzz span:nth-child(3) { font-size: 34px; animation-delay: 0.8s; }
@keyframes floatZ { 0% { opacity: 0; transform: translateY(8px); } 30% { opacity: 1; } 70% { opacity: 1; } 100% { opacity: 0; transform: translateY(-18px); } }
.zzz--hidden span { animation: none; opacity: 0; }
.wake-bubble { position: absolute; top: -110px; left: 50%; transform: translateX(-50%) scale(0.8); width: 320px; padding: var(--space-4) var(--space-5); background: white; border: 2.5px solid var(--ink-black); border-radius: 18px 20px 16px 22px; box-shadow: 4px 4px 0 rgba(0,0,0,0.3); font-family: var(--font-body); font-size: 18px; text-align: center; opacity: 0; transition: 0.4s; z-index: 10; line-height: 1.5; }
.wake-bubble--show { opacity: 1; transform: translateX(-50%) scale(1); }
.wake-bubble-tail { position: absolute; bottom: -10px; left: 50%; transform: translateX(-50%); }
.idle-hint { position: absolute; bottom: 70px; left: 50%; transform: translateX(-50%); font-family: var(--font-body); font-size: 16px; color: rgba(255,255,255,0.3); letter-spacing: 2px; animation: pulse 2.5s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 0.25; } 50% { opacity: 0.55; } }
.idle-hint--hidden { display: none; }
.gstar { position: absolute; width: 3px; height: 3px; background: #fff; border-radius: 50%; animation: twink 3s ease-in-out infinite alternate; }
</style>
