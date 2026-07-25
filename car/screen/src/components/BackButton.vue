<template>
  <button class="back-btn" @click="$router.back()">
    <i class="ri-arrow-left-s-line"></i>
  </button>
</template>

<style scoped>
.back-btn {
  width: 44px; height: 44px;
  display: flex; align-items: center; justify-content: center;
  border: 2.5px solid var(--ink-black);
  background: var(--bg-card);
  border-radius: 14px 16px 12px 18px;
  cursor: pointer;
  color: var(--ink-black);
  font-size: 26px;
  box-shadow: 2px 2px 0 var(--ink-black);
  transition: transform 0.12s var(--ease-bounce), box-shadow 0.12s;
  filter: url(#hand-drawn);
}
.back-btn:active {
  transform: scale(0.9) translate(1px, 1px);
  box-shadow: 0.5px 0.5px 0 var(--ink-black);
}
</style>
