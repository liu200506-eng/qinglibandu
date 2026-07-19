<template>
  <div class="state-renderer glass">
    <div class="state-row">
      <span class="label">AI STATE</span>
      <span class="value state-{{ ai.state }}">{{ ai.state.toUpperCase() }}</span>
      <span class="dot-dot" :class="ai.energyLevel"></span>
    </div>
    <div class="state-row">
      <span class="label">EMOTION</span>
      <span class="value emotion">{{ emoji }} {{ ai.emotion }}</span>
    </div>
    <div class="state-row">
      <span class="label">ENERGY</span>
      <div class="mini-bar"><div class="fill" :style="{ width: ai.energy * 100 + '%' }"></div></div>
      <span class="value num">{{ Math.round(ai.energy * 100) }}%</span>
    </div>

    <div v-if="ai.traces.length" class="traces">
      <span class="traces-title">RECENT TRACES</span>
      <div v-for="(t, i) in ai.traces.slice(-3).reverse()" :key="i" class="trace-item">
        <span class="trace-name">{{ t.agent }}</span>
        <span class="trace-status" :class="t.status">{{ t.status }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAIStore } from '@/stores/ai'

const ai = useAIStore()

const emoji = computed(() => {
  const map: Record<string, string> = {
    neutral: '😌',
    curious: '🤔',
    confident: '😎',
    happy: '😊',
    concerned: '😰',
    excited: '🤩'
  }
  return map[ai.emotion] || '😌'
})
</script>

<style scoped>
.state-renderer {
  position: fixed;
  top: 18px;
  right: 18px;
  padding: 14px 18px;
  min-width: 260px;
  z-index: 1000;
  font-family: ui-monospace, monospace;
  font-size: 12px;
}
.state-row { display: flex; align-items: center; gap: 10px; margin: 4px 0; }
.label { color: #5a68a0; letter-spacing: 1.5px; width: 80px; flex-shrink: 0; }
.value { color: #e6ebff; letter-spacing: 1px; }
.state-idle      { color: #0d9488; }
.state-focus     { color: #a9b6ff; }
.state-thinking  { color: #6c5ce7; }
.state-processing{ color: #00d2ff; }
.state-success   { color: #60ffb0; }
.state-error     { color: #ff6f8c; }
.dot-dot { width: 6px; height: 6px; border-radius: 50%; background: #60ffb0; box-shadow: 0 0 8px rgba(96,255,176,.8); }
.dot-dot.mid { background: #ffb860; }
.dot-dot.low { background: #ff6f8c; }

.mini-bar { flex: 1; height: 5px; background: rgba(255,255,255,.1); border-radius: 999px; overflow: hidden; }
.fill { height: 100%; background: linear-gradient(90deg, #6C5CE7, #00D2FF); transition: width .4s ease; }
.value.num { color: #c0c9f0; }

.emotion { font-size: 13px; }

.traces { margin-top: 10px; border-top: 1px dashed rgba(180,195,255,.2); padding-top: 8px; }
.traces-title { color: #5a68a0; letter-spacing: 1.5px; font-size: 10px; }
.trace-item { display: flex; justify-content: space-between; margin: 4px 0; font-size: 11px; color: #0d9488; }
.trace-status.completed { color: #60ffb0; }
.trace-status.running   { color: #ffb860; }
.trace-status.failed    { color: #ff6f8c; }
</style>
