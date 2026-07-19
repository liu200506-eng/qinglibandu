<template>
  <div class="kpi-card glass">
    <div class="kpi-head">
      <span class="kpi-ic">⚡</span>
      <span class="kpi-title">AI STATUS</span>
      <span class="kpi-trend" :class="trendClass">{{ trendText }}</span>
    </div>
    <div class="kpi-body">
      <div class="orb-mini">
        <div class="orb-mini-core" :class="`s-${ai.state}`"></div>
      </div>
      <div class="kpi-main">
        <div class="kpi-num text-gradient">{{ energyPercent }}<span class="unit">%</span></div>
        <div class="kpi-sub">ENERGY · {{ ai.state.toUpperCase() }}</div>
        <div class="mini-bar"><div class="fill" :style="{ width: ai.energy * 100 + '%' }"></div></div>
        <div class="kpi-emotion">EMOTION: {{ ai.emotion }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAIStore } from '@/stores/ai'

const ai = useAIStore()

const energyPercent = computed(() => Math.round(ai.energy * 100))
const trendClass = computed(() => {
  if (ai.energy >= 0.8) return 'up'
  if (ai.energy >= 0.5) return 'mid'
  return 'down'
})
const trendText = computed(() => {
  if (ai.state === 'thinking')  return 'THINKING'
  if (ai.state === 'processing') return 'RUNNING'
  if (ai.state === 'success')   return '✓ DONE'
  return 'IDLE'
})
</script>

<style scoped>
.kpi-card { padding: 18px 20px; grid-column: span 1; }
.kpi-head { display: flex; align-items: center; gap: 8px; font-family: ui-monospace, monospace; font-size: 11px; letter-spacing: 2px; color: #5a68a0; margin-bottom: 10px; }
.kpi-title { font-weight: 700; }
.kpi-trend { margin-left: auto; padding: 2px 8px; border-radius: 999px; font-size: 10px; }
.kpi-trend.up { background: rgba(96,255,176,.15); color: #60ffb0; border: 1px solid rgba(96,255,176,.35); }
.kpi-trend.mid { background: rgba(255,184,96,.15); color: #ffb860; border: 1px solid rgba(255,184,96,.35); }
.kpi-trend.down { background: rgba(255,111,140,.15); color: #ff6f8c; border: 1px solid rgba(255,111,140,.35); }
.kpi-body { display: flex; align-items: center; gap: 18px; }
.orb-mini { width: 54px; height: 54px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.orb-mini-core {
  width: 46px; height: 46px; border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, #6C5CE7, #00D2FF);
  box-shadow: 0 0 30px rgba(108,92,231,.45), inset 0 0 18px rgba(255,255,255,.25);
  animation: miniBreath 6s var(--ease-breath) infinite;
}
.orb-mini-core.s-processing { animation: miniWarp .9s ease-in-out infinite; }
.orb-mini-core.s-success { animation: miniSuccess 1.2s ease; }
.kpi-main { flex: 1; }
.kpi-num { font-size: 32px; font-weight: 800; letter-spacing: 1px; line-height: 1; }
.kpi-num .unit { font-size: 14px; margin-left: 2px; color: #0d9488; }
.kpi-sub { font-size: 10px; letter-spacing: 2px; color: #5a68a0; margin-top: 2px; font-family: ui-monospace, monospace; }
.mini-bar { margin-top: 8px; width: 100%; height: 5px; background: rgba(255,255,255,.08); border-radius: 999px; overflow: hidden; }
.fill { height: 100%; background: linear-gradient(90deg, #6C5CE7, #00D2FF, #60ffb0); transition: width .4s ease; }
.kpi-emotion { margin-top: 8px; font-size: 10px; letter-spacing: 1.5px; color: #0d9488; font-family: ui-monospace, monospace; }

@keyframes miniBreath {
  0%, 100% { transform: scale(1); }
  50%      { transform: scale(1.06); }
}
@keyframes miniWarp {
  0%, 100% { transform: scale(1); }
  50%      { transform: scale(1.06) rotate(2deg); filter: brightness(1.15); }
}
@keyframes miniSuccess {
  0%, 100% { box-shadow: 0 0 30px rgba(96,255,176,.3); }
  50%      { box-shadow: 0 0 60px rgba(96,255,176,.7); }
}
</style>
