<template>
  <div class="chart-card glass">
    <div class="card-head">
      <span class="ic">📡</span>
      <span class="title">学习概览 · 七维雷达</span>
      <span class="update-time">{{ updateTime }}</span>
    </div>
    <div ref="chartRef" class="chart"></div>
    <div class="legend-row">
      <div class="legend-item">
        <span class="lg-dot" style="background:#0d9488"></span>
        <span class="lg-label">当前水平</span>
      </div>
      <div class="legend-item">
        <span class="lg-dot" style="background:#0f766e"></span>
        <span class="lg-label">目标 80</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import * as echarts from 'echarts'
import { useProfileStore } from '@/stores/profile'

const profileStore = useProfileStore()

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null
const updateTime = ref('刚刚')

const mockProfile = {
  knowledge_mastery: 75,
  learning_stability: 70,
  response_speed: 82,
  error_pattern_score: 65,
  self_driven_score: 60,
  transfer_ability: 55,
  emotional_state: 80
}

const radarData = computed(() => {
  const real = profileStore.profile
  const base = real ? {
    knowledge_mastery: real.knowledge_mastery,
    learning_stability: real.learning_stability,
    response_speed: real.response_speed,
    error_pattern_score: real.error_pattern_score,
    self_driven_score: real.self_driven_score,
    transfer_ability: real.transfer_ability,
    emotional_state: real.emotional_state
  } : mockProfile
  return [
    { name: '知识掌握', value: base.knowledge_mastery },
    { name: '学习稳定', value: base.learning_stability },
    { name: '反应速度', value: base.response_speed },
    { name: '错因健康', value: base.error_pattern_score },
    { name: '自主学习', value: base.self_driven_score },
    { name: '迁移能力', value: base.transfer_ability },
    { name: '情绪状态', value: base.emotional_state }
  ]
})

function makeOption() {
  const indicators = radarData.value.map(d => ({ name: d.name, max: 100 }))
  const currentValues = radarData.value.map(d => d.value)
  const targetValues = radarData.value.map(() => 80)
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: '#0a0f1c',
      borderColor: 'rgba(180,195,255,.3)',
      textStyle: { color: '#d0d8f0', fontFamily: 'ui-monospace, monospace' }
    },
    radar: {
      indicator: indicators,
      radius: '65%',
      center: ['50%', '52%'],
      splitNumber: 5,
      axisName: {
        color: '#0d9488',
        fontSize: 11,
        fontFamily: 'ui-monospace, monospace',
        letterSpacing: 1
      },
      splitLine: {
        lineStyle: { color: 'rgba(180,195,255,.15)' }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(13,148,136,.04)', 'rgba(13,148,136,.07)', 'rgba(13,148,136,.04)', 'rgba(13,148,136,.07)']
        }
      },
      axisLine: { lineStyle: { color: 'rgba(180,195,255,.25)' } },
      nameTextStyle: { padding: 4 }
    },
    series: [{
      type: 'radar',
      data: [
        {
          value: targetValues,
          name: '目标 80',
          symbol: 'none',
          lineStyle: { width: 1, color: 'rgba(118,75,162,.6)', type: 'dashed' },
          areaStyle: { color: 'rgba(118,75,162,.08)' }
        },
        {
          value: currentValues,
          name: '当前水平',
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { width: 2, color: '#0d9488' },
          areaStyle: { color: 'rgba(102,126,234,0.35)' },
          itemStyle: { color: '#0d9488', borderColor: '#fff', borderWidth: 1 },
          emphasis: { itemStyle: { borderWidth: 2 } }
        }
      ]
    }]
  }
}

function redraw() {
  if (!chartInstance) return
  chartInstance.setOption(makeOption(), true)
}

function resize() { chartInstance?.resize() }

onMounted(() => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value, undefined, { renderer: 'canvas' })
    redraw()
    window.addEventListener('resize', resize)
  }
  if (profileStore.profile) {
    setTimeout(redraw, 100)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', resize)
  chartInstance?.dispose()
})
</script>

<style scoped>
.chart-card { padding: 18px 20px; grid-column: span 2; display: flex; flex-direction: column; }
@media (max-width: 820px) { .chart-card { grid-column: span 1; } }
.card-head { display: flex; align-items: center; gap: 8px; font-family: ui-monospace, monospace; font-size: 11px; letter-spacing: 2px; color: #5a68a0; margin-bottom: 6px; }
.card-head .title { font-weight: 700; color: #0d9488; flex: 1; }
.card-head .update-time { padding: 2px 10px; border: 1px solid rgba(180,195,255,.2); border-radius: 999px; font-size: 10px; color: #0d9488; }

.chart { flex: 1; min-height: 260px; }

.legend-row { display: flex; gap: 18px; justify-content: center; padding: 6px 0 0; }
.legend-item { display: flex; align-items: center; gap: 6px; font-family: ui-monospace, monospace; font-size: 10px; color: #0d9488; letter-spacing: 1px; }
.lg-dot { width: 8px; height: 8px; border-radius: 50%; }
</style>
