<script setup lang="ts">
import { computed, ref, onMounted, watch } from "vue"

interface Snapshot {
  created_at: string
  knowledge_mastery: number
  learning_stability: number
  emotional_state: number
}

const props = defineProps<{
  data: Snapshot[]
  maxPoints?: number
}>()

const limit = computed(() => props.maxPoints ?? 30)
const points = computed(() => (props.data || []).slice(-limit.value))

const W = 400
const H = 120
const P = { t: 10, r: 10, b: 22, l: 28 }
const chartW = W - P.l - P.r
const chartH = H - P.t - P.b

const activeIdx = ref<number | null>(null)

const xFor = (i: number, n: number) => P.l + (n <= 1 ? chartW / 2 : (chartW * i) / (n - 1))
const yFor = (v: number) => P.t + chartH - (Math.max(0, Math.min(100, v)) / 100) * chartH

const buildPath = (arr: number[], n: number) => {
  let d = ""
  for (let i = 0; i < n; i++) {
    const x = xFor(i, n)
    const y = yFor(arr[i] ?? 0)
    d += (i === 0 ? "M" : "L") + x.toFixed(1) + "," + y.toFixed(1) + " "
  }
  return d.trim()
}

const n = computed(() => points.value.length)

const masterPath = computed(() =>
  buildPath(points.value.map(p => p.knowledge_mastery), n.value)
)
const stabilPath = computed(() =>
  buildPath(points.value.map(p => p.learning_stability), n.value)
)
const emotionPath = computed(() =>
  buildPath(points.value.map(p => p.emotional_state), n.value)
)

const gridY = [0, 25, 50, 75, 100]
const gridX = computed(() => {
  const out: { x: number; label: string }[] = []
  const m = n.value
  if (m === 0) return out
  if (m <= 8) {
    for (let i = 0; i < m; i++) out.push({ x: xFor(i, m), label: formatLabel(points.value[i]?.created_at) })
  } else {
    const step = Math.ceil((m - 1) / 6)
    for (let i = 0; i < m; i += step) out.push({ x: xFor(i, m), label: formatLabel(points.value[i]?.created_at) })
    if ((m - 1) % step !== 0) out.push({ x: xFor(m - 1, m), label: formatLabel(points.value[m - 1]?.created_at) })
  }
  return out
})

function formatLabel(iso?: string) {
  if (!iso) return ""
  try {
    const d = new Date(iso)
    const mm = String(d.getMonth() + 1).padStart(2, "0")
    const dd = String(d.getDate()).padStart(2, "0")
    const hh = String(d.getHours()).padStart(2, "0")
    return `${mm}-${dd} ${hh}:00`
  } catch {
    return ""
  }
}

const tooltip = computed(() => {
  if (activeIdx.value === null || !points.value[activeIdx.value]) return null
  const p = points.value[activeIdx.value]
  const x = xFor(activeIdx.value, n.value)
  const y = P.t - 4
  return { x, y, p, idx: activeIdx.value }
})

function onMove(e: MouseEvent) {
  const svg = e.currentTarget as SVGElement
  if (!svg || n.value === 0) { activeIdx.value = null; return }
  const rect = svg.getBoundingClientRect()
  const px = ((e.clientX - rect.left) / rect.width) * W
  const relX = px - P.l
  if (relX < -chartW / (n.value + 1) || relX > chartW + chartW / (n.value + 1)) {
    activeIdx.value = null; return
  }
  let idx = Math.round((relX / chartW) * (n.value - 1))
  idx = Math.max(0, Math.min(n.value - 1, idx))
  activeIdx.value = idx
}

function onLeave() { activeIdx.value = null }

onMounted(() => {})
</script>

