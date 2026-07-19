﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿<template>
  <div class="resource-view">
    <el-card class="search-card" shadow="never">
      <div class="card-header">
        <span class="header-dot" />
        <span>🎯 开始知识练习 — 先选择你正在学习的阶段与科目</span>
        <span class="header-sub">选择好之后，左侧会自动生成知识目录，右侧展示对应章节的讲义 / 习题 / 考试检测</span>
      </div>

      <div style="margin-top:14px;display:flex;align-items:center;gap:14px;flex-wrap:wrap">
        <el-form-item label="示范课程" label-width="76px" style="margin:0">
          <el-tag type="success" effect="dark" size="large">大学 · 计算机网络</el-tag>
        </el-form-item>

        <el-form-item v-if="educationLevel === 'high_school'" label="年级" label-width="60px" style="margin:0">
          <el-radio-group v-model="grade" class="grade-group" size="default">
            <el-radio-button v-for="g in highSchoolGrades" :key="g" :value="g">{{ g }}</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-else label="大学方向" label-width="76px" style="margin:0">
          <el-radio-group v-model="grade" class="grade-group" size="default">
            <el-radio-button v-for="g in universityGrades" :key="g" :value="g">{{ g }}</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="科目" label-width="44px" style="margin:0;min-width:240px">
          <el-select
            v-model="selectedSubject"
            placeholder="选择科目"
            style="width:100%"
            :disabled="!subjectOptions.length"
          >
            <el-option v-for="s in subjectOptions" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>

        <el-button
          v-if="activeNode"
          class="generate-btn"
          style="margin-left:auto"
          plain
          :disabled="isGenerating"
          @click="handleGenerate"
        >
          <el-icon><DataAnalysis /></el-icon>
          <span>{{ isGenerating ? generationMessage : '重新生成本知识点' }}</span>
        </el-button>
      </div>
    </el-card>

    <div v-if="activeNode" class="now-learning-bar">
      <span class="now-learning-label">正在学习</span>
      <span class="now-learning-subject">{{ selectedSubject }}</span>
      <span class="now-learning-arrow">→</span>
      <span class="now-learning-chain">{{ nodeChainText }}</span>
      <span class="now-learning-tag">掌握度</span>
      <span class="now-learning-streak">🔥 {{ masteryLabel }}</span>
    </div>

    <div class="main-grid">
      <div class="left-col">
        <el-card class="tree-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="header-dot" />
              <span>📖 {{ selectedSubject || '请选择科目' }} · 知识目录</span>
              <span class="header-sub">{{ chapterList.length }} 个章节 · {{ totalNodeCount }} 个知识点</span>
            </div>
          </template>

          <div class="tree-search">
            <el-input
              v-model="filterKey"
              placeholder="🔍 在本学科内搜索章节 / 知识点"
              clearable
              size="small"
            />
          </div>

          <div class="dir-tree">
            <div v-for="chapter in filteredChapters" :key="chapter.id" class="dir-chapter">
              <div
                class="dir-chapter-head"
                :class="{ 'dir-chapter-active': !activeNode && activeChapter === chapter.id }"
                @click="toggleChapter(chapter.id)"
              >
                <el-icon class="dir-caret" :size="12">
                  <CaretTop v-if="chapterOpenMap[chapter.id]" />
                  <CaretBottom v-else />
                </el-icon>
                <span class="dir-chapter-name">{{ chapter.name }}</span>
                <span class="dir-chapter-count">{{ chapter.node_count }}</span>
                <span class="dir-chapter-dot" :style="{ background: chapter.color }" />
              </div>

              <div v-if="chapterOpenMap[chapter.id]" class="dir-sections">
                <div v-for="section in chapter.sections" :key="section.id" class="dir-section">
                  <div
                    class="dir-section-line"
                    :class="{ 'dir-section-active': activeNode?.section_id === section.id && !activeNode }"
                    @click="selectSection(section)"
                  >
                    <el-icon class="sec-caret" :size="10"><ArrowDown /></el-icon>
                    <span class="sec-name">{{ section.name }}</span>
                    <span class="sec-count">{{ section.node_count }}</span>
                    <span class="sec-mastery-dot" :style="{ background: masteryColor(section.mastery) }" />
                    <span class="sec-mark" @click.stop="markMastery(section.id, 'section')">
                      {{ section.mastery === 'mastered' ? '✅' : section.mastery === 'learning' ? '📘' : '⏳' }}
                    </span>
                  </div>

                  <div class="dir-leaf-wrap">
                    <div
                      v-for="leaf in section.children"
                      :key="leaf.id"
                      class="dir-leaf-line"
                      :class="{ 'dir-leaf-active': activeNode?.id === leaf.id }"
                      @click.stop="handleNodeClick(leaf)"
                    >
                      <span class="leaf-dot" :style="{ background: masteryColor(leaf.mastery) }" />
                      <span class="leaf-name">{{ leaf.name }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <el-card v-if="activeNode" class="tree-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="header-dot" />
              <span>🗺️ 学习路径 & 掌握度</span>
              <span class="header-sub">{{ selectedSubject }} · {{ masteryLabel }}</span>
            </div>
          </template>
          <el-progress type="dashboard" :percentage="masteryPercent" :width="140" :color="masteryProgressColor" />
          <div class="progress-mini">
            <div>✅ 已掌握 <b>{{ masteredCount }}</b></div>
            <div>📘 学习中 <b>{{ learningCount }}</b></div>
            <div>⏳ 未开始 <b>{{ pendingCount }}</b></div>
          </div>
        </el-card>
      </div>

      <div class="right-col">
        <el-tabs v-model="activeTab" class="right-tabs">
          <el-tab-pane label="📘 讲义" name="lecture">
            <el-alert
              v-if="isGenerating"
              class="stream-status"
              type="success"
              :closable="false"
              show-icon
              :title="generationMessage"
            />
            <div v-if="resourcePack" class="resource-pack">
              <div class="pack-section">
                <h4>🎯 本节目标</h4>
                <p class="pack-intro">{{ resourcePack.intro }}</p>
              </div>

              <div class="pack-section">
                <h4>📖 核心讲义</h4>
                <MarkdownContent class="lecture-text" :content="resourcePack.lecture" />
              </div>

              <div class="pack-section">
                <h4>📝 闪卡速记 ({{ resourcePack.flash_cards?.length || 0 }} 张，点卡片翻转)</h4>
                <div class="flash-cards">
                  <div
                    v-for="(fc, idx) in resourcePack.flash_cards"
                    :key="idx"
                    class="flash-card"
                    :class="{ flipped: flippedFlash.has(idx) }"
                    @click="toggleFlash(idx)"
                  >
                    <div class="fc-face fc-front">{{ fc.front || fc.question }}</div>
                    <div class="fc-face fc-back">{{ fc.back || fc.answer }}</div>
                    <span class="fc-hint">👆 翻转</span>
                  </div>
                </div>
              </div>

              <div class="card-actions">
                <el-button @click="activeTab = 'exercise'">📝 直接刷题</el-button>
                <el-button type="primary" @click="activeTab = 'quiz'">🧪 进入考试检测</el-button>
              </div>
            </div>
            <el-empty v-else description="请从左侧选择一个知识点节点" />
          </el-tab-pane>

          <el-tab-pane label="📝 习题" name="exercise">
            <div v-if="resourcePack && resourcePack.exercises?.length" class="exercise-list">
              <el-card
                v-for="(ex, eIdx) in resourcePack.exercises"
                :key="eIdx"
                class="exercise-item"
                shadow="never"
              >
                <div class="exercise-question">{{ eIdx + 1 }}. {{ ex.question }}</div>
                <div v-if="!isSubjective(ex)" class="exercise-options">
                  <div
                    v-for="(opt, oIdx) in (ex.options || [])"
                    :key="oIdx"
                    class="exercise-option"
                    :class="optionClass(ex, opt, oIdx)"
                    @click="pickOption(ex, opt, oIdx)"
                  >
                    <span>{{ opt }}</span>
                    <span class="opt-mark">
                      <span v-if="showAnswer(ex) && opt === correctText(ex)" class="opt-correct">✓ 正确答案</span>
                      <span v-else-if="showAnswer(ex) && optionMap(ex)[opt] && opt !== correctText(ex)" class="opt-wrong">✗ 你的选择</span>
                      <span v-else-if="!showAnswer(ex) && pickedMap(ex) === opt" class="opt-correct">👈 已选</span>
                    </span>
                  </div>
                </div>
                <div v-else class="short-answer-area">
                  <el-input
                    v-model="ex.__shortAnswer"
                    type="textarea"
                    :rows="4"
                    maxlength="1000"
                    show-word-limit
                    :disabled="showAnswer(ex)"
                    placeholder="请在这里输入你的答案，建议分点作答……"
                  />
                  <el-button
                    type="primary"
                    :disabled="!String(ex.__shortAnswer || '').trim() || showAnswer(ex)"
                    @click="submitShortAnswer(ex)"
                  >提交答案</el-button>
                </div>
                <div v-if="showAnswer(ex) && isSubjective(ex)" class="your-short-answer">
                  <b>你的答案：</b>{{ ex.__shortAnswer }}
                </div>
                <div v-if="showAnswer(ex)" class="exercise-answer">
                  ✅ {{ isSubjective(ex) ? '参考答案' : '正确答案' }}：{{ correctText(ex) }}
                </div>
                <el-collapse v-if="showAnswer(ex)" class="explanation-collapse">
                  <el-collapse-item title="👀 看解析">
                    <div class="exercise-explanation">
                      <div v-if="ex.explanation">📚 {{ ex.explanation }}</div>
                      <div v-if="ex.short_ref" class="short-ref-block">🔗 快速检索：{{ ex.short_ref }}</div>
                    </div>
                  </el-collapse-item>
                </el-collapse>
              </el-card>
            </div>
            <el-empty v-else :description="isGenerating ? '习题正在自动生成，请稍候…' : '当前知识点暂时没有习题'" />
          </el-tab-pane>

          <el-tab-pane label="🧪 考试检测" name="quiz">
            <div v-if="!quiz.running && !quiz.result" class="quiz-config">
              <div class="quiz-config-head">
                <div>
                  <div class="quiz-config-title">🧪 知识检测 · 模拟考试</div>
                  <div class="quiz-config-sub">
                    从「{{ selectedSubject }} · {{ activeNode?.name || '全科目' }}」随机抽题<br />
                    建议数量 5～20 题。<span class="quiz-note">提交后自动判分 + 生成错题清单</span>
                  </div>
                </div>
                <el-button
                  type="primary"
                  :loading="quiz.loading"
                  :disabled="!selectedSubject"
                  @click="startQuiz"
                >{{ quiz.loading ? '抽题中...' : '🚀 开始抽题检测' }}</el-button>
              </div>

              <div>
                <el-form-item label="抽题数量" label-width="90px" style="margin:0">
                  <el-slider v-model="quiz.count" :min="3" :max="25" :step="1" show-input style="max-width:420px" />
                </el-form-item>
                <el-form-item label="题目来源" label-width="90px" style="margin:0">
                  <el-radio-group v-model="quiz.scope">
                    <el-radio-button value="subject">整本学科</el-radio-button>
                    <el-radio-button value="node">当前知识点</el-radio-button>
                  </el-radio-group>
                </el-form-item>
              </div>
            </div>

            <div v-else-if="quiz.running" class="quiz-running">
              <div class="quiz-start-bar">
                <div class="quiz-meta">
                  🧪 {{ quiz.meta }} · 科目 <b>{{ selectedSubject }}</b> · 当前抽题 <b>{{ quiz.total }}</b> 道
                </div>
                <el-button size="small" @click="confirmQuizQuit">交卷并结束</el-button>
              </div>

              <div class="quiz-progress-bar">
                <div class="quiz-progress-fill" :style="{ width: quizProgressPct + '%' }" />
              </div>
              <div class="quiz-progress-text">第 {{ quiz.index + 1 }} / {{ quiz.total }} 题</div>

              <el-card class="quiz-card" shadow="never">
                <div class="quiz-question">
                  {{ quiz.index + 1 }}. {{ quiz.items[quiz.index].question }}
                </div>
                <div v-if="!isSubjective(quiz.items[quiz.index])" class="quiz-options">
                  <div
                    v-for="(opt, oIdx) in (quiz.items[quiz.index].options || [])"
                    :key="oIdx"
                    class="exercise-option"
                    :class="{
                      selected: quizAnswers[quiz.index] === opt
                    }"
                    @click="quizAnswers[quiz.index] = opt"
                  >
                    <span>{{ opt }}</span>
                    <span class="opt-mark">{{ quizAnswers[quiz.index] === opt ? '👈' : '' }}</span>
                  </div>
                </div>
                <el-input
                  v-else
                  v-model="quizAnswers[quiz.index]"
                  type="textarea"
                  :rows="5"
                  maxlength="1000"
                  show-word-limit
                  placeholder="请输入简答题答案，建议按要点分条作答……"
                />
                <div class="quiz-nav">
                  <el-button
                    :disabled="quiz.index === 0"
                    @click="quiz.index--"
                  >← 上一题</el-button>
                  <el-button
                    v-if="quiz.index < quiz.total - 1"
                    type="primary"
                    :disabled="!quizAnswers[quiz.index]"
                    @click="quiz.index++"
                  >下一题 →</el-button>
                  <el-button
                    v-else
                    type="success"
                    :disabled="unansweredCount > 0"
                    @click="submitQuiz"
                  >✅ 交卷 · 自动判分</el-button>
                </div>
              </el-card>

              <el-alert
                v-if="unansweredCount > 0"
                type="warning"
                :closable="false"
                :title="`还有 ${unansweredCount} 题没答`"
              />
            </div>

            <div v-else-if="quiz.result" class="quiz-result">
              <div class="quiz-result-title">🧪 检测结果 — {{ selectedSubject }}</div>
              <div class="quiz-result-stats">
                <div>总分 <b style="color:#0d9488;font-size:18px">{{ quiz.result.score }}</b> / {{ quiz.result.total }}</div>
                <div>正确率 <b>{{ quiz.result.percent }}%</b></div>
                <div>错题 <b>{{ quiz.result.wrong_count }}</b> 道</div>
                <div class="quiz-result-warn">{{ quiz.result.comment }}</div>
              </div>

              <el-card
                v-for="(wrong, wIdx) in quiz.result.wrong_questions"
                :key="wIdx"
                class="exercise-item"
                shadow="never"
              >
                <div class="exercise-question">{{ wrong.question }}</div>
                <div class="exercise-options">
                  <div
                    v-for="(opt, oIdx) in (wrong.options || [])"
                    :key="oIdx"
                    class="exercise-option"
                    :class="{
                      correct: opt === wrong.correct,
                      wrong: opt === wrong.your_answer && opt !== wrong.correct
                    }"
                  >
                    <span>{{ opt }}</span>
                    <span class="opt-mark">
                      <span v-if="opt === wrong.correct" class="opt-correct">✓ 正确答案</span>
                      <span v-else-if="opt === wrong.your_answer" class="opt-wrong">✗ 你的选择</span>
                    </span>
                  </div>
                </div>
                <div class="exercise-answer">✅ 正确答案：{{ wrong.correct }}</div>
                <el-collapse v-if="wrong.explanation" class="explanation-collapse">
                  <el-collapse-item title="👀 看解析">
                    <div class="exercise-explanation">
                      <div>📚 {{ wrong.explanation }}</div>
                    </div>
                  </el-collapse-item>
                </el-collapse>
              </el-card>

              <div style="text-align:center;margin-top:4px">
                <el-button @click="resetQuiz">🔁 再抽一份</el-button>
                <el-button type="primary" @click="activeTab = 'exercise'">📝 继续刷题</el-button>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="📺 精讲视频 & 平台" name="video">
            <div v-if="selectedSubject" style="margin-bottom:10px">
              <b style="font-size:14px;color:#1f2937">📹 {{ selectedSubject }} · 推荐公开视频</b>
              <div class="video-grid" style="margin-top:12px">
                <div
                  v-for="(video, idx) in videoList"
                  :key="idx"
                  class="video-card"
                >
                  <div class="video-thumb">🎬</div>
                  <div class="video-info">
                    <div class="video-title">{{ video.title }}</div>
                    <div class="video-desc">来自 {{ video.platform }}</div>
                    <div class="video-meta">时长 {{ video.duration }} · {{ video.level }}</div>
                    <el-button
                      class="video-go-btn"
                      size="small"
                      link
                      @click="openVideo(video.url)"
                    >观看 →</el-button>
                  </div>
                </div>
              </div>
              <div style="margin-top:24px">
                <b style="font-size:14px;color:#1f2937">📚 学习平台导航</b>
                <div class="platform-grid">
                  <a
                    v-for="p in platformList"
                    :key="p.name"
                    class="platform-card"
                    :href="p.url"
                    target="_blank"
                    rel="noopener"
                  >
                    <span class="platform-emoji">{{ p.emoji }}</span>
                    <span class="platform-name">{{ p.name }}</span>
                    <span class="platform-desc">{{ p.desc }}</span>
                  </a>
                </div>
              </div>
            </div>
            <el-empty v-else description="请先选择科目" />
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DataAnalysis, CaretTop, CaretBottom, ArrowDown } from '@element-plus/icons-vue'
import MarkdownContent from '@/components/MarkdownContent.vue'

