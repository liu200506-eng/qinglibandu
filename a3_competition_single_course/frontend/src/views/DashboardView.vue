<template>
  <div class="dash">
    <section class="hero">
      <div class="hero-orb"></div>
      <div class="hero-main">
        <div class="hero-greet"><span class="wave">👋</span>{{ greet }}</div>
        <div class="hero-h1">保持专注，稳步提升</div>
        <div class="hero-meta">
          <span><b>{{ stats.todayMinutes }}</b> 分钟 · 今日学习</span>
          <span class="dot">·</span>
          <span><b>{{ weekTotal }}</b>h · 本周累计</span>
          <span class="dot">·</span>
          <span>{{ today }}</span>
        </div>
      </div>

      <div class="hero-ring">
        <div class="ring" v-for="s in ringStats" :key="s.label">
          <svg viewBox="0 0 40 40" class="ring-svg">
            <circle cx="20" cy="20" r="16" fill="none" stroke="#eef0ed" stroke-width="3" />
            <circle cx="20" cy="20" r="16" fill="none"
              :stroke="s.color" stroke-width="3" stroke-linecap="round"
              stroke-dasharray="`${s.value*1.005} 100.5`"
              transform="rotate(-90 20 20)" />
          </svg>
          <div class="ring-center">
            <div class="ring-val" :style="{ color: s.color }">{{ s.value }}</div>
            <div class="ring-lbl">{{ s.label }}</div>
          </div>
        </div>
      </div>
    </section>

    <section class="sum">
      <div class="sum-card" v-for="s in sumStats" :key="s.label">
        <div class="sum-ic" :style="{ background: s.bg, color: s.color }">{{ s.ic }}</div>
        <div class="sum-body">
          <div class="sum-num" :style="{ color: s.color }">{{ s.value }}</div>
          <div class="sum-lbl">{{ s.label }}</div>
        </div>
      </div>
    </section>

    <section class="grid">
      <div class="col">
        <div class="card">
          <div class="card-hd">
            <div class="card-tit">📡 学习能力雷达</div>
            <div class="card-sb">七维能力 · 目标 80</div>
          </div>
          <div ref="radarRef" class="chart"></div>
        </div>

        <div class="card">
          <div class="card-hd">
            <div class="card-tit">🗓️ 本周学习热力</div>
            <div class="card-sb">时长分布</div>
          </div>
          <div class="heat">
            <div v-for="(d, i) in week" :key="i" class="h-day">
              <div class="h-bars">
                <div class="h-bar" :style="{ height: Math.max(d.hours*14, 6)+'px', background: d.color }"></div>
                <div class="h-bar-bg" :style="{ height: '70px' }"></div>
              </div>
              <div class="h-lbl">{{ d.label }}</div>
              <div class="h-h">{{ d.hours }}h</div>
            </div>
          </div>
        </div>
      </div>

      <div class="col">
        <div class="card">
          <div class="card-hd">
            <div class="card-tit">🧭 今日任务</div>
            <div class="card-sb">{{ doneCount }}/{{ tasks.length }} 完成</div>
          </div>
          <div class="tasks">
            <div v-for="(t, i) in tasks" :key="i" class="t" :class="{ done: t.done, active: t.active }">
              <div class="t-state">
                <span v-if="t.done">✓</span>
                <span v-else-if="t.active" class="t-spin"></span>
                <span v-else>○</span>
              </div>
              <div class="t-bd">
                <div class="t-t">{{ t.title }}</div>
                <div class="t-sub">
                  <span>{{ t.time }}</span>
                  <span class="t-tag" :style="{ background: t.color+'1a', color: t.color }">{{ t.tag }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-hd">
            <div class="card-tit">🧠 AI 学习建议</div>
          </div>
          <div class="advices">
            <div v-for="(a, i) in advices" :key="i" class="ad" :class="{ hot: a.priority === 'high' }">
              <span class="ad-ic">{{ a.ic }}</span>
              <div class="ad-bd">
                <div class="ad-t">{{ a.title }}</div>
                <div class="ad-r">{{ a.reason }}</div>
              </div>
              <span class="ad-go" @click="$router.push(a.path)">去</span>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-hd">
            <div class="card-tit">⚠️ 薄弱知识点</div>
            <div class="card-sb" v-if="weakPoints.length">{{ weakPoints.length }} 个</div>
          </div>
          <div v-if="weakPoints.length" class="weak">
            <div v-for="p in weakPoints.slice(0, 5)" :key="p.name" class="wp">
              <span class="wp-nm">{{ p.name }}</span>
              <div class="wp-bar"><div class="wp-fill" :style="{ width: p.pct+'%', background: p.color }"></div></div>
              <span class="wp-pct" :style="{ color: p.color }">{{ p.pct }}%</span>
            </div>
          </div>
          <div v-else class="empty">✓ 暂无薄弱知识点，继续保持！</div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import * as echarts from 'echarts'
import { useProfileStore } from '@/stores/profile'

const profileStore = useProfileStore()
const radarRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

const stats = reactive({
  focus: 82, accuracy: 78, knowledgeMastery: 75,
  emotionalState: 82, efficiency: 78, todayMinutes: 135
})

const greet = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了，注意休息'
  if (h < 11) return '早上好，元气满满'
  if (h < 14) return '中午好，坚持就是胜利'
  if (h < 18) return '下午好，冲刺时间到'
  return '晚上好，今日收尾加油'
})

