<template>
  <div class="ai-state-panel" v-if="visible">
    <div class="panel-glass">
      <div class="panel-header">
        <div class="header-title">
          <span class="hdr-bullet"></span>
          <span class="hdr-text">AI 决策面板</span>
          <span class="hdr-sub">· AI Decision Panel</span>
        </div>
        <button class="toggle-btn" @click="toggleVisible" title="折叠 / 展开">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
        </button>
      </div>

      <div class="panel-body">
        <div class="section">
          <div class="section-title">
            <span class="section-dot" style="background:#0d9488"></span>
            LearningState · 学习画像
          </div>
          <div class="state-row">
            <svg class="radar" viewBox="0 0 200 200" width="148" height="148">
              <defs>
                <radialGradient id="radarFill" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stop-color="rgba(13,148,136,.35)" />
                  <stop offset="100%" stop-color="rgba(13,148,136,.02)" />
                </radialGradient>
              </defs>
              <g class="radar-grid">
                <polygon v-for="(p, i) in gridPolys" :key="i"
                         :points="p.join(' ')" fill="none"
                         stroke="rgba(13,148,136,.15)" stroke-width="1" />
              </g>
              <g class="radar-axes">
                <line v-for="(a, i) in axes" :key="'a'+i"
                      x1="100" y1="100"
                      :x2="100 + Math.cos(a.r) * 90"
                      :y2="100 + Math.sin(a.r) * 90"
                      stroke="rgba(13,148,136,.18)" stroke-width="1" />
                <text v-for="(a, i) in axes" :key="'t'+i"
                      :x="100 + Math.cos(a.r) * 110"
                      :y="100 + Math.sin(a.r) * 110 + 4"
                      fill="#0d9488" font-size="10" font-weight="600"
                      text-anchor="middle" dominant-baseline="middle">
                  {{ a.label }}
                </text>
              </g>
              <polygon :points="dataPoly"
                       fill="url(#radarFill)"
                       stroke="#0d9488" stroke-width="2" />
              <circle v-for="(pt, i) in dataPoints" :key="'c'+i"
                      :cx="pt.x" :cy="pt.y" r="3.5"
                      fill="#0d9488" stroke="#fff" stroke-width="1.5" />
            </svg>
            <div class="state-side">
              <div class="side-card">
                <div class="side-label">知识掌握</div>
                <div class="side-value">{{ fmtNum(state.knowledge_mastery) }}%</div>
              </div>
              <div class="side-card weak">
                <div class="side-label">薄弱点</div>
                <div class="side-value">{{ (state.weak_points || []).length || 0 }} 项</div>
                <div class="side-tags" v-if="(state.weak_points || []).length">
                  <span class="weak-tag" v-for="(w, i) in (state.weak_points || []).slice(0,3)" :key="i">
                    {{ w.name || w }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="section">
          <div class="section-title">
            <span class="section-dot" style="background:#059669"></span>
            策略 · {{ modeLabel || (tutoringMode ? (tutoringMode === 'socratic' ? '苏格拉底引导' : '直接讲解') : '') }}
          </div>
          <div class="mode-row">
            <span class="strategy-badge" :class="strategyColor">
              <span class="bd-dot"></span>
              {{ strategyLabel }}
            </span>
            <span class="tutoring-badge" v-if="tutoringMode" :class="tutoringMode === 'socratic' ? 'socratic' : 'direct'">
              {{ tutoringMode === 'socratic' ? '苏格拉底引导' : '直接讲解' }}
            </span>
          </div>
        </div>

        <div class="section">
          <div class="section-title">
            <span class="section-dot" style="background:#0ea5e9"></span>
            Agent · 多智能体链路
          </div>
          <div class="trace-list">
            <div class="trace-item" v-for="(a, i) in agentTraces" :key="i">
              <span class="trace-dot" :style="{ background: agentColor(a.agent_name) }"
                    :class="{ pulse: a.status === 'running' }"></span>
              <div class="trace-name">{{ agentDisplayName(a.agent_name) }}</div>
              <span class="trace-status" :class="traceStatusClass(a.status)">{{ traceStatusText(a.status) }}</span>
            </div>
          </div>
        </div>

        <div class="section">
          <div class="section-title">
            <span class="section-dot" style="background:#f59e0b"></span>
            决策摘要 · Decision
          </div>
          <div class="summary-box">
            <span class="summary-emoji">{{ summaryEmoji }}</span>
            <span class="summary-text">{{ decisionSummary || '暂无决策摘要，开始提问后将展示 AI 决策过程…' }}</span>
          </div>
        </div>
      </div>

      <div class="panel-footer">青藜伴读 · Learning Agent</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  learningState?: any
  strategyMode?: string
  tutoringMode?: string
  modeLabel?: string
  agentTraces?: Array<{ agent_name: string; status?: string }>
  decisionSummary?: string
  visible?: boolean
}>()