<template>
  <div class="gs-growth-chart">
    <div class="gs-chart-header">
      <span class="gs-chart-title">成长趋势</span>
      <span class="gs-legend">
        <span class="gs-legend-item"><span class="gs-dot" style="background:#14b8a6"></span>掌握度</span>
        <span class="gs-legend-item"><span class="gs-dot" style="background:#0d9488"></span>稳定性</span>
        <span class="gs-legend-item"><span class="gs-dot" style="background:#ffb3c9"></span>情绪</span>
      </span>
    </div>
    <svg :width="W" :height="H" viewBox="`0 0 ${W} ${H}`" @mousemove="onMove" @mouseleave="onLeave">
      <defs>
        <linearGradient id="gsMasterFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#14b8a6" stop-opacity="0.35" />
          <stop offset="100%" stop-color="#14b8a6" stop-opacity="0.02" />
        </linearGradient>
      </defs>

      <g v-if="n > 0">
        <g class="gs-grid">
          <line v-for="v in gridY" :key="'y'+v"
            :x1="P.l" :x2="W - P.r"
            :y1="yFor(v)" :y2="yFor(v)"
            stroke="rgba(255,255,255,0.08)" stroke-width="1" />
          <text v-for="v in gridY" :key="'yt'+v"
            :x="P.l - 4" :y="yFor(v) + 3"
            text-anchor="end" font-size="9" fill="rgba(255,255,255,0.35)">
            {{ v }}
          </text>
          <line v-for="gx in gridX" :key="'x'+gx.label"
            :x1="gx.x" :x2="gx.x"
            :y1="P.t" :y2="H - P.b"
            stroke="rgba(255,255,255,0.06)" stroke-width="1" />
          <text v-for="gx in gridX" :key="'xt'+gx.label"
            :x="gx.x" :y="H - 6"
            text-anchor="middle" font-size="8" fill="rgba(255,255,255,0.35)">
            {{ gx.label }}
          </text>
        </g>

        <path :d="masterPath" fill="url(#gsMasterFill)" stroke="none" />

        <path :d="masterPath" fill="none" stroke="#14b8a6" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
        <path :d="stabilPath" fill="none" stroke="#0d9488" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
        <path :d="emotionPath" fill="none" stroke="#ffb3c9" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />

        <g v-for="(p, i) in points" :key="'pt'+i">
          <circle :cx="xFor(i, n)" :cy="yFor(p.knowledge_mastery)" r="3" fill="#14b8a6" />
          <circle :cx="xFor(i, n)" :cy="yFor(p.learning_stability)" r="3" fill="#0d9488" />
          <circle :cx="xFor(i, n)" :cy="yFor(p.emotional_state)" r="3" fill="#ffb3c9" />
        </g>

        <g v-if="tooltip">
          <line
            :x1="tooltip.x" :x2="tooltip.x"
            :y1="P.t" :y2="H - P.b"
            stroke="rgba(123,168,255,0.5)" stroke-dasharray="3 2" />
          <circle
            :cx="tooltip.x" :cy="yFor(tooltip.p.knowledge_mastery)" r="5"
            fill="#14b8a6" stroke="#fff" stroke-width="1.5" />
          <circle
            :cx="tooltip.x" :cy="yFor(tooltip.p.learning_stability)" r="5"
            fill="#0d9488" stroke="#fff" stroke-width="1.5" />
          <circle
            :cx="tooltip.x" :cy="yFor(tooltip.p.emotional_state)" r="5"
            fill="#ffb3c9" stroke="#fff" stroke-width="1.5" />
        </g>
      </g>
      <g v-else>
        <text :x="W/2" :y="H/2" text-anchor="middle" fill="rgba(255,255,255,0.4)" font-size="12">暂无数据</text>
      </g>
    </svg>

    <div v-if="tooltip" class="gs-tip"
      :style="{ left: (tooltip.x / W * 100) + '%', top: (tooltip.y / H * 100) + '%' }">
      <div class="gs-tip-row"><span class="gs-k">时间</span><span class="gs-v">{{ formatLabel(tooltip.p.created_at) }}</span></div>
      <div class="gs-tip-row"><span class="gs-k" style="color:#14b8a6">● 掌握度</span><span class="gs-v">{{ tooltip.p.knowledge_mastery.toFixed(1) }}</span></div>
      <div class="gs-tip-row"><span class="gs-k" style="color:#0d9488">● 稳定性</span><span class="gs-v">{{ tooltip.p.learning_stability.toFixed(1) }}</span></div>
      <div class="gs-tip-row"><span class="gs-k" style="color:#ffb3c9">● 情绪</span><span class="gs-v">{{ tooltip.p.emotional_state.toFixed(1) }}</span></div>
    </div>
  </div>
</template>

<style scoped>
.gs-growth-chart {
  position: relative;
  width: 100%;
  background: rgba(12, 20, 36, 0.6);
  border: 1px solid rgba(123, 168, 255, 0.22);
  border-radius: 10px;
  padding: 10px 12px 12px;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}
.gs-chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.gs-chart-title {
  font-size: 13px;
  font-weight: 600;
  color: #e8eefc;
  letter-spacing: 1px;
}
.gs-legend {
  display: flex;
  gap: 10px;
  font-size: 11px;
  color: rgba(255,255,255,0.6);
}
.gs-legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.gs-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  box-shadow: 0 0 6px currentColor;
}
.gs-tip {
  position: absolute;
  transform: translate(-50%, -105%);
  background: rgba(12, 26, 54, 0.92);
  border: 1px solid rgba(123, 168, 255, 0.45);
  border-radius: 8px;
  padding: 6px 10px;
  min-width: 150px;
  box-shadow: 0 6px 24px rgba(123, 168, 255, 0.25);
  pointer-events: none;
  backdrop-filter: blur(6px);
  font-size: 11px;
  color: #e8eefc;
  z-index: 2;
}
.gs-tip-row {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  line-height: 1.5;
}
.gs-k { color: rgba(255,255,255,0.6); }
.gs-v { color: #fff; font-weight: 600; }
</style>