const educationLevel = ref<'high_school' | 'university'>('university')
const highSchoolGrades = ['高一', '高二', '高三']
const universityGrades = ['计算机', '数学', '经管', '通识']
const grade = ref('计算机')
const selectedSubject = ref('计算机网络')

const subjectOptions = ref<string[]>([])
const chapterList = ref<any[]>([])
const activeChapter = ref<string | number | null>(null)
const chapterOpenMap = reactive<Record<string | number, boolean>>({})
const filterKey = ref('')

const activeNode = ref<any | null>(null)
const resourcePack = ref<any>(null)
const isGenerating = ref(false)
const generationMessage = ref('正在准备内容…')
let streamController: AbortController | null = null
const flippedFlash = reactive<Set<number>>(new Set())
const activeTab = ref('lecture')

const quiz = reactive({
  loading: false,
  running: false,
  result: null as any,
  items: [] as any[],
  index: 0,
  total: 0,
  meta: '',
  count: 10,
  scope: 'subject' as 'subject' | 'node'
})
const quizAnswers = reactive<Record<string, string>>({})
const resetQuizAnswers = () => {
  Object.keys(quizAnswers).forEach(k => delete quizAnswers[k])
}

const perNodeMastery = reactive<Record<string | number, string>>({})

const masteryLabel = computed(() => {
  const v = masteryPercent.value
  if (v >= 80) return '已掌握 ✅'
  if (v >= 40) return '学习中 📘'
  return '未开始 ⏳'
})
const masteryPercent = computed(() => {
  const allNodes: any[] = []
  chapterList.value.forEach(ch => ch.sections?.forEach((sec: any) => {
    if (sec.children) allNodes.push(...sec.children)
    else if (sec.node_count) allNodes.push({ id: sec.id, mastery: sec.mastery })
  }))
  if (!allNodes.length) return 0
  const score = allNodes.reduce((s, n) => s + (n.mastery === 'mastered' ? 100 : n.mastery === 'learning' ? 60 : 20), 0)
  return Math.round(score / allNodes.length)
})
const masteryProgressColor = computed(() => {
  if (masteryPercent.value >= 80) return '#059669'
  if (masteryPercent.value >= 40) return '#0d9488'
  return '#e6a23c'
})
const masteryColor = (mastery: string) => {
  if (mastery === 'mastered') return '#059669'
  if (mastery === 'learning') return '#0ea5a3'
  return '#cbd5e1'
}
const masteredCount = computed(() => {
  let n = 0
  chapterList.value.forEach(ch => ch.sections?.forEach((sec: any) => {
    if (sec.children) sec.children.forEach((c: any) => { if (c.mastery === 'mastered') n++ })
  }))
  return n
})
const learningCount = computed(() => {
  let n = 0
  chapterList.value.forEach(ch => ch.sections?.forEach((sec: any) => {
    if (sec.children) sec.children.forEach((c: any) => { if (c.mastery === 'learning') n++ })
  }))
  return n
})
const pendingCount = computed(() => {
  let n = 0
  chapterList.value.forEach(ch => ch.sections?.forEach((sec: any) => {
    if (sec.children) sec.children.forEach((c: any) => { if (c.mastery !== 'mastered' && c.mastery !== 'learning') n++ })
  }))
  return n
})

