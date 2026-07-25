<template>
  <div class="status-bar">
    <span>{{ time }}</span>
    <span class="status-bar__icons">
      <i class="ri-wifi-line"></i>
      <i class="ri-battery-2-charge-line" style="margin-left:8px"></i>
    </span>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const time = ref('09:30')

let timer = null
onMounted(() => {
  const now = new Date()
  time.value = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0')
  timer = setInterval(() => {
    const d = new Date()
    time.value = d.getHours().toString().padStart(2, '0') + ':' + d.getMinutes().toString().padStart(2, '0')
  }, 30000)
})
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.status-bar__icons {
  color: var(--ink-muted);
  font-size: 16px;
}
</style>