const today = computed(() => {
  const d = new Date()
  return `${d.getMonth()+1}月${d.getDate()}日 ${['周日','周一','周二','周三','周四','周五','周六'][d.getDay()]}`
})

const ringStats = computed(() => [
  { label: '专注度', value: stats.focus, color: '#0d9488', trend: 3 },
  { label: '正确率', value: stats.accuracy, color: '#f59e0b', trend: 1 },
  { label: '掌握度', value: stats.knowledgeMastery, color: '#059669', trend: 5 },
  { label: '情绪', value: stats.emotionalState, color: '#0ea5e9', trend: -1 }
])

const sumStats = computed(() => [
  { ic: '📚', label: '累计知识点', value: '128', color: '#0d9488', bg: '#f0fdfa', bar: 72 },
  { ic: '✍️', label: '完成习题', value: '342', color: '#f59e0b', bg: '#fffbeb', bar: 80 },
  { ic: '🎬', label: '学习视频', value: '24', color: '#0ea5e9', bg: '#f0f9ff', bar: 60 },
  { ic: '💬', label: 'AI 问答', value: '58', color: '#059669', bg: '#f0fdf4', bar: 66 }
])

const week = ref([
  { label: '一', hours: 2.5, color: '#0d9488' },
  { label: '二', hours: 3.0, color: '#0f766e' },
  { label: '三', hours: 1.5, color: '#0d9488' },
  { label: '四', hours: 4.0, color: '#059669' },
  { label: '五', hours: 2.0, color: '#f59e0b' },
  { label: '六', hours: 5.5, color: '#059669' },
  { label: '日', hours: 3.5, color: '#0f766e' }
])

const weekTotal = computed(() => week.value.reduce((a,b)=>a+b.hours,0).toFixed(1))

const tasks = ref([
  { title: '函数奇偶性习题 15 道', time: '09:00', tag: '练习', color: '#0d9488', done: true, active: false },
  { title: '导数链式法则 · 苏格拉底辅导', time: '11:30', tag: '辅导', color: '#0ea5e9', done: true, active: false },
  { title: '错题复盘 · 本周', time: '14:00', tag: '复盘', color: '#f59e0b', done: false, active: true },
  { title: '三角函数 PPT 整理', time: '16:30', tag: '资源', color: '#059669', done: false, active: false },
  { title: '每日巩固训练', time: '20:00', tag: '训练', color: '#0d9488', done: false, active: false }
])

const doneCount = computed(() => tasks.value.filter(t => t.done).length)

const advices = ref([
  { ic: '🔥', title: '三角函数需重点巩固', reason: '近3次正确率 42%，建议用苏格拉底式追问辅导', btn: '去 AI 答疑', path: '/tutoring', priority: 'high' },
  { ic: '📖', title: '今日推荐：导数链式法则 15 题', reason: '你已掌握基础导数，进阶训练能推进迁移能力', btn: '开始练习', path: '/resources' },
  { ic: '😴', title: '学习时长已达 2h+，建议休息 5 分钟', reason: '疲劳积累中，深呼吸或站起走动', btn: '好的', path: '/' }
])