const totalNodeCount = computed(() => chapterList.value.reduce((s, c) => s + (c.node_count || 0), 0))
const filteredChapters = computed(() => {
  if (!filterKey.value.trim()) return chapterList.value
  const k = filterKey.value.toLowerCase()
  return chapterList.value.filter(ch =>
    ch.name.toLowerCase().includes(k) ||
    (ch.sections || []).some((sec: any) =>
      sec.name.toLowerCase().includes(k) ||
      (sec.children || []).some((leaf: any) => leaf.name.toLowerCase().includes(k))
    )
  )
})

const nodeChainText = computed(() => {
  if (!activeNode.value) return '未选择知识点'
  const sec = chapterList.value.flatMap(ch => ch.sections || []).find((s: any) =>
    (s.children || []).some((c: any) => c.id === activeNode.value.id) || s.id === activeNode.value.section_id
  )
  const chapter = chapterList.value.find(ch => (ch.sections || []).some((s: any) => s.id === sec?.id))
  return `${chapter?.name || ''} · ${sec?.name || ''} · ${activeNode.value.name}`
})

const videoList = computed(() => {
  if (!selectedSubject.value) return []
  const all: Record<string, any[]> = {
    'Python程序设计': [
      { title: '【B站】Python 零基础到实战', platform: 'B 站', duration: '45:12', level: '入门', url: 'https://www.bilibili.com' },
      { title: '【MOOC】Python 数据分析基础', platform: '中国大学MOOC', duration: '16 讲', level: '进阶', url: 'https://www.icourse163.org' }
    ],
    '机器学习': [
      { title: '【B站】吴恩达 Machine Learning 中文版', platform: 'B 站', duration: '110 讲', level: '入门', url: 'https://www.bilibili.com' },
      { title: '【学堂在线】机器学习基础', platform: '学堂在线', duration: '32 讲', level: '进阶', url: 'https://www.xuetangx.com' }
    ],
    '高等数学': [
      { title: '同济版高等数学（上册）精讲', platform: 'B 站', duration: '180 讲', level: '基础', url: 'https://www.bilibili.com' },
      { title: '宋浩老师 · 微积分', platform: 'B 站', duration: '120 讲', level: '基础', url: 'https://www.bilibili.com' }
    ],
    '线性代数': [
      { title: '李永乐 · 线性代数基础', platform: 'B 站', duration: '60 讲', level: '基础', url: 'https://www.bilibili.com' }
    ],
    '计算机组成': [
      { title: '王道 · 计算机组成原理', platform: 'B 站', duration: '80 讲', level: '进阶', url: 'https://www.bilibili.com' }
    ],
    '编译原理': [
      { title: '龙书导读 · 编译原理', platform: 'B 站', duration: '50 讲', level: '进阶', url: 'https://www.bilibili.com' }
    ],
    '人工智能导论': [
      { title: 'AI 导论（清华大学）', platform: '学堂在线', duration: '24 讲', level: '入门', url: 'https://www.xuetangx.com' }
    ]
  }
  return all[selectedSubject.value] || [
    { title: `${selectedSubject.value} 公开课程合集（B 站）`, platform: 'B 站', duration: '系列', level: '综合', url: 'https://www.bilibili.com' },
    { title: `${selectedSubject.value} MOOC 公开课`, platform: '中国大学MOOC', duration: '系列', level: '综合', url: 'https://www.icourse163.org' }
  ]
})

