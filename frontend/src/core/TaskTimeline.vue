<template>
  <div class="timeline-card glass">
    <div class="card-head">
      <span class="ic">🧭</span>
      <span class="title">TASK TIMELINE</span>
      <span class="more">8 today</span>
    </div>

    <div class="timeline">
      <div v-for="(t, i) in tasks" :key="i" class="t-item" :class="{ done: t.done, active: t.active }">
        <span class="t-dot"></span>
        <div class="t-body">
          <div class="t-title">{{ t.title }}</div>
          <div class="t-meta">
            <span class="t-time">{{ t.time }}</span>
            <span class="t-tag" :style="{ background: t.tagColor + '22', color: t.tagColor, borderColor: t.tagColor + '44' }">{{ t.tag }}</span>
          </div>
        </div>
        <span v-if="t.done" class="t-check">✓</span>
        <span v-else-if="t.active" class="t-spinner"></span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const tasks = ref([
  { title: '函数奇偶性习题 15 道', time: '09:00', tag: '练习', tagColor: '#0d9488', done: true, active: false },
  { title: '导数链式法则 · 苏格拉底辅导', time: '11:30', tag: '辅导', tagColor: '#7c4dff', done: true, active: false },
  { title: '错题复盘 · 本周', time: '14:00', tag: '复盘', tagColor: '#00D2FF', done: false, active: true },
  { title: '三角函数 PPT', time: '16:30', tag: '资源', tagColor: '#60ffb0', done: false, active: false },
  { title: '每日巩固训练', time: '20:00', tag: '训练', tagColor: '#ffb860', done: false, active: false }
])
</script>

<style scoped>
.timeline-card { padding: 18px 20px; grid-column: span 1; }
.card-head { display: flex; align-items: center; gap: 8px; font-family: ui-monospace, monospace; font-size: 11px; letter-spacing: 2px; color: #5a68a0; margin-bottom: 14px; }
.card-head .title { font-weight: 700; color: #0d9488; flex: 1; }
.card-head .more { padding: 2px 8px; border: 1px solid rgba(180,195,255,.2); border-radius: 999px; font-size: 10px; color: #0d9488; }

.timeline { display: flex; flex-direction: column; gap: 10px; }
.t-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(180,195,255,.1);
  transition: all .2s ease;
}
.t-item:hover { background: rgba(124,140,255,.08); border-color: rgba(124,140,255,.25); }
.t-item.done { opacity: .65; }
.t-item.active { background: rgba(124,140,255,.12); border-color: rgba(124,140,255,.4); box-shadow: 0 0 25px rgba(124,140,255,.15); }

.t-dot { width: 8px; height: 8px; margin-top: 4px; border-radius: 50%; background: #7c8cff; box-shadow: 0 0 8px rgba(124,140,255,.6); flex-shrink: 0; }
.t-item.done .t-dot { background: #60ffb0; box-shadow: 0 0 8px rgba(96,255,176,.6); }
.t-item.active .t-dot { background: #00D2FF; box-shadow: 0 0 10px rgba(0,210,255,.8); animation: dotPulse 1.6s ease-in-out infinite; }
@keyframes dotPulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.25); } }

.t-body { flex: 1; min-width: 0; }
.t-title { font-size: 13px; font-weight: 600; color: #e6ebff; letter-spacing: .3px; }
.t-item.done .t-title { text-decoration: line-through; color: #0d9488; }
.t-meta { margin-top: 4px; display: flex; align-items: center; gap: 8px; }
.t-time { font-size: 10px; font-family: ui-monospace, monospace; letter-spacing: 1px; color: #5a68a0; }
.t-tag { font-size: 10px; font-family: ui-monospace, monospace; letter-spacing: 1px; padding: 1px 8px; border-radius: 999px; border: 1px solid; }

.t-check { color: #60ffb0; font-weight: 700; }
.t-spinner { width: 14px; height: 14px; border-radius: 50%; border: 2px solid rgba(0,210,255,.25); border-top-color: #00D2FF; animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
