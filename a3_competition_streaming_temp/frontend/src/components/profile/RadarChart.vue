<template>
  <div ref="chartRef" class="chart-container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  data: { name: string; value: number }[]
}>()

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

function initChart() {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

function updateChart() {
  if (!chartInstance || !props.data.length) return

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'item'
    },
    radar: {
      indicator: props.data.map(item => ({ name: item.name, max: 100 })),
      radius: '65%',
      splitNumber: 5,
      axisName: {
        color: '#666',
        fontSize: 12
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(102, 126, 234, 0.2)'
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(102, 126, 234, 0.05)', 'rgba(102, 126, 234, 0.1)']
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(102, 126, 234, 0.3)'
        }
      }
    },
    series: [{
      type: 'radar',
      data: [{
        value: props.data.map(item => item.value),
        name: '学习状态',
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          width: 2,
          color: '#0d9488'
        },
        areaStyle: {
          color: 'rgba(102, 126, 234, 0.3)'
        },
        itemStyle: {
          color: '#0d9488'
        }
      }]
    }]
  }

  chartInstance.setOption(option)
}

function handleResize() {
  chartInstance?.resize()
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})

watch(() => props.data, () => {
  updateChart()
}, { deep: true })
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 350px;
}
</style>