const platformList = [
  { name: '中国大学MOOC', emoji: '🎓', desc: '免费名校公开课', url: 'https://www.icourse163.org' },
  { name: 'Bilibili', emoji: '📺', desc: '海量免费教程', url: 'https://www.bilibili.com' },
  { name: '学堂在线', emoji: '📘', desc: '清华开源课程', url: 'https://www.xuetangx.com' },
  { name: 'Coursera', emoji: '🌐', desc: '全球名校课程', url: 'https://www.coursera.org' },
  { name: '知乎', emoji: '💡', desc: '高质量专栏', url: 'https://www.zhihu.com' },
  { name: 'StackOverflow', emoji: '🐞', desc: '程序问答', url: 'https://stackoverflow.com' },
  { name: 'LeetCode', emoji: '🧩', desc: '算法刷题', url: 'https://leetcode.cn' },
  { name: 'GitHub', emoji: '⭐', desc: '开源代码库', url: 'https://github.com' }
]

const quizProgressPct = computed(() => {
  if (!quiz.total) return 0
  return Math.round(((quiz.index + 1) / quiz.total) * 100)
})
const unansweredCount = computed(() => {
  let n = 0
  for (let i = 0; i < quiz.total; i++) if (!quizAnswers[i]) n++
  return n
})

const pickedMap = (ex: any) => ex.__picked
const optionMap = (ex: any) => ex.__picked_answer_map
const correctText = (ex: any) => {
  if (ex.correct_option) {
    const opt = (ex.options || [])[String.fromCharCode(64 + Number(ex.correct_option))?.trim() === ex.correct_option ? ex.correct_option : Number(ex.correct_option)]
    if (opt) return opt
  }
  return (ex.options || []).find((_: string, i: number) => String.fromCharCode(65 + i).toLowerCase() === String(ex.answer || '').toLowerCase()) || ex.answer || ''
}
const showAnswer = (ex: any) => !!ex.__answered
const pickOption = (ex: any, opt: string, _oIdx: number) => {
  if (ex.__answered) return
  ex.__picked = opt
  ex.__picked_answer_map = (optionMap(ex) || {})
  ex.__picked_answer_map[opt] = true
  ex.__answered = true

  const isCorrect = opt === correctText(ex)
  ElMessage.success(isCorrect ? '✅ 回答正确' : `❌ 答错了 · 正确答案：${correctText(ex)}`)

  if (!isCorrect) {
    const sid = localStorage.getItem('student_id') || '1'
    fetch('/api/db/error-records', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: sid,
        question: ex.question,
        user_answer: opt,
        correct_answer: correctText(ex),
        knowledge_point: ex.knowledge_point || '',
        explanation: ex.explanation || '',
        knowledge_node_id: activeNode.value?.id
      })
    }).catch(e => console.error('保存错题失败', e))
  }
}
const optionClass = (ex: any, opt: string, _oIdx: number) => {
  const cls: string[] = []
  if (ex.__answered) {
    const correct = correctText(ex)
    if (opt === correct) cls.push('correct')
    if (ex.__picked === opt && opt !== correct) cls.push('wrong')
  } else if (ex.__picked === opt) {
    cls.push('selected')
  }
  return cls
}

const toggleFlash = (idx: number) => {
  if (flippedFlash.has(idx)) flippedFlash.delete(idx)
  else flippedFlash.add(idx)
}

const markMastery = (id: number, type: 'section' | 'node') => {
  const next = perNodeMastery[id] === 'mastered' ? 'pending' : perNodeMastery[id] === 'learning' ? 'mastered' : 'learning'
  perNodeMastery[id] = next
  const target = type === 'section' ? chapterList.value.flatMap(ch => ch.sections || []).find((s: any) => s.id === id) : null
  if (target) target.mastery = next
}

const openVideo = (url: string) => window.open(url, '_blank')

