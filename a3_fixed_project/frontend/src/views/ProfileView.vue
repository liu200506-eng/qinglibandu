<template>
  <div class="profile-page">
    <div class="profile-hero">
      <div class="hero-left">
        <div class="avatar-wrap">
          <div class="avatar">{{ heroInitial }}</div>
        </div>
        <div class="hero-info">
          <div class="hero-name">
            {{ profile.username || '同学' }}
            <span class="level-badge" :class="'level-' + (profile.level_tier || 'C')">
              <span class="lt">{{ profile.level_tier || 'C' }}</span>
              <span class="lt-label">段位</span>
            </span>
            <el-tag :type="gradeTagType" size="small" effect="dark" style="margin-left:4px" v-if="profile.grade">{{ profile.grade }}</el-tag>
          </div>
          <div class="hero-tags">
            <el-tag size="small" type="success" effect="plain" v-if="profile.education_level === 'university'">大学</el-tag>
            <el-tag size="small" type="primary" effect="plain" v-else>高中</el-tag>
            <el-tag v-for="s in (profile.subjects || []).slice(0,4)" :key="s" size="small" effect="plain">{{ s }}</el-tag>
            <el-tag size="small" effect="plain">{{ cognitiveLabel(profile.cognitive_preference) }}</el-tag>
          </div>
          <div class="hero-meta">
            <span><el-icon><Clock /></el-icon> {{ formatTime(profile.last_updated) }}</span>
            <span class="sep">|</span>
            <span><el-icon><Edit /></el-icon> {{ errorTree.total_errors || 0 }} 道错题</span>
            <span class="sep">|</span>
            <span><el-icon><TrendCharts /></el-icon> 近30天掌握度 {{ profile.knowledge_mastery ?? '--' }}</span>
          </div>
        </div>
      </div>
      <div class="hero-center">
        <div class="score-ring">
          <svg viewBox="0 0 100 100" width="110" height="110">
            <circle cx="50" cy="50" r="42" stroke="rgba(255,255,255,0.2)" stroke-width="8" fill="none"/>
            <circle cx="50" cy="50" r="42" stroke="white" stroke-width="8" fill="none"
              stroke-linecap="round" :stroke-dasharray="`${scoreDash} 264`"
              style="transform: rotate(-90deg); transform-origin: 50% 50%"/>
          </svg>
          <div class="score-text">
            <div class="score-num">{{ profile.composite_score ?? '--' }}</div>
            <div class="score-label">综合画像分</div>
          </div>
        </div>
        <div class="score-tip">{{ levelTip }}</div>
      </div>
      <div class="hero-actions">
        <el-button type="primary" round @click="scrollTo('diagnosis')">🤖 AI诊断书</el-button>
        <el-button type="success" round @click="scrollTo('rhythm')">⏰ 学习节律</el-button>
        <el-button type="warning" round @click="showEdit = true">✏️ 编辑画像</el-button>
      </div>
    </div>

    <div class="ai-insight" v-if="insightText">
      💡 <b>AI洞察：</b>{{ insightText }}
    </div>

    <el-row :gutter="20" class="row-gap">
      <el-col :xs="24" :md="10">
        <el-card class="card" shadow="hover">
          <template #header>
            <div class="card-title">🧭 学习画像七维雷达</div>
            <el-tag size="small" effect="plain" style="margin-left:auto">综合 {{ profile.level_tier || 'C' }} 段位</el-tag>
          </template>
          <v-chart class="radar-chart" :option="radarOption" autoresize />
          <div class="radar-foot">
            <div class="dim" v-for="r in profile.radar || []" :key="r.name">
              <span class="dname">{{ r.name }}</span>
              <span class="dval" :style="{ color: dimColor(r.value) }">{{ r.value }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="14">
        <el-card class="card" shadow="hover">
          <template #header>
            <div class="card-title">🔮 错因星座图</div>
            <span class="sub-title" v-if="hasErrors">主错因：{{ topErrorLabel }} · 占比 {{ topErrorPct }}%</span>
            <span class="sub-title" v-else>答题后自动生成</span>
          </template>
          <v-chart class="error-chart" :option="errorRadarOption" autoresize v-if="hasErrors" />
          <el-empty v-else description="暂无错因数据，去答题试试？" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="row-gap">
      <el-col :xs="24" :md="14">
        <el-card class="card" shadow="hover">
          <template #header>
            <div class="card-title">📅 30天学习热力日历</div>
            <el-tag size="small" effect="plain" style="margin-left:auto">错题 {{ calendarErrors }} · 反馈 {{ calendarFeedback }}</el-tag>
          </template>
          <div class="calendar-wrap">
            <div class="calendar-weekdays">
              <span v-for="w in ['日','一','二','三','四','五','六']" :key="w">{{ w }}</span>
            </div>
            <div class="calendar-grid">
              <div v-for="(d, i) in calendarCells" :key="i" class="cell"
                :class="{ empty: !d, today: d && d.is_today, weekend: d && d.is_weekend, fire: d && d.errors >= 5 }"
                :style="d ? { backgroundColor: calendarColor(d.intensity) } : {}"
                @mouseenter="hoverDay = d">
                <span v-if="d" class="day-num">{{ d.day_num }}</span>
                <span v-if="d && d.errors >= 5" class="fire-badge">🔥</span>
              </div>
            </div>
            <div class="calendar-legend">
              <span>低</span>
              <span class="legend-block" style="background:#e3f2fd"></span>
              <span class="legend-block" style="background:#90caf9"></span>
              <span class="legend-block" style="background:#0d9488"></span>
              <span class="legend-block" style="background:#0d47a1"></span>
              <span>高</span>
              <span class="legend-tip">错题+反馈越多颜色越深</span>
            </div>
            <div v-if="hoverDay" class="calendar-hover">
              📆 {{ hoverDay.date }} · ❌ {{ hoverDay.errors }}道 · 💬 {{ hoverDay.feedback }}条
              <span v-if="hoverDay.top_knowledge && hoverDay.top_knowledge.length"> · 涉及：{{ hoverDay.top_knowledge.slice(0,3).join('、') }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="10">
        <el-card class="card" shadow="hover" id="rhythm">
          <template #header>
            <div class="card-title">⏰ 学习节律 · 昼夜热力</div>
            <span class="sub-title">高峰：{{ peakHourLabels }}</span>
          </template>
          <v-chart class="rhythm-chart" :option="rhythmOption" autoresize />
          <div class="rhythm-foot">
            📌 推荐黄金时段：<b>{{ recommendSlots }}</b>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="row-gap">
      <el-col :xs="24" :md="8">
        <el-card class="card" shadow="hover">
          <template #header>
            <div class="card-title">🧠 性格大五画像</div>
            <span class="sub-title">基于学习行为推断</span>
          </template>
          <v-chart class="big5-chart" :option="big5Option" autoresize />
        </el-card>
      </el-col>

      <el-col :xs="24" :md="8">
        <el-card class="card" shadow="hover">
          <template #header>
            <div class="card-title">🔥 TOP5 薄弱点加速区</div>
            <el-tag size="small" effect="plain" style="margin-left:auto">按优先级</el-tag>
          </template>
          <div v-if="!profile.top_weak || !profile.top_weak.length" class="empty-wrap"><el-empty description="暂无薄弱点" /></div>
          <div v-else class="weak-list">
            <div v-for="(w, idx) in profile.top_weak" :key="w.node_id" class="weak-row">
              <div class="weak-rank">{{ idx + 1 }}</div>
              <div class="weak-main">
                <div class="weak-name" :title="w.name">{{ w.name }}</div>
                <div class="weak-bar"><div class="wf" :style="{ width: Math.min(100, w.priority_score) + '%' }" :class="'w' + idx"></div></div>
              </div>
              <div class="weak-score">
                <div class="prio">{{ w.priority_score }}</div>
                <div class="sub">错{{ w.error_count }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="8">
        <el-card class="card" shadow="hover">
          <template #header>
            <div class="card-title">📈 近30天学习趋势</div>
            <el-tag size="small" effect="plain" style="margin-left:auto">7日均值线</el-tag>
          </template>
          <v-chart class="trend-chart" :option="trendOption" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="row-gap">
      <el-col :xs="24" :md="12">
        <el-card class="card" shadow="hover">
          <template #header>
            <div class="card-title">📂 错题谱系树</div>
            <el-radio-group v-model="errorTreeMode" size="small" style="margin-left:auto">
              <el-radio-button value="error_type">按错因</el-radio-button>
              <el-radio-button value="knowledge">按知识点</el-radio-button>
            </el-radio-group>
          </template>
          <el-scrollbar height="360px">
            <div v-if="!errorTree.total_errors" class="empty-wrap"><el-empty description="暂无错题记录" /></div>
            <el-collapse v-else accordion>
              <el-collapse-item v-for="(items, key) in errorTreeMap" :key="key" :title="key + ' · 共' + items.length + '道'">
                <div class="error-cards">
                  <div v-for="e in items" :key="e.id" class="ec" :style="{ borderLeftColor: errorTypeColor[e.error_type_label] || '#0d9488' }">
                    <div class="ec-q">❓ {{ (e.question || '').slice(0, 90) }}{{ (e.question || '').length > 90 ? '…' : '' }}</div>
                    <div class="ec-a">
                      <span class="wrong">你答：{{ e.user_answer || '空' }}</span>
                      <span class="right">正确：{{ e.correct_answer }}</span>
                    </div>
                    <div class="ec-meta">
                      <el-tag size="small" effect="plain">{{ e.knowledge }}</el-tag>
                      <span class="date">{{ (e.created_at || '').slice(0, 10) }}</span>
                    </div>
                  </div>
                </div>
              </el-collapse-item>
            </el-collapse>
          </el-scrollbar>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="12">
        <el-card class="card" shadow="hover">
          <template #header>
            <div class="card-title">🧩 知识点掌握热力图</div>
            <el-tag size="small" effect="plain" style="margin-left:auto">共 {{ Object.keys(profile.knowledge_states || {}).length }} 个</el-tag>
          </template>
          <div v-if="!hasKnowledge" class="empty-wrap"><el-empty description="暂无知识点数据" /></div>
          <div v-else class="knowledge-grid">
            <div v-for="(ks, id) in profile.knowledge_states" :key="id" class="kg-item"
              :style="{ borderLeftColor: masteryColor(ks.mastery) }">
              <div class="kg-head">
                <div class="kg-name" :title="ks.name">{{ ks.name }}</div>
                <el-tag v-if="ks.mastery < 40" size="small" type="danger" effect="light">薄弱</el-tag>
                <el-tag v-else-if="ks.mastery >= 80" size="small" type="success" effect="light">扎实</el-tag>
                <el-tag v-else size="small" type="warning" effect="light">学习中</el-tag>
              </div>
              <div class="kg-bar"><div class="kg-fill" :style="{ width: ks.mastery + '%', background: masteryColor(ks.mastery) }"></div></div>
              <div class="kg-meta">
                <span class="kg-score">{{ ks.mastery }}分</span>
                <span class="kg-err">❌ {{ ks.error_count || 0 }}</span>
                <span class="kg-ok">✅ {{ ks.correct_count || 0 }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="card diagnosis-card" shadow="hover" id="diagnosis">
      <template #header>
        <div class="card-title">🤖 AI画像诊断书</div>
        <el-button size="small" type="primary" link :loading="diagnosisLoading" @click="regenDiagnosis" style="margin-left:auto">
          <el-icon><Refresh /></el-icon> 重新生成
        </el-button>
      </template>
      <div v-if="!profile.diagnosis && !diagnosisLoading" class="empty-wrap">
        <el-empty description="点击『重新生成』按钮，AI会根据你的画像写专属诊断书">
          <el-button type="primary" @click="regenDiagnosis">生成诊断书</el-button>
        </el-empty>
      </div>
      <div v-else-if="diagnosisLoading" class="diagnosis-loading">
        <el-icon class="is-loading" :size="32" color="#409eff"><Loading /></el-icon>
        <div>AI画像师正在撰写你的专属诊断书…</div>
      </div>
      <div v-else class="diagnosis-md" v-html="renderMarkdown(profile.diagnosis || '')"></div>
    </el-card>

    <el-dialog v-model="showEdit" title="✏️ 编辑我的画像" width="520px">
      <el-form :model="editForm" label-width="90px">
        <el-form-item label="年级">
          <el-select v-model="editForm.grade" placeholder="选择" style="width:100%">
            <el-option v-for="g in grades" :key="g" :label="g" :value="g" />
          </el-select>
        </el-form-item>
        <el-form-item label="教育学段">
          <el-select v-model="editForm.education_level" style="width:100%">
            <el-option label="高中" value="high_school" />
            <el-option label="大学" value="university" />
          </el-select>
        </el-form-item>
        <el-form-item label="认知偏好">
          <el-select v-model="editForm.cognitive_preference" style="width:100%">
            <el-option label="视觉型 🖼️" value="visual" />
            <el-option label="听觉型 🎧" value="auditory" />
            <el-option label="动觉型 🛹" value="kinesthetic" />
            <el-option label="阅读型 📖" value="reading" />
          </el-select>
        </el-form-item>
        <el-form-item label="学科偏好">
          <el-checkbox-group v-model="editForm.subjects">
            <el-checkbox v-for="s in subjectsAll" :key="s" :label="s">{{ s }}</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="学习目标">
          <el-input type="textarea" v-model="editForm.learning_goal" :rows="2" placeholder="例如：数学冲到120分" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEdit = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { RadarChart, LineChart, BarChart, HeatmapChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { Clock, Edit, Refresh, Loading, TrendCharts } from '@element-plus/icons-vue'
import axios from 'axios'

use([RadarChart, LineChart, BarChart, HeatmapChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent, CanvasRenderer])

const API = '/api'
const STUDENT = '1'

const profile = reactive<any>({})
const calendar = ref<any[]>([])
const trend = ref<any[]>([])
const errorTree = reactive<any>({ by_error_type: {}, by_knowledge: {}, total_errors: 0 })
const hoverDay = ref<any>(null)
const errorTreeMode = ref<'error_type' | 'knowledge'>('error_type')
const showEdit = ref(false)
const saving = ref(false)
const diagnosisLoading = ref(false)

const grades = ['初一','初二','初三','高一','高二','高三','高四','大一','大二','大三','大四']
const subjectsAll = ['数学','语文','英语','物理','化学','生物','历史','地理','政治']
const editForm = reactive<any>({
  grade: '', education_level: 'high_school', cognitive_preference: 'visual',
  subjects: [] as string[], learning_goal: ''
})

const ERROR_LABEL_CN: Record<string, string> = {
  concept_unclear: '概念不清',
  calculation_error: '计算失误',
  question_misread: '审题不清',
  transfer_weak: '迁移薄弱',
  memory_fade: '记忆遗忘',
  method_wrong: '方法不当',
  formula_forget: '公式遗忘',
  logic_jump: '逻辑跳步',
}
const ERROR_LABEL_EN: Record<string, string> = {}
for (const [k, v] of Object.entries(ERROR_LABEL_CN)) ERROR_LABEL_EN[v] = k

function cnKey(k: string): string { return ERROR_LABEL_CN[k] || k }
function cnDistribution(raw: Record<string, number> | undefined): Record<string, number> {
  const out: Record<string, number> = {}
  if (!raw) return out
  for (const [k, v] of Object.entries(raw)) out[cnKey(k)] = v
  return out
}

const errorTypeColor: any = {
  '概念不清':'#ef4444','计算失误':'#f97316','审题不清':'#f59e0b',
  '迁移薄弱':'#8b5cf6','记忆遗忘':'#0ea5e9','方法不当':'#10b981',
  '公式遗忘':'#f59e0b','逻辑跳步':'#0d9488',
}

const levelTip = computed(() => {
  const t = profile.level_tier || 'C'
  const tips: any = {
    'S': '🏆 学霸段位，继续保持',
    'A': '🌟 优秀段位，再上一层',
    'B': '📈 中上段位，重点攻坚薄弱点',
    'C': '🔧 起步段位，补齐关键漏洞',
    'D': '🌱 新手段位，从基础开始',
  }
  return tips[t] || tips['C']
})

const insightText = computed(() => {
  const r = profile.radar || []
  if (!r.length) return ''
  const sorted = [...r].sort((a: any, b: any) => b.value - a.value)
  const best = sorted[0]
  const worst = sorted[sorted.length - 1]
  if (!best) return ''
  const bestTxt = `${best.name}${best.value}分（强项）`
  const worstTxt = worst && worst !== best ? `${worst.name}仅${worst.value}分（重点补）` : ''
  const goal = profile.learning_goal ? `· 目标：${profile.learning_goal}` : ''
  return `${bestTxt}${worstTxt ? ' · ' + worstTxt : ''}${goal}`
})

const gradeTagType = computed(() => {
  const g = profile.grade || ''
  if (['高一','高二','高三'].includes(g)) return 'primary'
  if (['大一','大二','大三','大四'].includes(g)) return 'success'
  return 'warning'
})

const heroInitial = computed(() => (profile.username || '同').slice(0, 1))
const scoreDash = computed(() => (profile.composite_score || 0) / 100 * 264)

const hasErrors = computed(() => Object.keys(profile.error_distribution_pct || {}).length > 0)
const hasKnowledge = computed(() => Object.keys(profile.knowledge_states || {}).length > 0)

const topErrorLabel = computed(() => {
  const d = cnDistribution(profile.error_distribution_pct || {})
  if (!Object.keys(d).length) return ''
  return Object.entries(d).sort((a, b) => Number(b[1]) - Number(a[1]))[0][0]
})
const topErrorPct = computed(() => {
  const d: Record<string, any> = (profile.error_distribution_pct as any) || {}
  if (!Object.keys(d).length) return 0
  const s = Object.entries(d).sort((a, b) => Number(b[1]) - Number(a[1]))
  return Math.round(Number(s[0][1]))
})

const calendarCells = computed(() => {
  const cells: any[] = []
  if (!calendar.value.length) return []
  const first = new Date(calendar.value[0]?.date || new Date())
  const firstWeekday = first.getDay()
  for (let i = 0; i < firstWeekday; i++) cells.push(null)
  const today = new Date().toISOString().slice(0, 10)
  calendar.value.forEach((d: any) => {
    const dt = new Date(d.date)
    cells.push({
      ...d,
      day_num: dt.getDate(),
      is_weekend: dt.getDay() === 0 || dt.getDay() === 6,
      is_today: d.date === today,
    })
  })
  return cells
})
const calendarErrors = computed(() => calendar.value.reduce((s: number, d: any) => s + d.errors, 0))
const calendarFeedback = computed(() => calendar.value.reduce((s: number, d: any) => s + d.feedback, 0))

function calendarColor(intensity: number) {
  const t = Math.max(0.08, Math.min(1, intensity || 0))
  const r = Math.round(224 - t * 180)
  const g = Math.round(242 - t * 180)
  const b = Math.round(254 - t * 150)
  return `rgb(${r},${g},${b})`
}

function dimColor(v: number) {
  if (v >= 80) return '#10b981'
  if (v >= 60) return '#0d9488'
  if (v >= 40) return '#f59e0b'
  return '#ef4444'
}

function masteryColor(m: number) {
  if (m >= 80) return '#10b981'
  if (m >= 60) return '#0d9488'
  if (m >= 40) return '#f59e0b'
  return '#ef4444'
}

function cognitiveLabel(p?: string) {
  const map: any = { visual: '视觉型', auditory: '听觉型', kinesthetic: '动觉型', reading: '阅读型' }
  return map[p || 'visual'] || '视觉型'
}

const radarOption = computed(() => {
  const data = profile.radar && profile.radar.length > 0 ? profile.radar :
    [{ name: '知识掌握', value: 50 }, { name: '学习稳定', value: 50 }, { name: '反应速度', value: 50 },
     { name: '错因健康', value: 70 }, { name: '自主学习', value: 50 }, { name: '迁移能力', value: 50 }, { name: '情绪状态', value: 70 }]
  return {
    tooltip: {},
    radar: {
      indicator: data.map((r: any) => ({ name: r.name, max: 100 })),
      center: ['50%', '50%'], radius: '65%',
      axisName: { color: '#475569', fontSize: 12, fontWeight: 600 },
      splitLine: { lineStyle: { color: '#e2e8f0' } },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: '#cbd5e1' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: data.map((r: any) => r.value),
        name: '学习画像',
        areaStyle: { color: 'rgba(99,102,241,0.25)' },
        lineStyle: { color: '#0d9488', width: 2 },
        itemStyle: { color: '#0d9488' },
      }]
    }]
  }
})

const errorRadarOption = computed(() => {
  const raw = cnDistribution(profile.error_distribution_pct || {})
  const allKeys = ['概念不清','计算失误','审题不清','迁移薄弱','记忆遗忘','方法不当','公式遗忘','逻辑跳步']
  const valid = allKeys.filter(k => (raw[k] ?? 0) > 0).length > 0 ? allKeys.filter(k => (raw[k] ?? 0) > 0) : Object.keys(raw)
  if (valid.length === 0) {
    return { title: { text: '暂无错因数据', left: 'center', textStyle: { color: '#94a3b8' } }, xAxis: {}, yAxis: {}, series: [] }
  }
  const values = valid.map(k => Math.round(raw[k] ?? 0))
  const colors = valid.map(k => errorTypeColor[k] || '#94a3b8')
  return {
    tooltip: { trigger: 'item', formatter: (p: any) => `${p.name}: ${p.value}%` },
    radar: {
      indicator: valid.map(k => ({ name: k, max: 100 })),
      center: ['50%', '52%'], radius: '62%',
      axisName: { color: '#475569', fontSize: 12, fontWeight: 600 },
      splitLine: { lineStyle: { color: '#e5e7eb' } },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: '#cbd5e1' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: values, name: '错因分布',
        areaStyle: { color: 'rgba(249,115,22,0.3)' },
        lineStyle: { color: '#f97316', width: 2 },
        itemStyle: { color: (p: any) => colors[p.dataIndex] || '#f97316', borderColor: '#fff', borderWidth: 2 },
        symbolSize: 8,
      }]
    }]
  }
})