const emit = defineEmits<{
  'update:visible': [v: boolean]
}>()

const visible = computed({
  get: () => props.visible !== false,
  set: (v) => emit('update:visible', v)
})
function toggleVisible() { visible.value = !visible.value }

const state = computed<any>(() => props.learningState || {})

const fieldOrder = [
  { key: 'knowledge_mastery', label: '知识' },
  { key: 'learning_stability', label: '稳定' },
  { key: 'reaction_speed', label: '反应' },
  { key: 'emotion_state', label: '情绪' },
  { key: 'autonomous_learning', label: '自主' },
  { key: 'transfer_ability', label: '迁移' }
]

const axes = computed(() => {
  const cx = Math.PI / 2
  return fieldOrder.map((_, i) => ({
    r: cx + (Math.PI * 2 / fieldOrder.length) * -i,
    label: fieldOrder[i].label
  }))
})

function getVal(k: string): number {
  const v = state.value?.[k]
  if (typeof v === 'number') return Math.min(1, Math.max(0, v))
  if (typeof v === 'string') {
    const n = parseFloat(v)
    if (!isNaN(n)) return Math.min(1, Math.max(0, n / 100 > 1 ? n / 100 : n))
  }
  return 0.3
}

const dataPoints = computed(() => {
  return axes.value.map((a, i) => ({
    x: 100 + Math.cos(a.r) * getVal(fieldOrder[i].key) * 90,
    y: 100 + Math.sin(a.r) * getVal(fieldOrder[i].key) * 90
  }))
})

const dataPoly = computed(() =>
  dataPoints.value.map(p => `${p.x},${p.y}`).join(' ')
)

const gridPolys = computed(() => {
  const rs = [0.25, 0.5, 0.75, 1]
  return rs.map(k =>
    axes.value.map(a =>
      `${100 + Math.cos(a.r) * 90 * k},${100 + Math.sin(a.r) * 90 * k}`
    )
  )
})

function fmtNum(v: any): string {
  if (v == null || v === '') return '—'
  const n = Number(v)
  if (isNaN(n)) return String(v)
  if (n > 1 && n <= 100) return Math.round(n).toString()
  return Math.round(n * 100).toString()
}

const strategyMap: Record<string, { label: string; color: string }> = {
  weakness_fix: { label: '补弱强化', color: 'weakness' },
  score_boost: { label: '提分冲刺', color: 'boost' },
  exam_sprint: { label: '考前速通', color: 'sprint' },
  balanced: { label: '均衡推进', color: 'balanced' }
}
const strategyLabel = computed(() => {
  const m = strategyMap[props.strategyMode || '']
  return m ? m.label : (props.strategyMode || '自动策略')
})
const strategyColor = computed(() => {
  const m = strategyMap[props.strategyMode || '']
  return m ? m.color : 'balanced'
})

const agentColorMap: Record<string, string> = {
  diagnose: '#0d9488',
  plan: '#0f766e',
  instruct: '#0d9488',
  socratic: '#f59e0b',
  emotional: '#0ea5e9',
  reviewer: '#059669',
  trainer: '#0d9488'
}
function agentColor(name: string): string {
  return agentColorMap[name] || '#64748b'
}
const agentNameMap: Record<string, string> = {
  diagnose: '诊断 Agent',
  plan: '规划 Agent',
  instruct: '讲授 Agent',
  socratic: '苏格拉底 Agent',
  emotional: '情绪 Agent',
  reviewer: '复盘 Agent',
  trainer: '训练 Agent'
}
function agentDisplayName(name: string): string {
  return agentNameMap[name] || name
}

function traceStatusClass(s?: string): string {
  if (s === 'running') return 'running'
  if (s === 'completed') return 'completed'
  if (s === 'failed') return 'failed'
  return 'waiting'
}
function traceStatusText(s?: string): string {
  if (s === 'running') return '运行中'
  if (s === 'completed') return '已完成'
  if (s === 'failed') return '失败'
  return '等待'
}

const summaryEmoji = computed(() => {
  const s = (props.decisionSummary || '').toLowerCase()
  if (!s) return '🧠'
  if (/weak|薄弱/.test(s)) return '🎯'
  if (/score|提分/.test(s)) return '🚀'
  if (/exam|考/.test(s)) return '🔥'
  if (/emotion|情绪/.test(s)) return '💛'
  if (/review|复盘/.test(s)) return '✅'
  return '🧭'
})
</script>