const weakPoints = ref<{ name: string; mastery: number; pct: number; color: string }[]>([])

function colorOf(v: number) {
  if (v >= 0.7) return '#059669'
  if (v >= 0.4) return '#f59e0b'
  return '#dc2626'
}

function loadData() {
  try { profileStore.fetchProfile('default') } catch {}
  if (profileStore.profile) {
    const p = profileStore.profile as any
    stats.knowledgeMastery = Math.round(p.knowledge_mastery || 75)
    stats.focus = Math.round(p.learning_stability || 70)
    stats.accuracy = Math.round(p.response_speed || 82)
    stats.emotionalState = Math.round(p.emotional_state || 80)
    const states = typeof p.knowledge_states === 'string' ? JSON.parse(p.knowledge_states) : (p.knowledge_states || {})
    weakPoints.value = Object.values(states)
      .filter((s: any) => (s.mastery || 0) < 0.6)
      .sort((a: any, b: any) => (a.mastery || 0) - (b.mastery || 0))
      .slice(0, 5)
      .map((s: any) => ({
        name: s.name || '',
        mastery: s.mastery || 0,
        pct: Math.round((s.mastery || 0) * 100),
        color: colorOf((s.mastery || 0))
      }))
  }
}

function makeRadar() {
  const real = profileStore.profile as any
  const base = real ? {
    knowledge_mastery: real.knowledge_mastery,
    learning_stability: real.learning_stability,
    response_speed: real.response_speed,
    error_pattern_score: real.error_pattern_score,
    self_driven_score: real.self_driven_score,
    transfer_ability: real.transfer_ability,
    emotional_state: real.emotional_state
  } : { knowledge_mastery:75, learning_stability:70, response_speed:82, error_pattern_score:65, self_driven_score:60, transfer_ability:55, emotional_state:80 }
  const data = [
    { name: '知识掌握', value: base.knowledge_mastery },
    { name: '学习稳定', value: base.learning_stability },
    { name: '反应速度', value: base.response_speed },
    { name: '错因健康', value: base.error_pattern_score },
    { name: '自主学习', value: base.self_driven_score },
    { name: '迁移能力', value: base.transfer_ability },
    { name: '情绪状态', value: base.emotional_state }
  ]
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', backgroundColor: '#1f2937', borderColor: 'transparent', textStyle: { color: '#fff' } },
    radar: {
      indicator: data.map(d => ({ name: d.name, max: 100 })),
      radius: '72%',
      center: ['50%', '52%'],
      splitNumber: 5,
      axisName: { color: '#64748b', fontSize: 11, fontFamily: 'ui-sans-serif' },
      splitLine: { lineStyle: { color: 'rgba(13,148,136,.12)' } },
      splitArea: { show: true, areaStyle: { color: ['rgba(240,253,250,.6)', 'rgba(255,255,255,.8)'] } },
      axisLine: { lineStyle: { color: 'rgba(13,148,136,.18)' } }
    },
    series: [{
      type: 'radar',
      data: [
        { value: data.map(() => 80), name: '目标 80', symbol: 'none', lineStyle: { width: 1, color: 'rgba(245,158,11,.5)', type: 'dashed' }, areaStyle: { color: 'rgba(245,158,11,.05)' } },
        { value: data.map(d => d.value), name: '当前', symbol: 'circle', symbolSize: 6, lineStyle: { width: 2, color: '#0d9488' }, areaStyle: { color: 'rgba(13,148,136,.22)' }, itemStyle: { color: '#0d9488', borderColor: '#fff', borderWidth: 1 } }
      ]
    }]
  }
}

function redraw() {
  if (!chartInstance || !radarRef.value) return
  chartInstance.resize()
  chartInstance.setOption(makeRadar(), true)
}

onMounted(() => {
  if (radarRef.value) {
    chartInstance = echarts.init(radarRef.value, undefined, { renderer: 'canvas' })
    chartInstance.setOption(makeRadar())
    window.addEventListener('resize', redraw)
  }
  loadData()
  setTimeout(redraw, 120)
})

onUnmounted(() => {
  window.removeEventListener('resize', redraw)
  chartInstance?.dispose()
})
</script>

