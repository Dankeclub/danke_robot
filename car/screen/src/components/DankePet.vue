<template>
  <Teleport to="body">
    <div
      class="danke-pet-wrapper"
      :class="[`pet--${visualState}`]"
      :style="wrapperStyle"
      ref="wrapperRef"
      @pointerdown="onPointerDown"
    >
      <!-- Speech Bubble -->
      <div v-if="bubbleText" class="pet-bubble">
        {{ bubbleText }}
        <svg class="bubble-tail" viewBox="0 0 20 12" width="20" height="12">
          <path d="M2 0 Q10 14 18 0" fill="#FFFFFF" stroke="#2D2D2D" stroke-width="2.5"/>
        </svg>
      </div>

      <!-- Pet SVG — 10:1 head-body, tree-stump bottom, no limbs -->
      <svg
        class="pet-svg"
        :class="{ 'is-bouncing': isBouncing }"
        viewBox="0 0 100 130" width="95" height="124"
        :style="svgStyle"
      >
        <!-- Unified body (egg head → tree-stump bottom, one continuous shape) -->
        <g :style="bodyStyle">
          <!-- Body outline: round egg head narrowing to stump base -->
          <path d="M50 8
                   C80 8 94 30 94 68
                   C94 94 86 112 74 120
                   C64 126 54 127 50 127
                   C46 127 36 126 26 120
                   C14 112 6 94 6 68
                   C6 30 20 8 50 8Z"
                fill="#FFFFFF" stroke="#2D2D2D" stroke-width="3.5"/>

          <!-- Bottom stump ring (subtle line to suggest stump base) -->
          <path d="M28 120 Q50 130 72 120" fill="none" stroke="#2D2D2D" stroke-width="1.8" stroke-linecap="round" opacity="0.35"/>

          <!-- Egg crack lines -->
          <path d="M42 18 Q46 28 43 38" fill="none" stroke="#2D2D2D" stroke-width="2" stroke-linecap="round" opacity="0.35"/>
          <path d="M60 16 Q63 26 59 34" fill="none" stroke="#2D2D2D" stroke-width="2" stroke-linecap="round" opacity="0.35"/>

          <!-- Face Area (yellow, wavy top, symmetric around x=50) -->
          <path d="M26 68
                   Q30 60 36 63
                   Q42 54 48 62
                   Q50 52 52 62
                   Q58 54 64 63
                   Q70 60 74 68
                   C77 86 72 102 50 102
                   C28 102 23 86 26 68Z"
                fill="#FADA5E" stroke="#2D2D2D" stroke-width="3"/>

          <!-- Cheek whiskers (symmetric around x=50) -->
          <line x1="18" y1="84" x2="26" y2="84" stroke="#2D2D2D" stroke-width="2" stroke-linecap="round"/>
          <line x1="16" y1="89" x2="24" y2="89" stroke="#2D2D2D" stroke-width="2" stroke-linecap="round"/>
          <line x1="82" y1="84" x2="74" y2="84" stroke="#2D2D2D" stroke-width="2" stroke-linecap="round"/>
          <line x1="84" y1="89" x2="76" y2="89" stroke="#2D2D2D" stroke-width="2" stroke-linecap="round"/>

          <!-- Blush (symmetric around x=50) -->
          <ellipse cx="35" cy="86" rx="6" ry="4" fill="#FFB5A0" opacity="0.45"/>
          <ellipse cx="65" cy="86" rx="6" ry="4" fill="#FFB5A0" opacity="0.45"/>

          <!-- Eyes (symmetric around x=50) -->
          <template v-if="visualState === 'sleeping'">
            <path d="M37 78 Q42 81 47 78" stroke="#2D2D2D" stroke-width="2.5" stroke-linecap="round" fill="none"/>
            <path d="M53 78 Q58 81 63 78" stroke="#2D2D2D" stroke-width="2.5" stroke-linecap="round" fill="none"/>
          </template>
          <template v-else-if="visualState === 'happy'">
            <path d="M34 78 L40 73 L46 78" stroke="#2D2D2D" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
            <path d="M54 78 L60 73 L66 78" stroke="#2D2D2D" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
          </template>
          <template v-else>
            <ellipse v-if="!blinking" cx="39" cy="78" rx="4.5" ry="5.5" fill="#2D2D2D"/>
            <ellipse v-else cx="39" cy="79" rx="4.5" ry="1.2" fill="#2D2D2D"/>
            <ellipse v-if="!blinking" cx="40" cy="76" rx="1.8" ry="2" fill="#fff"/>
            <ellipse v-if="!blinking" cx="61" cy="78" rx="4.5" ry="5.5" fill="#2D2D2D"/>
            <ellipse v-else cx="61" cy="79" rx="4.5" ry="1.2" fill="#2D2D2D"/>
            <ellipse v-if="!blinking" cx="62" cy="76" rx="1.8" ry="2" fill="#fff"/>
          </template>

          <!-- Mouth (centered at x=50) -->
          <template v-if="visualState === 'happy'">
            <path d="M44 95 Q50 103 56 95" stroke="#2D2D2D" stroke-width="2.5" stroke-linecap="round" fill="none"/>
          </template>
          <template v-else-if="visualState === 'talking'">
            <ellipse cx="50" cy="97" rx="6" ry="4.5" fill="#2D2D2D"/>
            <ellipse cx="50" cy="95" rx="3.5" ry="2" fill="#FADA5E"/>
          </template>
          <template v-else>
            <path d="M46 95 Q50 99 54 95" stroke="#2D2D2D" stroke-width="2" stroke-linecap="round" fill="none"/>
          </template>
        </g>
      </svg>

      <!-- Shadow -->
      <div class="pet-shadow" :class="{ 'is-bouncing': isBouncing }"></div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const props = defineProps({
  scene: { type: String, default: 'home' },
})