const loadSubjectOptions = async () => {
  try {
    const res = await fetch(`/api/db/subjects?education_level=${educationLevel.value}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    const list: any[] = data.subjects || data || []
    if (!Array.isArray(list)) throw new Error('科目接口返回格式不正确')
    subjectOptions.value = list.map((s: any) => (typeof s === 'string' ? s : s.name)).filter((name: string) => name === '计算机网络')
    if (!selectedSubject.value || !subjectOptions.value.includes(selectedSubject.value)) {
      selectedSubject.value = subjectOptions.value[0] || ''
    }
  } catch (e) {
    subjectOptions.value = educationLevel.value === 'university'
      ? ['计算机网络']
      : ['计算机网络']
    selectedSubject.value = subjectOptions.value[0] || ''
    ElMessage.warning('后端科目接口暂不可用，已加载本地演示科目')
  }
}

const loadKnowledgeTreeForSubject = async () => {
  if (!selectedSubject.value) {
    chapterList.value = []
    return
  }
  try {
    const level = educationLevel.value
    const res = await fetch(`/api/db/knowledge-tree/${encodeURIComponent(selectedSubject.value)}?education_level=${encodeURIComponent(level)}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    const tree = data.tree || data.chapters || data || []
    if (!Array.isArray(tree)) throw new Error('知识目录接口返回格式不正确')
    const chapters = tree.map((ch: any) => {
      const chChildren = ch.children || ch.nodes || []
      const sections: any[] = []
      const leafNodes: any[] = []
      chChildren.forEach((c: any) => {
        const hasChildren = c.children && c.children.length > 0
        const isSection = c.type === 'section' || hasChildren
        if (isSection) {
          sections.push({
            id: c.id,
            name: c.name,
            node_count: (c.children || []).length || 0,
            mastery: perNodeMastery[c.id] || 'pending',
            section_id: c.id,
            children: (c.children || []).map((leaf: any) => ({
              ...leaf,
              section_id: c.id,
              mastery: perNodeMastery[leaf.id] || leaf.mastery || 'pending'
            }))
          })
          leafNodes.push(...(c.children || []))
        } else {
          leafNodes.push({ ...c, section_id: ch.id, mastery: perNodeMastery[c.id] || 'pending' })
        }
      })
      if (!sections.length && chChildren.length) {
        sections.push({
          id: `section-${ch.id || ch.name}`,
          name: `${ch.name} · 知识点`,
          node_count: chChildren.length,
          mastery: 'pending',
          children: chChildren.map((leaf: any) => ({
            ...leaf,
            section_id: `section-${ch.id || ch.name}`,
            mastery: perNodeMastery[leaf.id] || leaf.mastery || 'pending'
          }))
        })
      }
      return {
        id: ch.id || ch.name,
        name: ch.name,
        color: ch.color || randomColor(ch.name),
        node_count: sections.reduce((s: number, sec: any) => s + sec.node_count, 0) || chChildren.length,
        sections,
        mastery: perNodeMastery[ch.id || ch.name] || 'pending'
      }
    })
    chapterList.value = chapters
    Object.keys(chapterOpenMap).forEach(k => delete chapterOpenMap[k])
    chapterList.value.forEach(ch => chapterOpenMap[ch.id] = true)
  } catch (e) {
    chapterList.value = []
    ElMessage.warning('目录加载失败，检查后端是否启动')
  }
}

const randomColor = (seed: string) => {
  const colors = ['#0ea5a3', '#0d9488', '#059669', '#14b8a6', '#10b981', '#0284c7', '#0891b2', '#6366f1']
  let h = 0
  for (const c of seed) h = ((h << 5) - h + c.charCodeAt(0)) | 0
  return colors[Math.abs(h) % colors.length]
}

const toggleChapter = (id: string | number) => {
  chapterOpenMap[id] = !chapterOpenMap[id]
  const ch = chapterList.value.find(c => c.id === id)
  if (ch) {
    const firstNode = ch.sections?.[0]?.children?.[0]
    if (firstNode && activeChapter.value !== id) handleNodeClick(firstNode)
    if (activeNode.value && ch.sections?.some((s: any) => (s.children || []).some((c: any) => c.id === activeNode.value.id))) {
      activeChapter.value = id
    }
  }
}

const selectSection = (section: any) => {
  const firstChild = (section.children || [])[0]
  if (firstChild) handleNodeClick(firstChild)
  else {
    activeNode.value = { ...section, section_id: section.id, mastery: perNodeMastery[section.id] || section.mastery || 'pending' }
    activeChapter.value = chapterList.value.findIndex(ch => ch.sections?.some((s: any) => s.id === section.id)) >= 0
      ? chapterList.value.find(ch => ch.sections?.some((s: any) => s.id === section.id))?.id ?? null
      : null
    ElMessage.info(`暂未展开具体知识点，请先在该章节节点继续下钻`)
  }
}

const handleNodeClick = async (node: any) => {
  streamController?.abort()
  streamController = null
  isGenerating.value = false
  activeNode.value = {
    ...node,
    mastery: perNodeMastery[node.id] || node.mastery || 'pending'
  }
  activeChapter.value = chapterList.value.find(ch => ch.sections?.some((s: any) =>
    (s.children || []).some((c: any) => c.id === node.id)
  ))?.id ?? null
  activeTab.value = 'lecture'

  // 先用知识树中已经携带的缓存立即渲染，用户点击后不再等待一次额外的“AI生成”。
  resourcePack.value = {
    intro: node.description || `本节目标：掌握「${node.name}」的核心概念与典型题型。`,
    lecture: node.lecture_text || '',
    flash_cards: (node.flash_cards || []).map(normalizeFlashCard),
    exercises: (node.exercises || []).map(normalizeExercise).filter(Boolean)
  }

  try {
    const r = await fetch(`/api/db/node/${node.id}/exercises`)
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    const data = await r.json()
    resourcePack.value = {
      intro: node.description || `本节目标：掌握「${node.name}」的核心概念与典型题型。`,
      lecture: data.lecture_text || resourcePack.value.lecture || '',
      flash_cards: (data.flash_cards || []).map(normalizeFlashCard),
      exercises: (data.exercises || []).map(normalizeExercise).filter(Boolean)
    }
    const hasLecture = String(resourcePack.value.lecture || '').trim().length >= 20
    if (!hasLecture) {
      await streamGenerateNode(node.id, node.name)
    }
  } catch (_e) {
    if (!resourcePack.value.lecture) resourcePack.value = defaultResourceFor(node.name)
    ElMessage.warning('内容读取失败，请检查后端服务')
  }
}

const normalizeFlashCard = (fc: any) => ({
  front: fc.front || fc.question || fc.term || '',
  back: fc.back || fc.answer || fc.definition || ''
})

const streamGenerateNode = async (nodeId: number, nodeName: string, force = false) => {
  if (!nodeId || isGenerating.value) return
  streamController?.abort()
  streamController = new AbortController()
  const controller = streamController
  isGenerating.value = true
  generationMessage.value = `正在生成「${nodeName}」…`
  let lectureStarted = false

  try {
    const response = await fetch(`/api/db/knowledge/${nodeId}/stream${force ? '?force=true' : ''}`, {
      signal: controller.signal,
      headers: { Accept: 'text/event-stream' }
    })
    if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`)

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const events = buffer.split('\n\n')
      buffer = events.pop() || ''
      for (const event of events) {
        const dataLine = event.split('\n').find(line => line.startsWith('data:'))
        if (!dataLine) continue
        const eventData = JSON.parse(dataLine.slice(5).trim())
        if (activeNode.value?.id !== nodeId) {
          controller.abort()
          return
        }
        if (eventData.message) generationMessage.value = eventData.message
        if (eventData.status === 'streaming' && eventData.step === 'lecture') {
          if (!lectureStarted) {
            resourcePack.value.lecture = ''
            lectureStarted = true
          }
          resourcePack.value.lecture += eventData.content || ''
        }
        if (eventData.status === 'error') throw new Error(eventData.message || '生成失败')
      }
    }

    if (activeNode.value?.id === nodeId) {
      const cached = await fetch(`/api/db/node/${nodeId}/exercises`).then(r => r.json())
      resourcePack.value.lecture = cached.lecture_text || resourcePack.value.lecture
      resourcePack.value.exercises = (cached.exercises || []).map(normalizeExercise).filter(Boolean)
      resourcePack.value.flash_cards = (cached.flash_cards || []).map(normalizeFlashCard)
      generationMessage.value = '内容生成完成'
    }
  } catch (error: any) {
    if (error?.name !== 'AbortError') {
      generationMessage.value = error?.message || '生成失败'
      ElMessage.error(`自动生成失败：${generationMessage.value}`)
    }
  } finally {
    if (streamController === controller) {
      isGenerating.value = false
      streamController = null
    }
  }
}

const normalizeExercise = (ex: any) => {
  if (!ex || !ex.question) return null
  const options = ex.options || ex.choices || []
  return {
    question: ex.question,
    options: options,
    answer: ex.answer,
    correct_option: ex.correct_option !== undefined ? ex.correct_option : (() => {
      const a = String(ex.answer || '').toUpperCase()
      const m = a.match(/^([A-Z])/)
      return m ? m[1] : ''
    })(),
    explanation: ex.explanation || ex.analysis || '',
    short_ref: ex.short_ref || ex.shortRef || ''
  }
}

const isSubjective = (ex: any) => !Array.isArray(ex?.options) || ex.options.length === 0
const submitShortAnswer = (ex: any) => {
  if (!String(ex.__shortAnswer || '').trim()) return
  ex.__answered = true

  const isCorrect = subjectiveAnswerMatches(ex.__shortAnswer, correctText(ex))
  ElMessage.success(isCorrect ? '✅ 回答正确' : '答案已提交，请结合参考答案和解析进行自评')

  if (!isCorrect) {
    const sid = localStorage.getItem('student_id') || '1'
    fetch('/api/db/error-records', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: sid,
        question: ex.question,
        user_answer: ex.__shortAnswer,
        correct_answer: correctText(ex),
        knowledge_point: ex.knowledge_point || '',
        explanation: ex.explanation || '',
        knowledge_node_id: activeNode.value?.id
      })
    }).catch(e => console.error('保存错题失败', e))
  }
}

const defaultResourceFor = (name: string) => ({
  intro: `本节目标：掌握「${name}」的核心概念、常见误区与典型题型。`,
  lecture: `# ${name}\n\n欢迎学习「${name}」。\n\n（AI 讲义正在后台生成，请稍后再次点击节点或使用「AI 生成本章节讲义」按钮。）`,
  flash_cards: [],
  exercises: []
})

const handleGenerate = async () => {
  if (!activeNode.value) {
    ElMessage.warning('请先在左侧点击一个知识点节点')
    return
  }
  await streamGenerateNode(activeNode.value.id, activeNode.value.name, true)
}

const startQuiz = async () => {
  quiz.loading = true
  quiz.items = []
  resetQuizAnswers()
  quiz.index = 0
  quiz.result = null
  try {
    const nodeId = quiz.scope === 'node' && activeNode.value ? activeNode.value.id : undefined
    const url = `/api/db/quiz/${encodeURIComponent(selectedSubject.value)}?education_level=${encodeURIComponent(educationLevel.value)}&count=${quiz.count}${nodeId ? `&source_node_id=${nodeId}` : ''}`
    const r = await fetch(url)
    const data = await r.json()
    const list: any[] = data.quiz || data.items || data.exercises || []
    quiz.items = list.map(normalizeExercise).filter(Boolean)
    quiz.total = quiz.items.length
    quiz.meta = `${data.subject || selectedSubject.value} · 抽题 ${quiz.total} 道`
    if (!quiz.total) {
      ElMessage.warning('当前范围暂时没有题目，请先打开一个知识点，系统会自动生成')
    } else {
      quiz.running = true
    }
  } catch (e) {
    ElMessage.error('抽题失败，请确认后端已启动')
  } finally {
    quiz.loading = false
  }
}

const submitQuiz = async () => {
  let correct = 0
  const wrongs: any[] = []
  quiz.items.forEach((ex, i) => {
    const your = quizAnswers[i]
    const correctTextFor = correctText(ex)
    const ok = isSubjective(ex)
      ? subjectiveAnswerMatches(your || '', correctTextFor)
      : your === correctTextFor
    if (ok) correct++
    else wrongs.push({
      question: ex.question,
      options: ex.options,
      your_answer: your,
      correct: correctTextFor,
      explanation: ex.explanation || ''
    })
  })
  const percent = quiz.total ? Math.round((correct / quiz.total) * 100) : 0
  let comment = '继续努力 💪'
  if (percent >= 90) comment = '🎉 太棒啦！'
  else if (percent >= 70) comment = '👍 还不错，再刷 3 道错题'
  else if (percent >= 40) comment = '📚 建议先把本节讲义过一遍再考'
  quiz.result = {
    score: correct,
    total: quiz.total,
    percent,
    wrong_count: wrongs.length,
    comment,
    wrong_questions: wrongs
  }
  quiz.running = false

  const sid = localStorage.getItem('student_id') || '1'
  for (const wrong of wrongs) {
    try {
      await fetch('/api/db/error-records', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: sid,
          question: wrong.question,
          user_answer: wrong.your_answer || '',
          correct_answer: wrong.correct || '',
          knowledge_point: wrong.knowledge_point || '',
          explanation: wrong.explanation || '',
          knowledge_node_id: activeNode.value?.id
        })
      })
    } catch (e) {
      console.error('保存错题失败', e)
    }
  }

  ElMessage.success(`✅ 交卷成功！得分 ${correct}/${quiz.total}`)
}

