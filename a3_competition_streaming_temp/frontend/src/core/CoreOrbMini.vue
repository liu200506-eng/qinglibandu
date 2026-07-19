<template>
  <div class="mini">
    <div class="mini-core"></div>
    <div class="mini-ring"></div>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.mini {
  position: relative;
  width: 34px; height: 34px;
  display: flex; align-items: center; justify-content: center;
}
.mini-core {
  width: 26px; height: 26px; border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, #6C5CE7, #00D2FF);
  box-shadow: 0 0 20px rgba(108,92,231,.5), inset 0 0 12px rgba(255,255,255,.25);
  animation: miniFloat 6s var(--ease-breath) infinite;
}
.mini-ring {
  position: absolute; inset: -2px;
  border-radius: 50%;
  border: 1px dashed rgba(180,195,255,.4);
  animation: miniRing 14s linear infinite;
}
@keyframes miniFloat {
  0%, 100% { transform: scale(1); }
  50%      { transform: scale(1.08); }
}
@keyframes miniRing {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
</style>