// ─── State ───
const visualState = ref('idle')
const bubbleText = ref('')
const blinking = ref(false)
const wrapperRef = ref(null)

// ─── Fluid animation values (updated in rAF loop) ───
const animTime = ref(0)         // running time in seconds
const bodyBobY = ref(0)         // body vertical bob
const bodyTilt = ref(0)         // body side tilt (degrees)
const petScale = ref(1)         // overall scale (breathing / bounce)

// ─── Position (pixels) ───
const posX = ref(0)
const posY = ref(0)
const velX = ref(0)             // velocity for spring physics
const velY = ref(0)

// ─── Scene → state mapping ───
function sceneToState(s) {
  const map = {
    home: 'idle', tasks: 'idle', challenge: 'idle',
    celebrate: 'happy', music: 'happy',
    chat: 'talking',
    learning: 'thinking', science: 'thinking', math: 'thinking',
    english: 'thinking', poems: 'thinking', quiz: 'thinking',
    qabox: 'thinking',
    messages: 'idle',
    idle: 'sleeping',
  }
  return map[s] || 'idle'
}

// ─── Animation loop (requestAnimationFrame) ───
let animId = null
let lastTime = 0
let blinkTimer = null
let bubbleTimer = null
let randomTiltTarget = 0
let randomTiltTimer = 0

function animLoop(timestamp) {
  if (!lastTime) lastTime = timestamp
  const dt = Math.min((timestamp - lastTime) / 1000, 0.1) // cap at 100ms
  lastTime = timestamp
  animTime.value += dt

  const t = animTime.value
  const st = visualState.value

  // Random tilt changes every 2-3 seconds during idle
  randomTiltTimer += dt
  if (st === 'idle' && randomTiltTimer > 2 + Math.random() * 1.5) {
    randomTiltTimer = 0
    randomTiltTarget = (Math.random() - 0.5) * 4 // ±2 degrees
  }

  switch (st) {
    case 'idle': {
      // Gentle breathing: sinusoidal with slight irregularity
      const breathPhase = t * 1.4
      bodyBobY.value = Math.sin(breathPhase) * 4.5 + Math.sin(breathPhase * 2.3) * 1.2
      petScale.value = 1 + Math.sin(breathPhase) * 0.025
      // Smooth tilt drift
      bodyTilt.value += (randomTiltTarget - bodyTilt.value) * 0.8 * dt
      break
    }
    case 'thinking': {
      // Rhythmic side-to-side tilt
      bodyTilt.value = Math.sin(t * 3.5) * 4.5 + Math.sin(t * 7) * 0.8
      bodyBobY.value = Math.sin(t * 1.2) * 2
      petScale.value = 1 + Math.sin(t * 2.1) * 0.015
      break
    }
    case 'happy': {
      // Quick bouncy scale oscillation, decaying
      const elapsed = t % 0.55
      const bounce = Math.exp(-elapsed * 6) * Math.sin(elapsed * 16) * 0.12
      petScale.value = 1 + bounce
      bodyBobY.value = Math.sin(t * 8) * 2 * Math.exp(-elapsed * 3)
      bodyTilt.value = Math.sin(t * 10) * 2.5 * Math.exp(-elapsed * 2)
      break
    }
    case 'talking': {
      // Subtle rapid bobs, like chatting
      bodyBobY.value = Math.sin(t * 4.5) * 2 + Math.sin(t * 8.7) * 0.8
      bodyTilt.value = Math.sin(t * 3.2) * 1.5
      petScale.value = 1 + Math.sin(t * 5) * 0.015
      break
    }
    case 'sleeping': {
      // Very slow, deep breathing
      const sp = t * 0.6
      bodyBobY.value = Math.sin(sp) * 2.5
      petScale.value = 0.97 + Math.sin(sp) * 0.02
      bodyTilt.value = Math.sin(sp * 0.5) * 0.5
      break
    }
  }

  // Apply inertia/spring physics for position
  applyInertia(dt)

  animId = requestAnimationFrame(animLoop)
}