const subjectiveAnswerMatches = (answer: string, reference: string) => {
  const normalize = (value: string) => value.toLowerCase().replace(/[\s，。；：、,.!?！？;:()（）]/g, '')
  const actual = normalize(answer)
  const expected = normalize(reference)
  if (!actual || !expected) return false
  if (actual.includes(expected) || expected.includes(actual)) return true
  const keywords = String(reference).split(/[，。；：、,.!?！？;:\s]+/).map(normalize).filter(word => word.length >= 2)
  if (!keywords.length) return false
  return keywords.filter(word => actual.includes(word)).length / keywords.length >= 0.5
}

const confirmQuizQuit = async () => {
  try {
    await ElMessageBox.confirm('交卷并结束？将按已答题目判分。', '提示', {
      confirmButtonText: '交卷',
      cancelButtonText: '继续作答',
      type: 'warning'
    })
    await submitQuiz()
  } catch { /* cancel */ }
}

const resetQuiz = () => {
  quiz.running = false
  quiz.result = null
  quiz.items = []
  quiz.index = 0
  resetQuizAnswers()
}

watch([educationLevel, grade], async () => {
  await loadSubjectOptions()
  if (!selectedSubject.value && subjectOptions.value.length) {
    selectedSubject.value = subjectOptions.value[0]
  }
  await loadKnowledgeTreeForSubject()
})

watch(selectedSubject, async () => {
  activeNode.value = null
  resourcePack.value = null
  await loadKnowledgeTreeForSubject()
})

onMounted(async () => {
  await loadSubjectOptions()
  if (subjectOptions.value.length && !selectedSubject.value) selectedSubject.value = subjectOptions.value[0]
  await loadKnowledgeTreeForSubject()
})

