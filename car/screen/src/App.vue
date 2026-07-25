<template>
  <!-- SVG Hand-drawn Filter Definition -->
  <svg style="position:absolute;width:0;height:0" aria-hidden="true">
    <defs>
      <filter id="hand-drawn" x="-2%" y="-2%" width="104%" height="104%">
        <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="3" result="noise" seed="2"/>
        <feDisplacementMap in="SourceGraphic" in2="noise" scale="2" xChannelSelector="R" yChannelSelector="G"/>
      </filter>
      <filter id="hand-drawn-more" x="-2%" y="-2%" width="104%" height="104%">
        <feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="4" result="noise" seed="5"/>
        <feDisplacementMap in="SourceGraphic" in2="noise" scale="3" xChannelSelector="R" yChannelSelector="G"/>
      </filter>
    </defs>
  </svg>

  <router-view v-slot="{ Component }">
    <component :is="Component" />
  </router-view>
  <AlertPopup />
</template>

<script setup>
import AlertPopup from './components/AlertPopup.vue'
</script>

<style>
#app { width: 100%; height: 100%; }
.card-sketch, .btn-sketch {
  filter: url(#hand-drawn);
}
</style>