const big5Option = computed(() => {
  const b = profile.big_five || { openness: 50, conscientiousness: 50, extraversion: 40, agreeableness: 60, neuroticism: 40 }
  const indicator = [
    { name: '开放性', value: b.openness },
    { name: '尽责性', value: b.conscientiousness },
    { name: '外向性', value: b.extraversion },
    { name: '亲和性', value: b.agreeableness },
    { name: '神经质', value: b.neuroticism },
  ]
  return {
    tooltip: {},
    radar: {
      indicator: indicator.map((r: any) => ({ name: r.name, max: 100 })),
      center: ['50%', '50%'], radius: '62%',
      axisName: { color: '#4338ca', fontSize: 12, fontWeight: 600 },
      splitLine: { lineStyle: { color: '#e0e7ff' } },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: '#ccfbf1' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: indicator.map((r: any) => r.value), name: '性格画像',
        areaStyle: { color: 'rgba(99,102,241,0.25)' },
        lineStyle: { color: '#4338ca', width: 2 },
        itemStyle: { color: '#4338ca' },
      }]
    }]
  }
})

const rhythmOption = computed(() => {
  const empty24 = new Array(24).fill(0) as number[]
  const empty7 = new Array(7).fill(0) as number[]
  const rh: any = profile.rhythm || { hour_count: empty24, weekday_count: empty7, hour_labels: [] }
  const hc: number[] = (rh.hour_count && Array.isArray(rh.hour_count) ? rh.hour_count.slice() : empty24) as number[]
  const maxC = Math.max(...hc, 1)
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 28, right: 12, top: 10, bottom: 22 },
    xAxis: { type: 'category', data: (rh.hour_labels || []).filter((_: any, i: number) => i % 2 === 0),
      axisLabel: { fontSize: 10 },
      axisTick: { show: false }, axisLine: { show: false } },
    yAxis: { type: 'value', min: 0, splitLine: { lineStyle: { color: '#e2e8f0' } }, axisLabel: { fontSize: 10 } },
    series: [{
      type: 'bar', barWidth: 10,
      data: hc.map((v: number, i: number) => ({
        value: v,
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: i >= 22 || i < 6 ? 'rgba(100,116,139,0.35)' :
                   v === maxC && v > 0 ? '#f59e0b' :
                   i >= 8 && i <= 11 || i >= 20 && i <= 22 ? '#0d9488' : '#ccfbf1'
        }
      }))
    }]
  }
})