onBeforeUnmount(() => streamController?.abort())
</script>

<style>
.resource-view{padding:0}
.search-card{margin-bottom:20px}
.card-header{display:flex;align-items:center;gap:8px;font-weight:bold}
.header-dot{width:6px;height:6px;border-radius:50%;background:#0d9488;box-shadow:0 0 8px rgba(13,148,136,.6)}
.header-sub{margin-left:auto;font-size:12px;color:#5a6888;font-weight:normal}

.edu-switch-group{display:flex;gap:4px}
.edu-switch-group :deep(.el-radio-button){margin-right:0;border:none;background:transparent}
.edu-switch-group :deep(.el-radio-button__inner){border-radius:8px!important;padding:10px 26px;font-weight:700;font-size:14px;color:#6b7a90;background:#f1f3f8;border:1px solid #e4e7ee!important;box-shadow:none;transition:all .25s ease}
.edu-switch-group :deep(.el-radio-button__inner):hover{color:#0d9488;background:#ecfdf9;border-color:#0d9488!important}
.edu-switch-group :deep(.el-radio-button__original-radio):checked + .el-radio-button__inner{background:linear-gradient(135deg,#0d9488 0%,#0ea5a3 100%)!important;color:#fff!important;border-color:#0d9488!important;box-shadow:0 4px 14px rgba(13,148,136,.32)!important;font-weight:800;letter-spacing:2px}
.edu-switch-group :deep(.el-radio-button__inner)::before{display:none}
.edu-switch-group :deep(.el-radio-button:first-child .el-radio-button__inner){border-top-left-radius:10px;border-bottom-left-radius:10px}
.edu-switch-group :deep(.el-radio-button:last-child .el-radio-button__inner){border-top-right-radius:10px;border-bottom-right-radius:10px}

.grade-group :deep(.el-radio-button){margin-right:0;border:none;background:transparent}
.grade-group :deep(.el-radio-button__inner){border-radius:6px!important;padding:7px 16px;font-size:12px;color:#6b7a90;background:#f7f8fb;border:1px solid #e4e7ee!important;box-shadow:none;transition:all .25s ease}
.grade-group :deep(.el-radio-button__inner):hover{color:#0d9488;background:#ecfdf9}
.grade-group :deep(.el-radio-button__original-radio):checked + .el-radio-button__inner{background:#ccfbf1!important;color:#0f766e!important;border-color:#0d9488!important;font-weight:700}

.tree-card{margin-bottom:20px}
.tree-search{display:flex;gap:6px;margin-top:12px;margin-bottom:12px}
.dir-tree{display:flex;flex-direction:column;gap:4px}

.dir-chapter-head{display:flex;align-items:center;gap:10px;padding:10px 12px;margin-bottom:2px;border-radius:10px;background:#f6f8fb;cursor:pointer;border:1px solid transparent;transition:all .22s ease}
.dir-chapter-head:hover{background:#ecfdf9;transform:translateX(2px);border-color:#ccfbf1}
.dir-caret{color:#0d9488;font-size:11px;width:14px;text-align:center;flex-shrink:0}
.dir-chapter-name{flex:1;font-weight:700;font-size:13px;color:#1f2937;letter-spacing:.4px}
.dir-chapter-count{font-size:11px;color:#6b7a90;background:#eef0f6;padding:2px 8px;border-radius:99px;font-weight:600}
.dir-chapter-dot{width:8px;height:8px;border-radius:50%;box-shadow:0 0 6px rgba(0,0,0,.15)}
.dir-chapter-active{background:linear-gradient(135deg,#0d9488 0%,#0ea5a3 100%)!important;color:#fff;border-color:#0d9488!important;box-shadow:0 4px 14px rgba(13,148,136,.3)}
.dir-chapter-active .dir-caret{color:#fff}
.dir-chapter-active .dir-chapter-name{color:#fff;font-weight:800}
.dir-chapter-active .dir-chapter-count{background:rgba(255,255,255,.25);color:#fff}

.dir-section{display:flex;flex-direction:column;gap:2px;margin-left:10px;border-left:2px dashed #e4e7ee;padding-left:6px}
.dir-section-line{display:flex;align-items:center;gap:8px;padding:8px 12px;border-radius:8px;cursor:pointer;color:#4a5580;font-size:12px;background:transparent;transition:all .2s ease}
.dir-section-line:hover{background:#ecfdf9;color:#0d9488;transform:translateX(2px)}
.sec-caret{color:#0ea5a3;font-size:10px;width:12px;text-align:center}
.sec-name{flex:1;font-weight:600}
.sec-count{font-size:10px;color:#8a96af;background:#f1f3f8;padding:1px 6px;border-radius:99px}
.sec-mastery-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.sec-mark{margin-left:2px}
.mark-btn{font-size:13px;cursor:pointer;padding:0 4px}
.mark-btn:hover{transform:scale(1.2)}
.dir-section-active{background:#ccfbf1;color:#0f766e;font-weight:600;box-shadow:inset 3px 0 0 #0d9488}

.dir-leaf-wrap{display:flex;flex-direction:column;gap:1px;margin-left:8px}
.dir-leaf-line{display:flex;align-items:center;gap:8px;padding:6px 12px;border-radius:6px;cursor:pointer;color:#5a6888;font-size:12px;transition:all .2s ease}
.dir-leaf-line:hover{background:#f0fdf4;color:#059669;transform:translateX(2px)}
.leaf-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0;box-shadow:0 0 4px rgba(0,0,0,.08)}
.leaf-name{flex:1}
.dir-leaf-active{background:#ccfbf1;color:#0f766e;font-weight:600;box-shadow:inset 3px 0 0 #0d9488}

.generate-btn{width:100%;margin-top:16px;background:linear-gradient(135deg,#0d9488 0%,#0f766e 100%);border:none}

.now-learning-bar{display:flex;align-items:center;gap:8px;padding:10px 14px;background:linear-gradient(135deg,#f0fdf4 0%,#ecfdf9 100%);border-radius:10px;margin-bottom:16px;border:1px solid #ccfbf1}
.now-learning-label{font-size:12px;color:#5a6888;font-weight:600}
.now-learning-subject{font-weight:700;color:#0d9488;background:#ccfbf1;padding:2px 8px;border-radius:6px;font-size:12px}
.now-learning-arrow{color:#0d9488;font-weight:900;font-size:14px}
.now-learning-chain{flex:1;font-weight:600;color:#1f2937;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.now-learning-tag{color:#8a96af;font-size:12px}
.now-learning-streak{margin-left:auto;font-size:12px;color:#0d9488;font-weight:700}

.main-grid{display:grid;grid-template-columns:340px 1fr;gap:20px}
.left-col{display:flex;flex-direction:column;gap:16px}
.right-col{min-width:0}

.right-tabs :deep(.el-tabs__nav-wrap::after){background:#e4e7ee}
.right-tabs :deep(.el-tabs__item.is-active){color:#0d9488;font-weight:700}
.right-tabs :deep(.el-tabs__active-bar){background:#0d9488}

.resource-pack{display:flex;flex-direction:column;gap:18px}
.pack-section{padding-bottom:16px;border-bottom:1px dashed #e4e7ee}
.pack-section:last-child{border-bottom:none}
.pack-section h4{margin:0 0 10px;font-size:14px;color:#0d9488;font-weight:800;letter-spacing:1px}
.pack-intro{color:#4b5563;font-size:13px;line-height:1.7}

.lecture-text{white-space:pre-wrap;line-height:1.9;color:#115e59;background:linear-gradient(135deg,#f0fdf4,#ecfdf9);border-radius:10px;padding:20px 22px;border:1px solid #ccfbf1}

.flash-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}
.flash-card{perspective:1000px;height:120px;cursor:pointer}
.flash-card>*{backface-visibility:hidden}
.fc-face{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;padding:14px;border-radius:10px;font-weight:700;font-size:14px;text-align:center}
.fc-front{background:linear-gradient(135deg,#0d9488 0%,#0ea5a3 100%);color:#fff}
.fc-back{background:#fff;border:2px solid #0d9488;color:#0f766e;transform:rotateY(180deg)}
.flash-card.flipped .fc-front{transform:rotateY(-180deg)}
.flash-card.flipped .fc-back{transform:rotateY(0)}
.fc-hint{position:absolute;bottom:4px;right:6px;font-size:9px;opacity:.5}

.exercise-list{display:flex;flex-direction:column;gap:12px}
.exercise-item{border:1px solid #ccfbf1;border-radius:10px;padding:16px;background:#fff}
.exercise-question{font-weight:700;margin-bottom:10px;color:#1f2937;font-size:13px}
.exercise-options{display:flex;flex-direction:column;gap:6px;margin-top:8px}
.exercise-option{padding:10px 12px;border:1px solid #e4e7ee;border-radius:8px;cursor:pointer;transition:all .2s;font-size:12px;color:#4a5580;display:flex;justify-content:space-between;align-items:center;gap:8px}
.exercise-option:hover{background:#ecfdf9;border-color:#0d9488;color:#0d9488}
.exercise-option.selected{background:#ccfbf1;color:#0f766e;border-color:#0d9488;font-weight:600}
.exercise-option.correct{background:#d1fae5;border-color:#059669;color:#059669}
.exercise-option.wrong{background:#fef0f0;border-color:#f56c6c;color:#f56c6c}
.opt-mark{font-size:10px;font-weight:600;flex-shrink:0}
.opt-correct{color:#059669}
.opt-wrong{color:#f56c6c}
.exercise-answer{margin-top:10px;padding:10px 12px;background:#f0fdf4;border-radius:6px;font-size:12px;color:#0d9488;font-weight:600;border-left:3px solid #0d9488}
.short-answer-area{display:flex;flex-direction:column;align-items:flex-end;gap:10px;margin-top:10px}
.your-short-answer{margin-top:10px;padding:10px 12px;background:#f8fafc;border-radius:6px;font-size:12px;color:#475569;white-space:pre-wrap}
.stream-status{margin-bottom:12px}
.explanation-collapse{margin-top:10px;border-radius:8px;border:1px dashed #ccfbf1}
.explanation-collapse :deep(.el-collapse-item__header){font-size:12px;color:#0d9488;padding:0 12px;height:30px;background:#f8fffe}
.explanation-collapse :deep(.el-collapse-item__wrap){background:#fff}
.explanation-collapse :deep(.el-collapse-item__content){padding:10px 14px}
.exercise-explanation{display:flex;flex-direction:column;gap:6px;font-size:13px;color:#4b5563;line-height:1.7}
.exercise-explanation .short-ref-block{padding:8px;background:#f0f9eb;border-radius:6px;font-size:12px;color:#059669;font-style:italic}

.card-actions{margin-top:16px;display:flex;gap:8px;flex-wrap:wrap}
.progress-mini{display:flex;gap:10px;font-size:11px;color:#5a6888;margin-top:6px;line-height:1.5}

.video-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}
.video-card{border-radius:10px;overflow:hidden;border:1px solid #f1f3f8;transition:transform .2s ease,box-shadow .2s ease}
.video-card:hover{transform:translateY(-2px);box-shadow:0 8px 20px rgba(13,148,136,.15)}
.video-thumb{height:140px;background:linear-gradient(135deg,#0d9488 0%,#0f766e 100%);display:flex;align-items:center;justify-content:center;color:#fff;font-size:32px}
.video-info{padding:10px 12px}
.video-title{font-weight:700;font-size:13px;line-height:1.4;margin-bottom:6px;height:36px;overflow:hidden;color:#1f2937}
.video-desc{font-size:11px;color:#0d9488;height:16px;overflow:hidden;margin-bottom:4px;font-weight:600}
.video-meta{display:flex;gap:10px;font-size:10px;color:#8a96af;margin-bottom:4px}
.video-go-btn{margin-top:6px;width:100%;color:#0d9488;font-weight:700}

.platform-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:14px}
.platform-card{display:flex;flex-direction:column;align-items:center;padding:14px 6px;background:#fafbfc;border-radius:10px;text-decoration:none;transition:transform .15s,background .2s,border-color .2s;border:1px solid #f1f3f8}
.platform-card:hover{transform:translateY(-2px);background:#f0fdf4;border-color:#ccfbf1}
.platform-emoji{font-size:26px;margin-bottom:4px}
.platform-name{font-size:12px;font-weight:700;color:#1f2937}
.platform-desc{font-size:10px;color:#0d9488;margin-top:2px;text-align:center}

.quiz-config{display:flex;flex-direction:column;gap:16px}
.quiz-config-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}
.quiz-config-title{font-weight:800;font-size:15px;color:#1f2937}
.quiz-config-sub{margin-top:4px;font-size:12px;color:#5a6888}
.quiz-config-sub .quiz-note{margin-left:8px;color:#8a96af;font-weight:400}
.quiz-start-bar{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:16px;background:linear-gradient(135deg,#ecfdf9,#f0fdf4);border-radius:10px;border:1px solid #ccfbf1}
.quiz-meta{font-size:13px;color:#1f2937;font-weight:600}
.quiz-meta b{color:#0d9488}

.quiz-running{display:flex;flex-direction:column;gap:12px}
.quiz-progress-bar{height:6px;background:#e4e7ee;border-radius:99px;overflow:hidden}
.quiz-progress-fill{height:100%;background:linear-gradient(90deg,#0d9488,#0ea5a3);border-radius:99px;transition:width .3s ease}
.quiz-progress-text{font-size:12px;color:#5a6888;margin-top:2px}
.quiz-card{border:1px solid #ccfbf1;border-radius:12px;padding:18px;background:#fff}
.quiz-question{font-size:15px;font-weight:700;color:#1f2937;margin-bottom:14px;line-height:1.7}
.quiz-options{display:flex;flex-direction:column;gap:8px}
.quiz-nav{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-top:14px}

.quiz-result{display:flex;flex-direction:column;gap:16px}
.quiz-result-title{font-size:16px;font-weight:800;color:#1f2937}
.quiz-result-stats{display:flex;gap:14px;font-size:13px;color:#5a6888;padding:10px 12px;background:#f0fdf4;border-radius:8px;border-left:3px solid #0d9488;flex-wrap:wrap}
.quiz-result-stats .quiz-result-warn{margin-left:auto;color:#e6a23c;font-weight:600}
</style>