// ─── Computed styles ───
const wrapperStyle = computed(() => ({
  left: posX.value + 'px',
  top: posY.value + 'px',
}))

const svgStyle = computed(() => ({
  transform: `scale(${petScale.value.toFixed(4)})`,
}))

const bodyStyle = computed(() => ({
  transform: `translateY(${bodyBobY.value.toFixed(2)}px) rotate(${bodyTilt.value.toFixed(3)}deg)`,
  transformOrigin: '50px 68px',
}))

// ─── Blink cycle ───
function scheduleBlink() {
  if (visualState.value === 'sleeping') return
  const delay = 1800 + Math.random() * 3500
  blinkTimer = setTimeout(() => {
    blinking.value = true
    setTimeout(() => {
      blinking.value = false
      scheduleBlink()
    }, 120)
  }, delay)
}

// ─── Greeting ───
function showGreeting() {
  const greetings = {
    home: '今天想做什么呀？选一个开始吧~',
    tasks: '加油完成今天的任务吧！',
    chat: '想聊什么我都陪你~',
    learning: '今天学点什么呢？',
    qabox: '有什么问题尽管问我！',
    messages: '有新的消息哦~',
    idle: 'zzZ...',
  }
  const msg = greetings[props.scene]
  if (msg) {
    bubbleText.value = msg
    clearTimeout(bubbleTimer)
    bubbleTimer = setTimeout(() => { bubbleText.value = '' }, 4500)
  }
}

// ─── CSS bounce eligibility ───
const isBouncing = computed(() => {
  return (visualState.value === 'idle' || visualState.value === 'thinking') && !dragging
})

// ─── Double-click detection ───
let lastClickTime = 0
let clickCount = 0

// ─── Drag with spring physics ───
let dragging = false
let dragStartX = 0, dragStartY = 0
let dragInitX = 0, dragInitY = 0
let dragVelX = 0, dragVelY = 0
let lastDragX = 0, lastDragY = 0
let lastDragTime = 0
let dragMoved = false  // track if pointer moved enough to count as drag

function clampX(x) { return Math.max(-30, Math.min(1024 - 70, x)) }
function clampY(y) { return Math.max(-20, Math.min(600 - 110, y)) }

function onPointerDown(e) {
  dragging = true
  dragMoved = false
  dragStartX = e.clientX
  dragStartY = e.clientY
  dragInitX = posX.value
  dragInitY = posY.value
  lastDragX = e.clientX
  lastDragY = e.clientY
  lastDragTime = performance.now()
  dragVelX = 0; dragVelY = 0
  visualState.value = 'happy'
  if (wrapperRef.value) wrapperRef.value.setPointerCapture(e.pointerId)
  e.preventDefault()
}

function onPointerMove(e) {
  if (!dragging) return
  const now = performance.now()
  const dt = Math.max(now - lastDragTime, 1)
  dragVelX = (e.clientX - lastDragX) / dt * 16 // px per frame
  dragVelY = (e.clientY - lastDragY) / dt * 16
  lastDragX = e.clientX
  lastDragY = e.clientY
  lastDragTime = now

  const dx = e.clientX - dragStartX
  const dy = e.clientY - dragStartY
  if (Math.abs(dx) > 4 || Math.abs(dy) > 4) dragMoved = true
  posX.value = clampX(dragInitX + dx)
  posY.value = clampY(dragInitY + dy)
}