const peakHourLabels = computed(() => {
  const ph = profile.rhythm?.peak_hours || []
  if (!ph.length) return '—'
  return ph.map((h: number) => `${h}:00`).join(' / ')
})

const recommendSlots = computed(() => {
  const ph = profile.rhythm?.peak_hours || []
  if (!ph.length) return '每晚8:00-10:00（推荐）'
  return ph.slice(0, 2).map((h: number) => `${h}:00-${h+2}:00`).join('、') + '，建议优先安排重难点'
})

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['掌握度','情绪','错题7日均'], top: 0 },
  grid: { left: 40, right: 20, top: 35, bottom: 25 },
  xAxis: { type: 'category', data: trend.value.map((d: any) => d.date.slice(5)), axisLabel: { fontSize: 10 } },
  yAxis: [
    { type: 'value', name: '分', min: 0, max: 100 },
    { type: 'value', name: '情绪', min: 0, max: 100 },
  ],
  series: [
    { name: '掌握度', type: 'line', smooth: true, data: trend.value.map((d: any) => d.mastery ?? null),
      lineStyle: { color: '#0d9488', width: 2 }, itemStyle: { color: '#0d9488' },
      areaStyle: { color: 'rgba(99,102,241,0.15)' } },
    { name: '情绪', type: 'line', yAxisIndex: 1, smooth: true,
      data: trend.value.map((d: any) => d.emotion ?? null),
      lineStyle: { color: '#f472b6', width: 2 }, itemStyle: { color: '#f472b6' } },
    { name: '错题7日均', type: 'line', smooth: true,
      data: trend.value.map((d: any) => d.moving_avg ?? null),
      lineStyle: { color: '#ef4444', width: 1.5, type: 'dashed' },
      itemStyle: { color: '#ef4444' } },
  ]
}))

