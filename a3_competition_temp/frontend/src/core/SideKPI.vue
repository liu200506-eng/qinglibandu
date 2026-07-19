<template>
  <div class="kpi-card glass" style="grid-column: span 1;">
    <div class="card-head">
      <span class="ic">📊</span>
      <span class="title">{{ title }}</span>
    </div>
    <div class="kpi-row">
      <div class="ring-wrap">
        <div class="ring">
          <svg viewBox="0 0 36 36" class="circular-chart">
            <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
            <path class="circle" :stroke="color" :stroke-dasharray="`${value} 100`" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
          </svg>
          <span class="ring-num">{{ value }}<span class="ring-unit">{{ unit }}</span></span>
        </div>
      </div>
      <div class="kpi-foot">
        <span class="sub">当前水平</span>
        <span class="hint" :class="hintClass">{{ hint }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  title: string
  value: number
  unit?: string
  color?: string
}>()

const hint = computed(() => {
  if (props.value >= 80) return '优秀，继续保持'
  if (props.value >= 60) return '良好，还可提升'
  if (props.value >= 40) return '一般，建议加强'
  return '薄弱，优先练习'
})
const hintClass = computed(() => {
  if (props.value >= 80) return 'good'
  if (props.value >= 60) return 'ok'
  if (props.value >= 40) return 'warn'
  return 'bad'
})
</script>

<style scoped>
.kpi-card { padding: 18px 20px; }
.card-head { display: flex; align-items: center; gap: 8px; font-family: ui-monospace, monospace; font-size: 11px; letter-spacing: 2px; color: #5a68a0; margin-bottom: 10px; }
.card-head .title { font-weight: 700; color: #0d9488; }

.kpi-row { display: flex; align-items: center; gap: 16px; }
.ring-wrap { display: flex; justify-content: center; flex-shrink: 0; }
.ring { position: relative; width: 84px; height: 84px; }
.circular-chart { display: block; width: 100%; height: 100%; }
.circle-bg { fill: none; stroke: rgba(255,255,255,.08); stroke-width: 3; }
.circle { fill: none; stroke-width: 3; stroke-linecap: round; transform: rotate(-90deg); transform-origin: 50% 50%; transition: stroke-dasharray .6s ease; }
.ring-num {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 800; letter-spacing: 1px; color: #e6ebff; font-family: ui-monospace, monospace;
}
.ring-unit { font-size: 11px; color: #5a68a0; margin-left: 2px; font-weight: 600; }

.kpi-foot { display: flex; flex-direction: column; gap: 4px; }
.sub { font-size: 10px; letter-spacing: 1.5px; color: #5a68a0; font-family: ui-monospace, monospace; }
.hint { font-size: 12px; font-weight: 600; letter-spacing: .3px; }
.hint.good { color: #60ffb0; }
.hint.ok   { color: #a9b6ff; }
.hint.warn { color: #ffb860; }
.hint.bad  { color: #ff6f8c; }
</style>