<style scoped>
.ai-state-panel {
  width: 340px;
  max-width: 360px;
  position: relative;
  z-index: 10;
}
.panel-glass {
  background: #fff;
  border: 1px solid #e7e5e2;
  border-radius: 18px;
  box-shadow: 0 16px 48px rgba(13,148,136,.12), 0 4px 12px rgba(0,0,0,.05);
  overflow: hidden;
  color: #0f172a;
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: linear-gradient(90deg, #f0fdfa 0%, #ffffff 100%);
  border-bottom: 1px solid #e7e5e2;
}
.header-title { display: flex; align-items: center; gap: 6px; font-size: 13px; }
.hdr-bullet {
  width: 8px; height: 8px; border-radius: 50%;
  background: #0d9488; box-shadow: 0 0 10px rgba(13,148,136,.7);
  animation: pulse-bullet 2s infinite;
}
@keyframes pulse-bullet { 0%,100%{opacity:.55} 50%{opacity:1} }
.hdr-text { font-weight: 700; letter-spacing: .5px; color: #0f172a; }
.hdr-sub { color: #0d9488; font-size: 11px; font-weight: 400; }
.toggle-btn {
  background: #fff;
  border: 1px solid #e7e5e2;
  color: #0d9488;
  width: 26px; height: 26px; border-radius: 8px;
  cursor: pointer;
  display: inline-flex; align-items: center; justify-content: center;
  transition: all .15s;
}
.toggle-btn:hover { background: #f0fdfa; border-color: #0d9488; }

.panel-body { padding: 10px 12px; display: flex; flex-direction: column; gap: 12px; }

.section { }
.section-title {
  font-size: 11px; font-weight: 700;
  color: #0f766e; letter-spacing: 1px;
  display: flex; align-items: center; gap: 6px;
  margin-bottom: 8px;
  text-transform: uppercase;
}
.section-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }

.state-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.radar { flex-shrink: 0; border-radius: 10px; background: #f0fdfa; border: 1px solid #ccfbf1; }
.state-side { display: flex; flex-direction: column; gap: 8px; flex: 1; min-width: 0; }
.side-card {
  background: #fafaf8;
  border: 1px solid #e7e5e2;
  border-radius: 10px;
  padding: 8px 10px;
}
.side-label { font-size: 10px; color: #64748b; }
.side-value { font-size: 18px; font-weight: 700; color: #0d9488; letter-spacing: 1px; }
.side-card.weak .side-value { color: #dc2626; }
.side-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
.weak-tag {
  font-size: 10px;
  background: #fff1f2;
  color: #dc2626;
  padding: 2px 6px;
  border-radius: 6px;
  border: 1px solid #fecaca;
}

.mode-row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.strategy-badge, .tutoring-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  padding: 5px 10px;
  border-radius: 999px;
  letter-spacing: .5px;
}
.bd-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.strategy-badge.weakness { background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }
.strategy-badge.boost    { background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
.strategy-badge.sprint   { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
.strategy-badge.balanced { background: #f0fdf4; color: #047857; border: 1px solid #bbf7d0; }
.tutoring-badge.socratic { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
.tutoring-badge.direct   { background: #f0fdfa; color: #0f766e; border: 1px solid #ccfbf1; }

.trace-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: #fafaf8;
  border-radius: 10px;
  padding: 8px 10px;
  border: 1px solid #e7e5e2;
}
.trace-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 2px;
  font-size: 12px;
}
.trace-dot {
  width: 8px; height: 8px; border-radius: 50%;
  flex-shrink: 0;
}
.trace-dot.pulse { animation: trace-pulse 1.2s infinite; }
@keyframes trace-pulse {
  0%,100% { box-shadow: 0 0 0 0 rgba(13,148,136,.6); }
  50%     { box-shadow: 0 0 0 8px rgba(13,148,136,0); }
}
.trace-name { flex: 1; color: #334155; }
.trace-status {
  font-size: 10px; font-weight: 600;
  padding: 2px 8px; border-radius: 999px;
  letter-spacing: .5px;
}
.trace-status.running   { background: #f0fdf4;  color: #047857; border: 1px solid #bbf7d0; }
.trace-status.completed { background: #f0fdfa;  color: #0f766e; border: 1px solid #ccfbf1; }
.trace-status.failed    { background: #fef2f2;  color: #b91c1c; border: 1px solid #fecaca; }
.trace-status.waiting   { background: #fafaf8; color: #64748b; border: 1px solid #e7e5e2; }

.summary-box {
  background: linear-gradient(135deg, #f0fdfa 0%, #fffbeb 100%);
  border: 1px solid #ccfbf1;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 12px;
  line-height: 1.6;
  color: #1e293b;
  display: flex;
  gap: 8px;
  align-items: flex-start;
}
.summary-emoji { font-size: 16px; flex-shrink: 0; }
.summary-text { flex: 1; white-space: pre-wrap; }

.panel-footer {
  text-align: right;
  padding: 6px 12px 8px;
  font-size: 10px;
  color: #64748b;
  letter-spacing: .5px;
}
</style>
