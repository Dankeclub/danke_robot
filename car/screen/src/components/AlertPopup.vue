<template>
  <Teleport to="body">
    <Transition name="alert">
      <div v-if="visible" class="alert-overlay">
        <div class="alert-card card-sketch">
          <!-- Egg character -->
          <div class="alert-pet">
            <svg viewBox="0 0 100 100" width="80" height="80">
              <!-- Body -->
              <ellipse cx="50" cy="55" rx="36" ry="42" fill="#FFFFFF" stroke="#2D2D2D" stroke-width="3"/>
              <!-- Face -->
              <path d="M25 58 Q30 52 36 55 Q42 48 48 54 Q50 46 52 54 Q58 48 64 55 Q70 52 75 58 Q77 72 64 80 Q50 85 36 80 Q23 72 25 58Z" fill="#FADA5E" stroke="#2D2D2D" stroke-width="2.5"/>
              <!-- Eyes: worried -->
              <template v-if="type === 'posture'">
                <path d="M33 66 L43 63" stroke="#2D2D2D" stroke-width="2.5" stroke-linecap="round"/>
                <path d="M67 66 L57 63" stroke="#2D2D2D" stroke-width="2.5" stroke-linecap="round"/>
              </template>
              <!-- Eyes: normal/worried -->
              <template v-else>
                <ellipse cx="38" cy="66" rx="4" ry="5" fill="#2D2D2D"/>
                <ellipse cx="62" cy="66" rx="4" ry="5" fill="#2D2D2D"/>
                <ellipse cx="39" cy="64" rx="1.5" ry="1.8" fill="#fff"/>
                <ellipse cx="63" cy="64" rx="1.5" ry="1.8" fill="#fff"/>
              </template>
              <!-- Mouth: worried / o-shape -->
              <template v-if="type === 'posture'">
                <ellipse cx="50" cy="78" rx="5" ry="4" fill="#2D2D2D"/>
              </template>
              <template v-else>
                <ellipse cx="50" cy="78" rx="6" ry="3.5" fill="#2D2D2D"/>
              </template>
              <!-- Blush -->
              <ellipse cx="32" cy="74" rx="5" ry="3" fill="#FFB5A0" opacity="0.4"/>
              <ellipse cx="68" cy="74" rx="5" ry="3" fill="#FFB5A0" opacity="0.4"/>
              <!-- Exclamation mark -->
              <circle cx="12" cy="24" r="12" fill="#FFEC8E" stroke="#2D2D2D" stroke-width="2.5"/>
              <text x="12" y="30" text-anchor="middle" font-size="16" font-weight="700" fill="#2D2D2D" font-family="sans-serif">!</text>
            </svg>
          </div>

          <!-- Message -->
          <div class="alert-msg">{{ message }}</div>

          <!-- Button -->
          <button class="alert-btn btn-sketch btn-sketch--primary" @click="dismiss">
            {{ type === 'posture' ? '马上坐好！' : '我知道了！' }}
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { useAlertPopup } from '../utils/alert-popup.js'

const { state, dismiss } = useAlertPopup()

const visible = computed(() => state.visible)
const type = computed(() => state.type)
const message = computed(() => state.message)
</script>

<style scoped>
.alert-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(45, 45, 45, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(2px);
}

.alert-card {
  width: 340px;
  padding: 36px 28px 28px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  background: #FFFEF9;
  border-radius: 24px 20px 28px 22px;
}

.alert-pet {
  width: 80px;
  height: 80px;
  animation: alert-bob 0.6s ease-in-out infinite alternate;
}

@keyframes alert-bob {
  0% { transform: translateY(0); }
  100% { transform: translateY(-6px); }
}

.alert-msg {
  font-family: var(--font-body);
  font-size: 18px;
  color: var(--ink-black);
  text-align: center;
  line-height: 1.6;
  padding: 0 8px;
}

.alert-btn {
  margin-top: 4px;
}

/* Transition */
.alert-enter-active { transition: 0.25s ease-out; }
.alert-leave-active { transition: 0.2s ease-in; }
.alert-enter-from { opacity: 0; }
.alert-leave-to { opacity: 0; }
.alert-enter-from .alert-card { transform: scale(0.8) translateY(20px); }
.alert-leave-to .alert-card { transform: scale(0.9); }
.alert-enter-active .alert-card { transition: 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.alert-leave-active .alert-card { transition: 0.15s ease-in; }
</style>
