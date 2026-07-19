<template>
  <div class="kpi-card glass">
    <div class="card-head">
      <span class="ic">⚠️</span>
      <span class="title">WEAK POINTS</span>
      <span class="count">{{ points.length }}</span>
    </div>

    <div v-if="points.length" class="wp-list">
      <div v-for="p in points.slice(0, 5)" :key="p.node_id || p.name" class="wp-item">
        <div class="wp-name">{{ p.name }}</div>
        <el-progress
          :percentage="Math.round((p.mastery || 0) * 100)"
          :color="getColor(p.mastery || 0)"
          :stroke-width="6"
        />
      </div>
    </div>
    <div v-else class="empty">
      <div class="empty-ic">✓</div>
      <p>暂无薄弱知识点</p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ points: any[] }>()

function getColor(v: number): string {
  if (v >= 0.7) return '#67c23a'
  if (v >= 0.4) return '#e6a23c'
  return '#f56c6c'
}
</script>

<style scoped>
.kpi-card { padding: 18px 20px; grid-column: span 1; }
.card-head { display: flex; align-items: center; gap: 8px; font-family: ui-monospace, monospace; font-size: 11px; letter-spacing: 2px; color: #5a68a0; margin-bottom: 12px; }
.card-head .title { font-weight: 700; color: #0d9488; flex: 1; }
.card-head .count { padding: 2px 8px; border: 1px solid rgba(255,111,140,.35); background: rgba(255,111,140,.12); color: #ff6f8c; border-radius: 999px; font-size: 10px; }

.wp-list { display: flex; flex-direction: column; gap: 10px; }
.wp-item { display: flex; flex-direction: column; gap: 6px; }
.wp-name { font-size: 12px; color: #d0d8f0; font-weight: 600; letter-spacing: .3px; }
.wp-item :deep(.el-progress-bar__outer) { background: rgba(255,255,255,.08); border-radius: 999px; }
.wp-item :deep(.el-progress-bar__inner) { border-radius: 999px; }

.empty { padding: 20px; text-align: center; }
.empty-ic { font-size: 28px; color: #60ffb0; margin-bottom: 8px; }
.empty p { font-size: 12px; color: #0d9488; margin: 0; letter-spacing: 1px; }
</style>