const errorTreeMap = computed(() => errorTreeMode.value === 'error_type' ? errorTree.by_error_type : errorTree.by_knowledge)

function formatTime(s?: string) {
  if (!s) return '刚刚'
  return s.slice(0, 16).replace('T', ' ')
}

function renderMarkdown(md: string) {
  if (!md) return ''
  let html = md
    .replace(/^### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^📊\s*([^\/]+)\/\s*🔍\s*([^\/]+)\/\s*📈\s*([^\/]+)\/\s*💊\s*(.+)$/m,
      '<div class="diag-grid"><div class="diag-item diag-1"><b>📊 综合评价</b><div>$1</div></div><div class="diag-item diag-2"><b>🔍 错因指纹</b><div>$2</div></div><div class="diag-item diag-3"><b>📈 近期趋势</b><div>$3</div></div><div class="diag-item diag-4"><b>💊 AI处方</b><div>$4</div></div></div>')
    .replace(/^📊\s*(.+)$/gm, '<div class="diag-line">📊 $1</div>')
    .replace(/^🔍\s*(.+)$/gm, '<div class="diag-line">🔍 $1</div>')
    .replace(/^📈\s*(.+)$/gm, '<div class="diag-line">📈 $1</div>')
    .replace(/^💊\s*(.+)$/gm, '<div class="diag-line">💊 $1</div>')
    .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)+/g, '<ul>$&</ul>')
    .replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>')
  if (!html.includes('<p>') && !html.includes('<div class="diag')) html = `<p>${html}</p>`
  return html
}

