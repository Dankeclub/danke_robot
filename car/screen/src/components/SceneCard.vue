<template>
  <div
    class="scene-card card-sketch"
    :class="[`scene-card--${theme}`, tiltClass, sizeClass]"
    @click="$emit('click')"
  >
    <!-- Doodle tape -->
    <svg class="doodle-tape" :class="tapeClass" viewBox="0 0 40 16" width="40" height="16">
      <rect x="2" y="1" width="36" height="14" rx="2" fill="#FFF9C4" stroke="#2D2D2D" stroke-width="1.5" opacity="0.7"/>
    </svg>

    <div class="scene-card__body">
      <!-- Icon -->
      <div class="scene-card__icon" :class="`icon--${theme}`">
        <i :class="icon"></i>
      </div>

      <div class="scene-card__text">
        <!-- Label -->
        <span class="scene-card__label">{{ label }}</span>
        <!-- Subtitle -->
        <span v-if="subtitle" class="scene-card__subtitle">{{ subtitle }}</span>
      </div>
    </div>

    <!-- Extra slot (CTA button, arrow, etc.) -->
    <slot name="extra" />

    <!-- Badge -->
    <span v-if="badge" class="scene-card__badge">{{ badge }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  theme: { type: String, default: 'task' },
  icon: { type: String, required: true },
  label: { type: String, required: true },
  subtitle: { type: String, default: '' },
  badge: { type: [String, Number], default: '' },
  tiltIndex: { type: Number, default: 0 },
  size: { type: String, default: 'default' }, // 'default' | 'wide' | 'side' | 'medium' | 'compact'
})

defineEmits(['click'])

const tiltClass = computed(() => `card-tilt-${(props.tiltIndex % 5) + 1}`)
const sizeClass = computed(() => `scene-card--${props.size}`)
const tapeClass = computed(() => {
  const rotations = ['tape-1', 'tape-2', 'tape-3']
  return rotations[props.tiltIndex % 3]
})
</script>

<style scoped>
.scene-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  width: 180px;
  height: 155px;
  cursor: pointer;
  transition: transform var(--dur-normal) var(--ease-bounce),
              box-shadow var(--dur-normal);
}
.scene-card:active {
  transform: scale(0.92) translate(3px, 3px) !important;
  box-shadow: 1px 1px 0 var(--ink-black);
}

.scene-card__body {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
}
.scene-card__text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.scene-card__icon {
  width: 64px;
  height: 64px;
  border-radius: 14px 18px 16px 12px;
  border: 2.5px solid var(--ink-black);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  box-shadow: 2px 2px 0 var(--ink-black);
  flex-shrink: 0;
}

.icon--task    { background: #FFEC8E; color: #E8960C; }
.icon--chat    { background: #C0E3F5; color: #3B82C6; }
.icon--learn   { background: #AACE7B; color: #4B7A1F; }
.icon--qa      { background: #CCE7E3; color: #5B7F9F; }
.icon--message { background: #FCF3B9; color: #E8826B; }

.scene-card__label {
  font-family: var(--font-heading);
  font-size: var(--text-base);
  font-weight: 400;
  color: var(--ink-black);
  letter-spacing: 0.5px;
}
.scene-card__subtitle {
  font-family: var(--font-body);
  font-size: var(--text-xs);
  color: var(--ink-muted);
  letter-spacing: 0.3px;
}

/* ─── Size: wide (520×228) — left column big cards ─── */
.scene-card--wide {
  width: 520px;
  height: 228px;
  flex-direction: row;
  justify-content: space-between;
  padding: var(--space-5) var(--space-6);
  gap: 0;
}
.scene-card--wide .scene-card__body {
  flex-direction: row;
  align-items: center;
  gap: var(--space-6);
}
.scene-card--wide .scene-card__text {
  align-items: flex-start;
  gap: var(--space-1);
}
.scene-card--wide .scene-card__icon {
  width: 88px;
  height: 88px;
  font-size: 46px;
}
.scene-card--wide .scene-card__label {
  font-size: 26px;
}
.scene-card--wide .scene-card__subtitle {
  font-size: var(--text-base);
}

/* ─── Size: side (320×146) — right column stacked cards ─── */
.scene-card--side {
  width: 320px;
  height: 146px;
  flex-direction: row;
  justify-content: flex-start;
  padding: var(--space-4) var(--space-5);
  gap: 0;
}
.scene-card--side .scene-card__body {
  flex-direction: row;
  align-items: center;
  gap: var(--space-5);
}
.scene-card--side .scene-card__text {
  align-items: flex-start;
  gap: 2px;
}
.scene-card--side .scene-card__icon {
  width: 60px;
  height: 60px;
  font-size: 32px;
  border-radius: 12px 15px 14px 10px;
}
.scene-card--side .scene-card__label {
  font-size: 22px;
}

/* ─── Size: medium (260×220) ─── */
.scene-card--medium {
  width: 260px;
  height: 220px;
}

/* ─── Size: compact (210×155) ─── */
.scene-card--compact {
  width: 210px;
  height: 155px;
  gap: var(--space-2);
}
.scene-card--compact .scene-card__icon {
  width: 52px;
  height: 52px;
  font-size: 26px;
  border-radius: 10px 14px 12px 9px;
}
.scene-card--compact .scene-card__label {
  font-size: var(--text-base);
}

.scene-card__badge {
  position: absolute;
  top: -6px;
  right: -6px;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: 50%;
  background: var(--marker-red);
  color: #fff;
  font-family: var(--font-heading);
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--ink-black);
  box-shadow: 1px 1px 0 var(--ink-black);
}

/* Doodle tape positions */
.doodle-tape {
  position: absolute;
  z-index: 2;
}
.tape-1 { top: -8px; left: 25%; transform: rotate(-8deg); }
.tape-2 { top: -7px; right: 20%; transform: rotate(10deg); }
.tape-3 { top: -9px; left: 35%; transform: rotate(-5deg); }

/* Tilt overrides for cards with tape */
.card-tilt-1:active, .card-tilt-2:active, .card-tilt-3:active,
.card-tilt-4:active, .card-tilt-5:active {
  transform: scale(0.92) translate(3px, 3px) !important;
}
</style>
