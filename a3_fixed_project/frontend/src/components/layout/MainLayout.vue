<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-logo">📚</div>
        <span class="brand-name">青藜伴读</span>
      </div>

      <div class="nav-group">
        <div class="nav-group-title">学习中心</div>
        <router-link
          v-for="item in studyNav"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: route.path === item.path || (item.path !== '/' && route.path.startsWith(item.path)) }"
        >
          {{ item.label }}
        </router-link>
      </div>

      <div class="nav-group">
        <div class="nav-group-title">智能工具</div>
        <router-link
          v-for="item in aiNav"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: route.path === item.path }"
        >
          {{ item.label }}
        </router-link>
      </div>

      <div class="bottom">
        <div class="edu-switch">
          <div class="edu-row" @click="eduOpen = !eduOpen">
            <div class="edu-info">
              <span class="edu-label">当前阶段</span>
              <span class="edu-val">{{ eduLabel }}<template v-if="gradeLabel"> · {{ gradeLabel }}</template></span>
            </div>
            <span class="edu-caret" :class="{ open: eduOpen }">▾</span>
          </div>

          <div v-if="eduOpen" class="edu-panel">
            <el-radio-group v-model="eduLevel" size="small" class="edu-radio" @change="onEduChange">
              <el-radio-button v-for="o in levelOptions" :key="o.v" :label="o.v">{{ o.l }}</el-radio-button>
            </el-radio-group>
            <el-select v-model="grade" placeholder="选年级" size="small" class="grade-select" @change="onEduChange">
              <el-option v-for="g in gradeOptions" :key="g.v" :label="g.l" :value="g.v" />
            </el-select>
          </div>
        </div>

        <div class="user-chip">
          <div class="avatar">{{ userInitial }}</div>
          <div class="u-info">
            <span class="u-name">{{ username }}</span>
            <span class="u-sub">{{ eduLabel }} 学员</span>
          </div>
          <button class="logout-btn" @click="handleLogout" title="退出">
            <el-icon size="14"><SwitchButton /></el-icon>
          </button>
        </div>
      </div>
    </aside>

    <main class="main-area">
      <header class="topbar">
        <div class="crumb">
          <span class="crumb-ic">🏠</span>
          <span class="crumb-text">{{ pageTitle }}</span>
          <span class="crumb-sub">{{ today }}</span>
        </div>
        <div class="top-right">
          <div class="status-chip">
            <span class="st-dot"></span>
            <span>AI 系统在线</span>
          </div>
          <div class="clock">{{ clock }}</div>
        </div>
      </header>

      <div class="page-wrap">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { SwitchButton } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

const username = ref(localStorage.getItem('username') || '同学')
const userInitial = computed(() => (username.value || 'U').slice(0, 1))
const clock = ref('')
let timer: number | null = null

const eduOpen = ref(false)
const eduLevel = ref(localStorage.getItem('education_level') || 'high_school')
const grade = ref(localStorage.getItem('grade') || '')

const levelOptions = [
  { v: 'high_school', l: '高中' },
  { v: 'university', l: '大学' }
]

const gradeMap: Record<string, { v: string; l: string }[]> = {
  high_school: [
    { v: '10', l: '高一' }, { v: '11', l: '高二' }, { v: '12', l: '高三' }
  ],
  university: [
    { v: 'c1', l: '大一' }, { v: 'c2', l: '大二' }, { v: 'c3', l: '大三' }, { v: 'c4', l: '大四' }
  ]
}

const labelOf = (v: string) => levelOptions.find(o => o.v === v)?.l || v
const eduLabel = computed(() => labelOf(eduLevel.value))
const gradeLabel = computed(() => {
  const list = gradeMap[eduLevel.value] || []
  const found = list.find(g => g.v === grade.value)
  return found?.l || ''
})
const gradeOptions = computed(() => gradeMap[eduLevel.value] || [])

function tickClock() {
  const d = new Date()
  clock.value = d.toLocaleTimeString('zh-CN', { hour12: false })
}

const today = computed(() => {
  const d = new Date()
  const w = ['周日','周一','周二','周三','周四','周五','周六'][d.getDay()]
  return `${d.getMonth() + 1}月${d.getDate()}日 · ${w}`
})

const studyNav = [
  { path: '/', label: '📊 学习总览' },
  { path: '/profile', label: '🧠 学习画像' },
  { path: '/planning', label: '📅 学习规划' },
  { path: '/resources', label: '📖 知识练习' }
]

const aiNav = [
  { path: '/knowledge', label: '📚 知识库' },
  { path: '/feedback', label: '🧾 错题本' },
  { path: '/tutoring', label: '💬 AI 答疑' },
  { path: '/workflow', label: '⚙️ 工作流' }
]

const pageTitle = computed(() => {
  const map: Record<string, string> = {
    '/': '学习总览',
    '/profile': '学习画像',
    '/planning': '学习规划',
    '/resources': '知识练习',
    '/knowledge': '知识库',
    '/feedback': '错题本',
    '/tutoring': 'AI 答疑',
    '/workflow': 'AI 工作流'
  }
  return map[route.path] || '学习总览'
})

async function onEduChange() {
  const sid = localStorage.getItem('student_id')
  if (sid) {
    try {
      await fetch(`/api/db/student/${sid}/education`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ education_level: eduLevel.value, grade: grade.value })
      })
    } catch {}
  }
  localStorage.setItem('education_level', eduLevel.value)
  localStorage.setItem('grade', grade.value)
  ElMessage.success(`已切换到 ${eduLabel.value}${gradeLabel.value ? ' · ' + gradeLabel.value : ''}`)
}

function handleLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('student_id')
  localStorage.removeItem('username')
  router.push('/login')
}

onMounted(() => {
  tickClock()
  timer = window.setInterval(tickClock, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  background: #f5f7fa;
  font-family: ui-sans-serif, -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: #1a2040;
  overflow: hidden;
}

.sidebar {
  width: 210px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: #fbf9f4;
  border-right: 1px solid #efe9dd;
  padding: 22px 16px 16px;
  position: relative;
}

.brand {
  display: flex; align-items: center; gap: 10px;
  padding: 2px 2px 20px;
  margin-bottom: 18px;
  border-bottom: 1px dashed #e6dfcf;
}
.brand-logo {
  width: 30px; height: 30px; border-radius: 10px;
  background: linear-gradient(135deg, #0d9488, #0ea5a3);
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; color: #fff;
  box-shadow: 0 2px 10px rgba(13,148,136,.35);
}
.brand-name {
  font-size: 15px; font-weight: 800; letter-spacing: 2px;
  color: #0f766e;
}

.nav-group { display: flex; flex-direction: column; gap: 2px; margin-bottom: 14px; }
.nav-group-title {
  font-size: 10px; font-weight: 700; letter-spacing: 3px; color: #a59878;
  padding: 8px 10px 6px;
  text-transform: uppercase;
}

.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  color: #6b7a90;
  font-size: 13px; letter-spacing: .4px;
  border: 1px solid transparent;
  transition: all .2s ease;
  text-decoration: none;
}
.nav-item:hover {
  color: #0f766e;
  background: #ecfdf9;
  border-color: #d0f5ed;
}
.nav-item.active {
  color: #fff;
  background: linear-gradient(90deg, #0d9488 0%, #0ea5a3 100%);
  border-color: #0d9488;
  box-shadow: 0 2px 10px rgba(13,148,136,.25);
  font-weight: 600;
}

.bottom {
  margin-top: auto;
  padding-top: 14px;
  border-top: 1px dashed #e6dfcf;
}
.edu-switch { margin-bottom: 10px; }
.edu-row {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px;
  background: #faf7f0;
  border: 1px solid #efe9dd;
  border-radius: 10px;
  cursor: pointer;
}
.edu-info { display: flex; flex-direction: column; flex: 1; min-width: 0; }
.edu-label { font-size: 10px; color: #a59878; letter-spacing: 2px; text-transform: uppercase; font-weight: 600; }
.edu-val { font-size: 12px; font-weight: 700; color: #3f3a2d; }
.edu-caret { color: #a59878; font-size: 12px; transition: transform .2s ease; }
.edu-caret.open { transform: rotate(180deg); }
.edu-panel {
  margin-top: 6px;
  padding: 8px;
  background: #faf7f0;
  border: 1px solid #efe9dd;
  border-radius: 10px;
}
.edu-radio { margin-bottom: 6px; width: 100%; }
.edu-radio :deep(.el-radio-button__inner) {
  border-radius: 6px!important; padding: 6px 10px; font-size: 12px;
}
.edu-radio :deep(.el-radio-button__original-radio):checked + .el-radio-button__inner {
  background: #0d9488!important; border-color: #0d9488!important; color: #fff!important;
}
.grade-select { width: 100%; }
.grade-select :deep(.el-input__wrapper) { border-radius: 6px; }

.user-chip {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 10px;
  background: #faf7f0;
  border: 1px solid #efe9dd;
  border-radius: 10px;
}
.avatar {
  width: 26px; height: 26px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #0d9488, #0ea5a3);
  font-weight: 700; color: #fff; font-size: 12px; flex-shrink: 0;
}
.u-info { display: flex; flex-direction: column; flex: 1; min-width: 0; }
.u-name { font-size: 12px; font-weight: 700; color: #3f3a2d; }
.u-sub { font-size: 10px; color: #a59878; letter-spacing: 1px; }
.logout-btn {
  width: 26px; height: 26px; border-radius: 6px;
  border: 1px solid #efe9dd;
  background: #fff; color: #a59878;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all .2s ease;
}
.logout-btn:hover { color: #e11d48; border-color: #fecaca; background: #fff1f2; }

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #fbf9f4;
}

.topbar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 28px;
  background: #fff;
  border-bottom: 1px solid #efe9dd;
  position: sticky; top: 0; z-index: 10;
}
.crumb { display: flex; align-items: center; gap: 8px; }
.crumb-ic { font-size: 16px; }
.crumb-text { font-size: 16px; font-weight: 800; letter-spacing: 1px; color: #3f3a2d; }
.crumb-sub { font-size: 11px; color: #a59878; letter-spacing: 1px; }

.top-right { display: flex; align-items: center; gap: 14px; }
.status-chip {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 12px;
  background: #ecfdf9;
  border: 1px solid #b8eadf;
  border-radius: 999px;
  font-size: 11px; font-weight: 600; color: #0d9488; letter-spacing: 1px;
}
.st-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #0d9488;
  box-shadow: 0 0 8px rgba(13,148,136,.7);
}

.clock {
  font-family: ui-monospace, monospace;
  font-size: 13px; color: #a59878; letter-spacing: 1px;
}

.page-wrap {
  flex: 1;
  overflow-y: auto;
  padding: 20px 28px 28px;
}
.page-wrap::-webkit-scrollbar { width: 6px; }
.page-wrap::-webkit-scrollbar-thumb { background: rgba(165,152,120,.3); border-radius: 999px; }
.page-wrap::-webkit-scrollbar-track { background: transparent; }
</style>