function onPointerUp() {
  if (!dragging) return
  const now = performance.now()
  const wasDrag = dragMoved
  dragging = false

  if (!wasDrag) {
    // It's a click — check for double-click
    if (now - lastClickTime < 500) {
      clickCount++
      if (clickCount >= 2) {
        // Double-click detected → navigate to chat
        clickCount = 0
        lastClickTime = 0
        router.push('/chat')
        return
      }
    } else {
      clickCount = 1
    }
    lastClickTime = now
  } else {
    clickCount = 0
  }

  // Apply velocity for inertia
  velX.value = dragVelX * 0.6
  velY.value = dragVelY * 0.6
  visualState.value = sceneToState(props.scene)
}

// Inertia physics — decelerate to stop, no spring-back
function applyInertia(dt) {
  if (dragging) return
  const friction = 0.85

  posX.value = clampX(posX.value + velX.value)
  posY.value = clampY(posY.value + velY.value)

  velX.value *= friction
  velY.value *= friction

  // Clamp near-zero
  if (Math.abs(velX.value) < 0.05) velX.value = 0
  if (Math.abs(velY.value) < 0.05) velY.value = 0
}

// ─── Lifecycle ───
onMounted(() => {
  posX.value = 1024 - 140
  posY.value = 600 - 170
  visualState.value = sceneToState(props.scene)

  lastTime = performance.now()
  animId = requestAnimationFrame(animLoop)

  scheduleBlink()
  setTimeout(showGreeting, 1200)

  document.addEventListener('pointermove', onPointerMove)
  document.addEventListener('pointerup', onPointerUp)
})

onUnmounted(() => {
  cancelAnimationFrame(animId)
  clearTimeout(blinkTimer)
  clearTimeout(bubbleTimer)
  document.removeEventListener('pointermove', onPointerMove)
  document.removeEventListener('pointerup', onPointerUp)
})

// Watch scene changes
watch(() => props.scene, (newScene) => {
  visualState.value = sceneToState(newScene)
  randomTiltTimer = 0
  showGreeting()
})
</script>

<style scoped>
.danke-pet-wrapper {
  position: fixed;
  z-index: 100;
  width: 95px;
  height: 124px;
  cursor: grab;
  will-change: left, top;
  touch-action: none;
}

.danke-pet-wrapper:active {
  cursor: grabbing;
}

.pet-svg {
  width: 95px;
  height: 124px;
  filter: drop-shadow(2px 3px 0 rgba(45, 45, 45, 0.2));
  will-change: transform;
}

/* Bubble */
.pet-bubble {
  position: absolute;
  bottom: 132px;
  left: 50%;
  transform: translateX(-50%);
  max-width: 220px;
  padding: 10px 14px;
  background: #FFFFFF;
  border: 2.5px solid #2D2D2D;
  border-radius: 16px 18px 14px 20px;
  box-shadow: 3px 3px 0 rgba(45,45,45,0.15);
  font-family: var(--font-body);
  font-size: 15px;
  color: #2D2D2D;
  text-align: center;
  line-height: 1.4;
  animation: bubblePop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.bubble-tail {
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
}

@keyframes bubblePop {
  0% { opacity: 0; transform: translateX(-50%) scale(0.7); }
  100% { opacity: 1; transform: translateX(-50%) scale(1); }
}

/* ─── CSS Bounce Animation ─── */
.pet-svg.is-bouncing {
  animation: petBounce 2.4s ease-in-out infinite;
}

@keyframes petBounce {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  18%      { transform: translateY(-16px) rotate(-2deg); }
  36%      { transform: translateY(-6px) rotate(1deg); }
  54%      { transform: translateY(-20px) rotate(-3deg); }
  72%      { transform: translateY(-8px) rotate(2deg); }
  88%      { transform: translateY(-2px) rotate(-0.5deg); }
}

.pet-shadow {
  position: absolute;
  bottom: -6px;
  left: 50%;
  width: 50px;
  height: 8px;
  margin-left: -25px;
  background: radial-gradient(ellipse, rgba(45,45,45,0.25) 0%, transparent 70%);
  border-radius: 50%;
}

.pet-shadow.is-bouncing {
  animation: shadowPulse 2.4s ease-in-out infinite;
}

@keyframes shadowPulse {
  0%, 100% { transform: scaleX(1); opacity: 0.3; }
  18%      { transform: scaleX(0.7); opacity: 0.15; }
  54%      { transform: scaleX(0.55); opacity: 0.08; }
  88%      { transform: scaleX(0.9); opacity: 0.25; }
}

@media (prefers-reduced-motion: reduce) {
  .pet-svg.is-bouncing,
  .pet-shadow.is-bouncing {
    animation: none;
  }
}
</style>