function scrollTo(id: string) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function loadAll() {
  try {
    const [p, t, c, e] = await Promise.all([
      axios.get(`${API}/profile/${STUDENT}`).catch(() => null),
      axios.get(`${API}/profile/${STUDENT}/trend?days=30`).catch(() => null),
      axios.get(`${API}/profile/${STUDENT}/calendar?days=30`).catch(() => null),
      axios.get(`${API}/profile/${STUDENT}/error-tree`).catch(() => null),
    ])
    if (p?.data?.profile) Object.assign(profile, p.data.profile)
    if (t?.data?.trend) trend.value = t.data.trend
    if (c?.data?.calendar) calendar.value = c.data.calendar
    if (e?.data) {
      Object.assign(errorTree, {
        by_error_type: e.data.by_error_type || {},
        by_knowledge: e.data.by_knowledge || {},
        total_errors: e.data.total_errors || 0,
      })
    }
    Object.assign(editForm, {
      grade: profile.grade || '',
      education_level: profile.education_level || 'high_school',
      cognitive_preference: profile.cognitive_preference || 'visual',
      subjects: (profile.subjects || []).slice(),
      learning_goal: profile.learning_goal || '',
    })
  } catch (err: any) {
    ElMessage.error('加载画像失败：' + (err?.message || ''))
  }
}