<style scoped>
.dash { display: flex; flex-direction: column; gap: 14px; color: var(--c-text, #1e293b); }

.hero {
  position: relative;
  display: flex; align-items: center; justify-content: space-between; gap: 20px;
  padding: 24px 28px;
  background: linear-gradient(135deg, #f0fdfa 0%, #ecfdf5 40%, #ffffff 100%);
  border: 1px solid #ccfbf1;
  border-radius: 18px;
  overflow: hidden;
}
.hero-orb {
  position: absolute; right: -40px; top: -40px;
  width: 200px; height: 200px; border-radius: 50%;
  background: radial-gradient(circle, rgba(13,148,136,.14) 0%, rgba(13,148,136,0) 70%);
  pointer-events: none;
}
.hero-orb::after {
  content: ''; position: absolute; left: 40px; bottom: -80px;
  width: 140px; height: 140px; border-radius: 50%;
  background: radial-gradient(circle, rgba(245,158,11,.1) 0%, rgba(245,158,11,0) 70%);
}
.hero-main { position: relative; z-index: 1; }
.hero-greet { font-size: 12px; color: #0d9488; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; display: flex; align-items: center; gap: 6px; }
.wave { display: inline-block; animation: wobble 2.4s ease-in-out infinite; transform-origin: 70% 70%; }
@keyframes wobble { 0%,100%{transform:rotate(0)}20%{transform:rotate(16deg)}40%{transform:rotate(-10deg)}60%{transform:rotate(8deg)}80%{transform:rotate(-4deg)} }
.hero-h1 { font-size: 26px; font-weight: 800; letter-spacing: 1px; color: #0f172a; margin-top: 6px; }
.hero-meta { font-size: 12px; color: #64748b; margin-top: 8px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.hero-meta b { color: #0d9488; font-weight: 800; }
.dot { color: #cbd5e1; }

.hero-ring { display: flex; gap: 12px; position: relative; z-index: 1; }
.ring {
  position: relative;
  width: 76px; height: 76px;
  background: #fff; border-radius: 14px;
  border: 1px solid #e7e5e2;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 16px rgba(0,0,0,.04);
}
.ring-svg { position: absolute; inset: 4px; width: calc(100% - 8px); height: calc(100% - 8px); }
.ring-center { text-align: center; }
.ring-val { font-size: 18px; font-weight: 800; font-family: var(--font-mono, monospace); line-height: 1; }
.ring-lbl { font-size: 9px; color: #94a3b8; letter-spacing: 1px; margin-top: 3px; font-weight: 600; }

.sum { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
@media (max-width: 1100px) { .sum { grid-template-columns: repeat(2, 1fr); } }
.sum-card {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px;
  background: #fff; border: 1px solid #e7e5e2; border-radius: 14px;
  box-shadow: 0 2px 10px rgba(10,15,30,.04);
  transition: transform .2s ease, box-shadow .2s ease;
}
.sum-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(13,148,136,.1); }
.sum-ic {
  width: 40px; height: 40px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; flex-shrink: 0;
}
.sum-num { font-size: 22px; font-weight: 800; font-family: var(--font-mono, monospace); letter-spacing: .5px; line-height: 1; }
.sum-lbl { font-size: 11px; color: #64748b; letter-spacing: .3px; margin-top: 3px; }

.grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 14px; }
@media (max-width: 1100px) { .grid { grid-template-columns: 1fr; } }
.col { display: flex; flex-direction: column; gap: 14px; }

.card {
  background: #fff; border: 1px solid #e7e5e2; border-radius: 16px;
  padding: 18px 20px;
  box-shadow: 0 2px 12px rgba(10,15,30,.04);
  transition: box-shadow .2s ease, transform .2s ease;
}
.card:hover { box-shadow: 0 8px 28px rgba(13,148,136,.08); }
.card-hd { display: flex; align-items: center; margin-bottom: 14px; }
.card-tit { font-size: 14px; font-weight: 800; letter-spacing: .5px; color: #0f172a; }
.card-sb { margin-left: auto; font-size: 11px; color: #94a3b8; letter-spacing: 1px; }

.chart { height: 290px; }

.heat { display: flex; align-items: flex-end; justify-content: space-between; gap: 6px; height: 160px; padding: 4px 0; }
.h-day { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6px; }
.h-bars { position: relative; display: flex; flex-direction: column; align-items: center; }
.h-bar { width: 22px; max-width: 22px; min-height: 4px; border-radius: 6px 6px 3px 3px; z-index: 1; transition: transform .2s ease; }
.h-bar:hover { transform: scaleY(1.08); }
.h-bar-bg { position: absolute; bottom: 0; width: 22px; background: #f1f5f4; border-radius: 4px; z-index: 0; }
.h-lbl { font-size: 11px; color: #64748b; font-weight: 600; }
.h-h { font-size: 10px; color: #94a3b8; font-family: var(--font-mono, monospace); }

.tasks { display: flex; flex-direction: column; gap: 8px; }
.t {
  display: flex; align-items: center; gap: 12px;
  padding: 11px 12px;
  border-radius: 10px;
  background: #fafaf8; border: 1px solid #eef0ed;
  transition: all .2s ease;
}
.t:hover { background: #f0fdfa; border-color: #ccfbf1; transform: translateX(2px); }
.t.done { opacity: .5; background: #fafaf8; }
.t.active { background: #f0fdfa; border-color: #0d9488; box-shadow: 0 0 16px rgba(13,148,136,.1); }
.t-state {
  width: 22px; height: 22px; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  background: #eef0ed; color: #94a3b8; font-size: 11px; font-weight: 700; flex-shrink: 0;
}
.t.done .t-state { background: #059669; color: #fff; }
.t.active .t-state { background: #0d9488; color: #fff; }
.t.done .t-t { text-decoration: line-through; color: #94a3b8; }
.t-spin { width: 12px; height: 12px; border-radius: 50%; border: 2px solid rgba(255,255,255,.4); border-top-color: #fff; animation: spin 1s linear infinite; }
@keyframes spin { from{transform:rotate(0)}to{transform:rotate(360deg)} }
.t-bd { flex: 1; min-width: 0; }
.t-t { font-size: 13px; font-weight: 600; color: #0f172a; letter-spacing: .3px; }
.t-sub { margin-top: 3px; display: flex; align-items: center; gap: 8px; font-size: 11px; color: #94a3b8; }
.t-tag { font-size: 10px; font-weight: 600; letter-spacing: 1px; padding: 1px 10px; border-radius: 999px; }

.advices { display: flex; flex-direction: column; gap: 10px; }
.ad {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 12px; border-radius: 12px;
  background: #fafaf8; border: 1px solid #eef0ed;
  transition: all .2s ease;
}
.ad:hover { background: #f0fdfa; border-color: #ccfbf1; transform: translateX(2px); }
.ad.hot { border-color: #fed7aa; background: #fffbeb; }
.ad.hot:hover { border-color: #fdba74; box-shadow: 0 4px 16px rgba(245,158,11,.15); }
.ad-ic { font-size: 20px; flex-shrink: 0; }
.ad-bd { flex: 1; min-width: 0; }
.ad-t { font-size: 13px; font-weight: 600; color: #0f172a; }
.ad-r { font-size: 11px; color: #64748b; line-height: 1.5; margin-top: 3px; }
.ad-go {
  flex-shrink: 0; padding: 4px 14px;
  background: #0d9488; color: #fff;
  font-size: 12px; font-weight: 600;
  border-radius: 999px; cursor: pointer;
  transition: all .2s ease;
}
.ad-go:hover { background: #0f766e; transform: translateY(-1px); box-shadow: 0 4px 14px rgba(13,148,136,.3); }

.weak { display: flex; flex-direction: column; gap: 8px; }
.wp {
  display: grid; grid-template-columns: 1fr auto auto;
  gap: 10px; align-items: center;
  padding: 8px 10px;
  background: #fafaf8; border-radius: 8px;
  transition: background .2s ease;
}
.wp:hover { background: #f0fdfa; }
.wp-nm { font-size: 12px; font-weight: 600; color: #0f172a; }
.wp-bar { width: 100%; height: 6px; background: #eef0ed; border-radius: 999px; overflow: hidden; }
.wp-fill { height: 100%; border-radius: 999px; transition: width .6s ease; }
.wp-pct { font-size: 11px; font-family: var(--font-mono, monospace); font-weight: 700; min-width: 32px; text-align: right; }

.empty { padding: 24px; text-align: center; color: #64748b; font-size: 13px; }
</style>
