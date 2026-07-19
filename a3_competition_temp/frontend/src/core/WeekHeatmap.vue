<template>
  <div class="kpi-card glass">
    <div class="card-head">
      <span class="ic">🗓️</span>
      <span class="title">WEEKLY HEATMAP</span>
    </div>

    <div class="heat">
      <div v-for="(d, i) in week" :key="i" class="h-day">
        <div class="h-day-label">{{ d.label }}</div>
        <div class="h-day-bar" :style="{ height: Math.max(d.hours * 10, 2) + 'px', background: d.color }"></div>
        <div class="h-day-hours">{{ d.hours }}h</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ week: { label: string; hours: number; color: string }[] }>()
</script>

<style scoped>
.kpi-card { padding: 18px 20px; grid-column: span 1; }
.card-head { display: flex; align-items: center; gap: 8px; font-family: ui-monospace, monospace; font-size: 11px; letter-spacing: 2px; color: #5a68a0; margin-bottom: 14px; }
.card-head .title { font-weight: 700; color: #0d9488; }

.heat { display: flex; align-items: flex-end; justify-content: space-between; gap: 8px; height: 140px; }
.h-day { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6px; }
.h-day-label { font-size: 10px; color: #5a68a0; font-family: ui-monospace, monospace; letter-spacing: 1px; }
.h-day-bar {
  width: 100%; max-width: 24px; min-height: 2px;
  border-radius: 4px 4px 2px 2px;
  opacity: .85;
  box-shadow: 0 0 12px currentColor;
  transition: all .3s ease;
}
.h-day-bar:hover { opacity: 1; transform: scaleY(1.08); }
.h-day-hours { font-size: 10px; color: #0d9488; font-family: ui-monospace, monospace; }
</style>