async function regenDiagnosis() {
  diagnosisLoading.value = true
  try {
    const res = await axios.get(`${API}/profile/${STUDENT}/diagnosis`)
    if (res.data?.diagnosis) {
      profile.diagnosis = res.data.diagnosis
      ElMessage.success('AI诊断书已更新')
    }
  } catch (e: any) {
    ElMessage.warning('诊断书生成中，稍后自动刷新')
  } finally {
    diagnosisLoading.value = false
  }
}

async function saveEdit() {
  saving.value = true
  try {
    await axios.put(`${API}/profile/${STUDENT}`, editForm)
    ElMessage.success('已保存')
    showEdit.value = false
    await loadAll()
  } finally {
    saving.value = false
  }
}

onMounted(loadAll)
</script>

<style scoped>
.profile-page { padding: 16px; }
.row-gap { margin-bottom: 20px; }
.card { border-radius: 12px; border: none; }
.card :deep(.el-card__header) { padding: 14px 18px; border-bottom: 1px solid #f1f5f9; }
.card-title { font-weight: 600; font-size: 15px; display: flex; align-items: center; gap: 6px; width: 100%; }
.sub-title { margin-left: auto; font-size: 12px; color: #64748b; font-weight: 400; }
.card :deep(.el-card__body) { padding: 18px; }

.profile-hero {
  background: linear-gradient(135deg, #0d9488 0%, #14b8a6 50%, #f59e0b 100%);
  color: #fff; border-radius: 16px; padding: 22px 24px;
  display: flex; justify-content: space-between; align-items: center; gap: 20px;
  margin-bottom: 16px; box-shadow: 0 6px 24px rgba(99,102,241,0.25);
  flex-wrap: wrap;
}
.hero-left { display: flex; gap: 18px; align-items: center; min-width: 260px; }
.avatar-wrap { display: flex; align-items: center; }
.avatar {
  width: 64px; height: 64px; border-radius: 50%;
  background: rgba(255,255,255,0.2); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 28px; font-weight: 700; backdrop-filter: blur(8px);
  border: 2px solid rgba(255,255,255,0.5);
}
.hero-name { font-size: 22px; font-weight: 700; display: flex; align-items: center; gap: 6px; }
.level-badge {
  display: inline-flex; align-items: center; gap: 2px;
  padding: 3px 10px; border-radius: 20px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
  color: #fff; background: rgba(255,255,255,0.25);
  backdrop-filter: blur(6px);
  font-weight: 700; font-size: 13px; line-height: 1.4;
}
.level-badge.level-S { background: linear-gradient(135deg, #fde047, #f59e0b); color: #1f2937; }
.level-badge.level-A { background: linear-gradient(135deg, #a7f3d0, #10b981); color: #064e3b; }
.level-badge.level-B { background: linear-gradient(135deg, #ccfbf1, #0d9488); color: #0f766e; }
.level-badge.level-C { background: linear-gradient(135deg, #fed7aa, #f97316); color: #7c2d12; }
.level-badge.level-D { background: linear-gradient(135deg, #fecaca, #ef4444); color: #7f1d1d; }
.level-badge .lt { font-size: 14px; font-weight: 800; }
.level-badge .lt-label { font-size: 10px; opacity: 0.85; }
.hero-tags { margin: 8px 0; display: flex; gap: 6px; flex-wrap: wrap; }
.hero-tags :deep(.el-tag) { background: rgba(255,255,255,0.2); border-color: rgba(255,255,255,0.3); color: #fff; }
.hero-meta { font-size: 13px; opacity: 0.9; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.hero-meta .sep { opacity: 0.5; }

.hero-center { display: flex; flex-direction: column; align-items: center; }
.score-ring { position: relative; }
.score-ring svg { filter: drop-shadow(0 2px 6px rgba(0,0,0,0.2)); }
.score-text { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #fff; }
.score-num { font-size: 22px; font-weight: 800; line-height: 1; }
.score-label { font-size: 10px; opacity: 0.9; margin-top: 4px; }
.score-tip { font-size: 12px; opacity: 0.9; margin-top: 6px; max-width: 160px; text-align: center; }

.hero-actions { display: flex; flex-direction: column; gap: 10px; }

.ai-insight {
  background: linear-gradient(135deg, #fef9c3 0%, #fde68a 100%);
  color: #78350f; padding: 12px 18px; border-radius: 12px; margin-bottom: 16px;
  font-size: 14px; box-shadow: 0 2px 10px rgba(251,191,36,0.2);
}

.radar-chart { height: 340px; }
.error-chart { height: 340px; }
.big5-chart { height: 300px; }
.rhythm-chart { height: 200px; }
.trend-chart { height: 300px; }

.radar-foot { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px 10px; margin-top: 10px; }
.dim { font-size: 12px; color: #334155; display: flex; justify-content: space-between; background: #f8fafc; padding: 6px 8px; border-radius: 6px; }
.dname { color: #64748b; }
.dval { font-weight: 700; }

.rhythm-foot { margin-top: 8px; font-size: 13px; color: #475569; }

.calendar-wrap { padding: 4px 0; }
.calendar-weekdays {
  display: grid; grid-template-columns: repeat(7, 1fr);
  text-align: center; color: #64748b; font-weight: 600; font-size: 13px;
  margin-bottom: 6px;
}
.calendar-grid {
  display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px;
}
.calendar-grid .cell {
  aspect-ratio: 1; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; color: #1e293b; position: relative;
  cursor: default; transition: transform 0.15s;
  background: #f8fafc;
}
.calendar-grid .cell.empty { background: transparent; }
.calendar-grid .cell.weekend { outline: 1px solid #f472b655; }
.calendar-grid .cell.today { outline: 2px solid #0d9488; }
.calendar-grid .cell.fire { box-shadow: 0 0 0 1px rgba(239,68,68,0.5); }
.calendar-grid .cell:hover:not(.empty) { transform: scale(1.08); z-index: 2; }
.fire-badge { position: absolute; top: -4px; right: -4px; font-size: 10px; }
.calendar-legend { display: flex; align-items: center; justify-content: flex-end; gap: 4px; margin-top: 10px; font-size: 12px; color: #64748b; }
.legend-block { width: 14px; height: 14px; border-radius: 3px; }
.legend-tip { margin-left: auto; font-size: 11px; }
.calendar-hover { margin-top: 8px; font-size: 13px; color: #475569; padding: 6px 10px; background: #f1f5f9; border-radius: 6px; }

.empty-wrap { display: flex; justify-content: center; padding: 30px 0; }

.ec { padding: 10px 12px; margin-bottom: 10px; background: #f8f7f4; border-radius: 8px; border-left: 3px solid #0d9488; }
.ec-q { font-size: 14px; color: #1e293b; font-weight: 500; margin-bottom: 6px; line-height: 1.5; }
.ec-a { font-size: 13px; display: flex; gap: 14px; }
.ec-a .wrong { color: #ef4444; font-weight: 600; }
.ec-a .right { color: #10b981; font-weight: 600; }
.ec-meta { margin-top: 6px; display: flex; align-items: center; gap: 8px; }
.ec-meta .date { color: #94a3b8; font-size: 12px; }

.knowledge-grid { display: flex; flex-direction: column; gap: 10px; max-height: 420px; overflow-y: auto; padding-right: 4px; }
.kg-item { padding: 10px 12px; background: #f8fafc; border-radius: 8px; border-left: 4px solid; }
.kg-head { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.kg-name { font-size: 14px; font-weight: 600; color: #1e293b; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kg-bar { height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; margin-bottom: 6px; }
.kg-fill { height: 100%; border-radius: 3px; transition: width 0.4s; }
.kg-meta { display: flex; align-items: center; gap: 10px; font-size: 12px; color: #64748b; }
.kg-score { font-weight: 600; color: #334155; }

.weak-list { display: flex; flex-direction: column; gap: 12px; padding: 4px 0; }
.weak-row { display: flex; align-items: center; gap: 10px; }
.weak-rank {
  width: 28px; height: 28px; border-radius: 50%;
  background: #eef2ff; color: #4338ca;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 14px; flex-shrink: 0;
}
.weak-main { flex: 1; min-width: 0; }
.weak-name { font-size: 14px; font-weight: 600; color: #1e293b; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.weak-bar { height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; }
.wf { height: 100%; border-radius: 3px; transition: width 0.4s; }
.wf.w0 { background: linear-gradient(90deg, #ef4444, #f97316); }
.wf.w1 { background: linear-gradient(90deg, #f97316, #f59e0b); }
.wf.w2 { background: linear-gradient(90deg, #f59e0b, #eab308); }
.wf.w3 { background: linear-gradient(90deg, #eab308, #84cc16); }
.wf.w4 { background: linear-gradient(90deg, #84cc16, #22c55e); }
.weak-score { text-align: right; flex-shrink: 0; width: 56px; }
.prio { font-weight: 700; color: #4338ca; font-size: 15px; }
.sub { font-size: 11px; color: #64748b; }

.diagnosis-card { margin-bottom: 20px; }
.diagnosis-loading { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 40px; color: #475569; }
.diagnosis-md { font-size: 15px; line-height: 1.8; color: #1e293b; }
.diagnosis-md :deep(h3), .diagnosis-md :deep(h4) { color: #4338ca; margin: 12px 0 8px; font-weight: 700; }
.diagnosis-md :deep(ul) { padding-left: 18px; margin: 6px 0; }
.diagnosis-md :deep(li) { margin-bottom: 4px; }
.diagnosis-md :deep(code) { background: #eef2ff; padding: 1px 6px; border-radius: 4px; color: #4338ca; font-size: 13px; }
.diagnosis-md :deep(b) { color: #1e293b; }
.diagnosis-md :deep(.diag-grid) { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 6px; }
.diagnosis-md :deep(.diag-item) { padding: 12px; border-radius: 10px; background: #f8fafc; border-left: 4px solid #cbd5e1; }
.diagnosis-md :deep(.diag-1) { border-left-color: #0d9488; }
.diagnosis-md :deep(.diag-2) { border-left-color: #f97316; }
.diagnosis-md :deep(.diag-3) { border-left-color: #0ea5e9; }
.diagnosis-md :deep(.diag-4) { border-left-color: #10b981; }
.diagnosis-md :deep(.diag-item b) { display: block; margin-bottom: 4px; font-size: 13px; color: #64748b; }
.diagnosis-md :deep(.diag-item > div) { font-size: 14px; color: #1e293b; }
.diagnosis-md :deep(.diag-line) { padding: 6px 0; border-bottom: 1px dashed #e2e8f0; }

@media (max-width: 768px) {
  .profile-hero { flex-direction: column; gap: 16px; align-items: flex-start; }
  .hero-center { align-self: center; }
  .hero-actions { flex-direction: row; flex-wrap: wrap; }
  .diagnosis-md :deep(.diag-grid) { grid-template-columns: 1fr; }
  .radar-foot { grid-template-columns: repeat(2, 1fr); }
}
</style>
