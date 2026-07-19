<template>
  <div class="learning-flow">
    <div class="flow-header">
      <h1 class="flow-title">🧠 个性化学习之旅</h1>
      <p class="flow-subtitle">AI驱动的智能学习路径，为你量身定制</p>
    </div>

    <div class="flow-timeline">
      <div 
        v-for="(step, index) in steps" 
        :key="step.id"
        class="timeline-step"
        :class="{ 
          active: currentStep === index, 
          completed: index < currentStep,
          disabled: index > currentStep 
        }"
      >
        <div class="step-dot">
          <span v-if="index < currentStep" class="check-icon">✓</span>
          <span v-else-if="index === currentStep" class="step-number">{{ index + 1 }}</span>
          <span v-else class="step-number">{{ index + 1 }}</span>
        </div>
        <div class="step-line" v-if="index < steps.length - 1"></div>
        <div class="step-label">{{ step.label }}</div>
      </div>
    </div>

    <div class="flow-content">
      <transition name="fade" mode="out-in">
        <div v-if="currentStep === 0" class="step-panel">
          <div class="panel-icon">🚀</div>
          <h2>开始你的学习之旅</h2>
          <p>我们将通过智能诊断和个性化规划，为你打造专属学习路径</p>
          <button class="primary-btn" @click="nextStep">开始学习</button>
        </div>

        <div v-else-if="currentStep === 1" class="step-panel">
          <div class="panel-icon">👤</div>
          <h2>自然语言建立初始画像</h2>
          <p>请用自然语言描述你的学习情况，例如：</p>
          <div class="examples">
            <span>"我是计算机网络初学者，每天只有20分钟学习时间"</span>
            <span>"我理论基础较好，但计算题容易出错"</span>
            <span>"我编程能力强，喜欢通过实践学习"</span>
          </div>
          <textarea 
            v-model="profileInput" 
            class="profile-input"
            placeholder="请描述你的学习背景、目标和偏好..."
          ></textarea>
          <div class="button-group">
            <button class="secondary-btn" @click="usePresetProfile('beginner')">使用预设：基础薄弱</button>
            <button class="secondary-btn" @click="usePresetProfile('intermediate')">使用预设：理论较好</button>
            <button class="secondary-btn" @click="usePresetProfile('advanced')">使用预设：编程能力强</button>
          </div>
          <button class="primary-btn" :disabled="!profileInput.trim()" @click="submitProfile">下一步</button>
          <button class="why-btn" @click="showWhy(1)">📖 为什么需要这个步骤？</button>
        </div>

        <div v-else-if="currentStep === 2" class="step-panel">
          <div class="panel-icon">📝</div>
          <h2>诊断测试</h2>
          <p>请完成以下5道诊断题，帮助系统了解你的知识掌握情况</p>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: (diagnosticProgress / 5 * 100) + '%' }"></div>
          </div>
          <div class="question-card" v-if="currentQuestion">
            <div class="question-header">
              <span class="question-number">第 {{ currentQuestionIndex + 1 }} 题</span>
              <span class="question-tag">{{ currentQuestion.category }}</span>
            </div>
            <div class="question-text">{{ currentQuestion.question }}</div>
            <div class="options">
              <label 
                v-for="(option, idx) in currentQuestion.options" 
                :key="idx"
                class="option-label"
                :class="{ selected: selectedAnswers[currentQuestionIndex] === idx }"
              >
                <input 
                  type="radio" 
                  :value="idx" 
                  v-model="selectedAnswers[currentQuestionIndex]"
                  @change="answerQuestion(idx)"
                >
                <span>{{ ['A', 'B', 'C', 'D'][idx] }}. {{ option }}</span>
              </label>
            </div>
          </div>
          <div v-if="diagnosticProgress === 5" class="complete-message">
            <span class="check-icon-large">✓</span>
            <p>诊断测试完成！</p>
            <button class="primary-btn" @click="finishDiagnostic">查看诊断结果</button>
          </div>
          <button class="why-btn" @click="showWhy(2)">📖 为什么需要这个步骤？</button>
        </div>

        <div v-else-if="currentStep === 3" class="step-panel">
          <div class="panel-icon">🎯</div>
          <h2>薄弱知识点分析</h2>
          <p>基于你的答题情况，系统发现以下薄弱点：</p>
          <div class="weak-points-grid">
            <div 
              v-for="point in weakPoints" 
              :key="point.name" 
              class="weak-point-card"
            >
              <div class="point-icon" :style="{ background: point.color + '20', color: point.color }">
                {{ point.icon }}
              </div>
              <div class="point-info">
                <div class="point-name">{{ point.name }}</div>
                <div class="point-desc">{{ point.description }}</div>
                <div class="point-score">掌握度: {{ point.score }}%</div>
              </div>
            </div>
          </div>
          <button class="primary-btn" @click="nextStep">继续规划学习路径</button>
          <button class="why-btn" @click="showWhy(3)">📖 为什么需要这个步骤？</button>
        </div>

        <div v-else-if="currentStep === 4" class="step-panel">
          <div class="panel-icon">🧬</div>
          <h2>Agent 规划过程</h2>
          <p>以下是系统各 Agent 的决策过程：</p>
          <div class="agent-timeline">
            <div 
              v-for="(agent, idx) in agentPlan" 
              :key="agent.name"
              class="agent-step"
              :class="{ active: agent.active, completed: idx < currentAgent }"
            >
              <div class="agent-icon">{{ agent.icon }}</div>
              <div class="agent-info">
                <div class="agent-name">{{ agent.name }}</div>
                <div class="agent-input">输入: {{ agent.input }}</div>
                <div class="agent-output">输出: {{ agent.output }}</div>
                <div class="agent-reason">决策理由: {{ agent.reason }}</div>
              </div>
            </div>
          </div>
          <button class="primary-btn" @click="nextStep">查看学习路径</button>
          <button class="why-btn" @click="showWhy(4)">📖 为什么需要这个步骤？</button>
        </div>

        <div v-else-if="currentStep === 5" class="step-panel">
          <div class="panel-icon">📚</div>
          <h2>个性化学习资源</h2>
          <p>根据你的画像和薄弱点，系统为你生成以下学习资源：</p>
          <div class="resources-grid">
            <div 
              v-for="resource in learningResources" 
              :key="resource.id"
              class="resource-card"
              @click="openResource(resource)"
            >
              <div class="resource-icon" :style="{ background: resource.color + '20', color: resource.color }">
                {{ resource.icon }}
              </div>
              <div class="resource-info">
                <div class="resource-title">{{ resource.title }}</div>
                <div class="resource-type">{{ resource.type }}</div>
                <div class="resource-meta">
                  <span>难度: {{ resource.difficulty }}</span>
                  <span>时长: {{ resource.duration }}</span>
                </div>
              </div>
              <div class="resource-action">→</div>
            </div>
          </div>
          <button class="primary-btn" @click="nextStep">开始练习</button>
          <button class="why-btn" @click="showWhy(5)">📖 为什么需要这个步骤？</button>
        </div>

        <div v-else-if="currentStep === 6" class="step-panel">
          <div class="panel-icon">💡</div>
          <h2>针对性练习</h2>
          <p>完成以下练习来巩固所学知识</p>
          <div class="practice-progress">
            <span>完成 {{ practiceProgress }}/{{ practiceQuestions.length }} 题</span>
          </div>
          <div class="question-card" v-if="currentPracticeQuestion">
            <div class="question-header">
              <span class="question-number">练习 {{ currentPracticeIndex + 1 }}</span>
              <span class="question-tag">{{ currentPracticeQuestion.knowledge_point }}</span>
            </div>
            <div class="question-text">{{ currentPracticeQuestion.question }}</div>
            <textarea 
              v-model="practiceAnswers[currentPracticeIndex]"
              class="practice-input"
              placeholder="请输入你的答案..."
            ></textarea>
            <button 
              class="secondary-btn" 
              :disabled="!practiceAnswers[currentPracticeIndex].trim()"
              @click="submitPracticeAnswer"
            >
              提交答案
            </button>
          </div>
          <div v-if="practiceProgress === practiceQuestions.length" class="complete-message">
            <span class="check-icon-large">✓</span>
            <p>练习完成！</p>
            <button class="primary-btn" @click="finishPractice">查看学习效果</button>
          </div>
          <button class="why-btn" @click="showWhy(6)">📖 为什么需要这个步骤？</button>
        </div>

        <div v-else-if="currentStep === 7" class="step-panel">
          <div class="panel-icon">📈</div>
          <h2>画像更新与效果评估</h2>
          <div class="profile-comparison">
            <div class="comparison-section">
              <h3>学习前画像</h3>
              <div class="radar-mini" ref="radarBefore"></div>
            </div>
            <div class="comparison-arrow">→</div>
            <div class="comparison-section">
              <h3>学习后画像</h3>
              <div class="radar-mini" ref="radarAfter"></div>
            </div>
          </div>
          <div class="improvement-stats">
            <div class="improvement-card">
              <div class="improvement-value">+{{ improvement.knowledge }}</div>
              <div class="improvement-label">知识掌握度</div>
            </div>
            <div class="improvement-card">
              <div class="improvement-value">+{{ improvement.efficiency }}</div>
              <div class="improvement-label">学习效率</div>
            </div>
            <div class="improvement-card">
              <div class="improvement-value">-{{ improvement.errors }}</div>
              <div class="improvement-label">错误率</div>
            </div>
          </div>
          <button class="primary-btn" @click="restartFlow">继续学习</button>
          <button class="why-btn" @click="showWhy(7)">📖 为什么需要这个步骤？</button>
        </div>
      </transition>
    </div>

    <div v-if="showWhyModal" class="why-modal">
      <div class="modal-content">
        <div class="modal-icon">📖</div>
        <h3>{{ whyContent.title }}</h3>
        <p>{{ whyContent.description }}</p>
        <button class="secondary-btn" @click="showWhyModal = false">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import * as echarts from 'echarts'

const steps = [
  { id: 'start', label: '开始学习' },
  { id: 'profile', label: '建立画像' },
  { id: 'diagnostic', label: '诊断测试' },
  { id: 'analysis', label: '薄弱点分析' },
  { id: 'planning', label: 'Agent规划' },
  { id: 'resources', label: '资源生成' },
  { id: 'practice', label: '针对性练习' },
  { id: 'update', label: '画像更新' }
]

const currentStep = ref(0)
const profileInput = ref('')
const selectedAnswers = ref<number[]>([])
const diagnosticProgress = ref(0)
const currentQuestionIndex = ref(0)
const currentAgent = ref(0)
const practiceAnswers = ref<string[]>([])
const practiceProgress = ref(0)
const currentPracticeIndex = ref(0)
const showWhyModal = ref(false)
const whyContent = ref({ title: '', description: '' })

const diagnosticQuestions = [
  {
    question: 'TCP协议工作在OSI模型的哪一层？',
    options: ['网络层', '传输层', '数据链路层', '应用层'],
    answer: 1,
    category: '传输层',
    knowledge_point: 'TCP基础'
  },
  {
    question: 'TCP慢启动阶段，cwnd（拥塞窗口）如何变化？',
    options: ['线性增长', '指数增长', '保持不变', '随机变化'],
    answer: 1,
    category: 'TCP拥塞控制',
    knowledge_point: '慢启动'
  },
  {
    question: 'HTTP协议默认使用的端口号是？',
    options: ['21', '22', '80', '443'],
    answer: 2,
    category: '应用层',
    knowledge_point: 'HTTP基础'
  },
  {
    question: 'IP地址192.168.1.1属于哪类地址？',
    options: ['A类', 'B类', 'C类', 'D类'],
    answer: 2,
    category: '网络层',
    knowledge_point: 'IP地址分类'
  },
  {
    question: 'TCP三次握手的目的是什么？',
    options: ['加密数据传输', '建立可靠连接', '压缩数据', '验证用户身份'],
    answer: 1,
    category: '传输层',
    knowledge_point: 'TCP连接管理'
  }
]

const practiceQuestions = [
  {
    question: '请解释TCP慢启动的工作原理，cwnd如何变化？',
    knowledge_point: '慢启动',
    difficulty: '中等'
  },
  {
    question: '假设TCP连接的ssthresh=8，初始cwnd=1，经过几个RTT后cwnd达到ssthresh？请写出计算过程。',
    knowledge_point: '慢启动计算',
    difficulty: '困难'
  },
  {
    question: 'TCP为什么需要拥塞控制？列举三种常见的拥塞控制算法。',
    knowledge_point: '拥塞控制',
    difficulty: '中等'
  }
]

const weakPoints = ref([
  { name: 'TCP慢启动', description: '对cwnd指数增长机制理解不透彻', score: 45, icon: '⚠️', color: '#ef4444' },
  { name: '拥塞避免', description: '线性增长阶段的判断条件不明确', score: 52, icon: '📉', color: '#f59e0b' },
  { name: 'RTT计算', description: '往返时间概念理解模糊', score: 58, icon: '⏱️', color: '#f59e0b' }
])

const agentPlan = ref([
  {
    name: '画像诊断Agent',
    icon: '🔍',
    input: '用户答题记录、学习行为数据',
    output: '识别薄弱知识点：TCP慢启动、拥塞避免',
    reason: '基于诊断测试结果，用户在TCP拥塞控制相关题目上正确率仅40%',
    active: true
  },
  {
    name: '学习规划Agent',
    icon: '📋',
    input: '薄弱知识点、学习目标',
    output: '规划学习路径：先理解原理→观看动画→完成计算题',
    reason: '针对基础薄弱用户，采用循序渐进策略',
    active: false
  },
  {
    name: '资源调度Agent',
    icon: '📦',
    input: '学习路径、用户偏好',
    output: '调度资源：动画视频、图解讲义、计算题练习',
    reason: '用户偏好视觉化学习，选择动画和图解形式',
    active: false
  },
  {
    name: '教学执行Agent',
    icon: '🎓',
    input: '学习资源、用户状态',
    output: '生成个性化讲义和练习',
    reason: '根据用户水平调整讲解深度，提供针对性练习',
    active: false
  },
  {
    name: '审查评估Agent',
    icon: '✅',
    input: '生成的资源、学习效果',
    output: '评估资源质量和学习效果',
    reason: '确保资源准确无误，学习效果达到预期',
    active: false
  }
])

const learningResources = ref([
  {
    id: 1,
    title: 'TCP慢启动动态演示',
    type: '动画视频',
    difficulty: '入门',
    duration: '5分钟',
    icon: '🎬',
    color: '#0d9488'
  },
  {
    id: 2,
    title: 'TCP拥塞控制图解讲义',
    type: '图解讲义',
    difficulty: '中等',
    duration: '10分钟',
    icon: '📊',
    color: '#0ea5e9'
  },
  {
    id: 3,
    title: 'TCP滑动窗口原理',
    type: '概念讲解',
    difficulty: '入门',
    duration: '8分钟',
    icon: '📚',
    color: '#f59e0b'
  },
  {
    id: 4,
    title: 'cwnd与rwnd区别辨析',
    type: '对比练习',
    difficulty: '中等',
    duration: '15分钟',
    icon: '🔄',
    color: '#8b5cf6'
  },
  {
    id: 5,
    title: 'TCP慢启动计算题集',
    type: '计算题',
    difficulty: '困难',
    duration: '20分钟',
    icon: '🧮',
    color: '#ef4444'
  }
])

const improvement = ref({
  knowledge: 25,
  efficiency: 18,
  errors: 30
})

const currentQuestion = computed(() => diagnosticQuestions[currentQuestionIndex.value])
const currentPracticeQuestion = computed(() => practiceQuestions[currentPracticeIndex.value])

function nextStep() {
  if (currentStep.value < steps.length - 1) {
    currentStep.value++
  }
}

function usePresetProfile(type: string) {
  const presets = {
    beginner: '我是计算机网络初学者，基础比较薄弱，经常混淆cwnd与rwnd的概念，每天大约有20分钟学习时间。',
    intermediate: '我理论基础较好，但是计算题容易出错，特别是涉及RTT和cwnd计算的题目。',
    advanced: '我编程能力强，喜欢通过实践学习，希望能通过代码仿真来理解TCP协议。'
  }
  profileInput.value = presets[type]
}

function submitProfile() {
  nextStep()
}

function answerQuestion(idx: number) {
  selectedAnswers.value[currentQuestionIndex.value] = idx
  if (currentQuestionIndex.value < diagnosticQuestions.length - 1) {
    setTimeout(() => {
      currentQuestionIndex.value++
      diagnosticProgress.value++
    }, 500)
  } else {
    diagnosticProgress.value++
  }
}

function finishDiagnostic() {
  nextStep()
}

function openResource(resource: any) {
  alert(`打开资源: ${resource.title}`)
}

function submitPracticeAnswer() {
  if (currentPracticeIndex.value < practiceQuestions.length - 1) {
    setTimeout(() => {
      currentPracticeIndex.value++
      practiceProgress.value++
    }, 500)
  } else {
    practiceProgress.value++
  }
}

function finishPractice() {
  nextStep()
}

function restartFlow() {
  currentStep.value = 0
  diagnosticProgress.value = 0
  currentQuestionIndex.value = 0
  selectedAnswers.value = []
  practiceProgress.value = 0
  currentPracticeIndex.value = 0
  practiceAnswers.value = []
}

function showWhy(step: number) {
  const reasons = {
    1: {
      title: '为什么需要建立学习画像？',
      description: '学习画像通过收集你的学习背景、目标和偏好，帮助系统理解你的独特需求。这是实现个性化学习的基础。没有画像，系统只能提供千篇一律的内容；有了画像，系统可以为你量身定制学习路径。'
    },
    2: {
      title: '为什么需要诊断测试？',
      description: '诊断测试帮助系统客观评估你的知识掌握情况，识别真实的薄弱点。主观描述可能存在偏差，而客观测试能提供更准确的数据。这确保了后续规划基于真实的学习状态。'
    },
    3: {
      title: '为什么需要分析薄弱点？',
      description: '识别薄弱点是精准教学的前提。通过分析，系统可以知道哪些知识点需要重点关注，哪些可以快速浏览。这避免了盲目学习，提高了学习效率。'
    },
    4: {
      title: '为什么展示Agent规划过程？',
      description: '透明的规划过程让你了解系统的决策逻辑。每个Agent都有明确的职责，它们协同工作完成学习路径规划。这展示了系统的智能决策能力，也让你对学习路径更有信心。'
    },
    5: {
      title: '为什么需要个性化资源？',
      description: '不同学生适合不同类型的资源。初学者可能需要更多动画和图解，高级学生可能更偏好代码实践。个性化资源确保你获得最适合的学习材料。'
    },
    6: {
      title: '为什么需要针对性练习？',
      description: '练习是巩固知识的关键。针对性练习直接针对你的薄弱点，帮助你快速提高。通过主动答题，你可以检验自己的理解程度，发现新的问题。'
    },
    7: {
      title: '为什么需要画像更新？',
      description: '学习是一个动态过程，你的知识状态在不断变化。画像更新机制记录你的进步，确保系统始终基于最新的状态提供服务。这形成了一个持续优化的学习闭环。'
    }
  }
  whyContent.value = reasons[step]
  showWhyModal.value = true
}

let radarBeforeChart: echarts.ECharts | null = null
let radarAfterChart: echarts.ECharts | null = null

function initRadarCharts() {
  const beforeEl = document.querySelector('.radar-mini') as HTMLElement
  const afterEl = document.querySelectorAll('.radar-mini')[1] as HTMLElement
  
  const baseOption = {
    backgroundColor: 'transparent',
    radar: {
      indicator: [
        { name: '掌握度', max: 100 },
        { name: '效率', max: 100 },
        { name: '持续性', max: 100 },
        { name: '错误模式', max: 100 },
        { name: '先修缺口', max: 100 },
        { name: '目标匹配', max: 100 },
        { name: '资源偏好', max: 100 }
      ],
      radius: '65%',
      center: ['50%', '50%'],
      splitNumber: 4,
      axisName: { color: '#64748b', fontSize: 8 },
      splitLine: { lineStyle: { color: 'rgba(0,0,0,0.1)' } },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: 'rgba(0,0,0,0.1)' } }
    },
    series: [{
      type: 'radar',
      data: []
    }]
  }

  if (beforeEl) {
    radarBeforeChart = echarts.init(beforeEl)
    radarBeforeChart.setOption({
      ...baseOption,
      series: [{
        type: 'radar',
        data: [{
          value: [50, 45, 60, 55, 65, 70, 55],
          name: '学习前',
          lineStyle: { width: 2, color: '#94a3b8' },
          areaStyle: { color: 'rgba(148, 163, 184, 0.2)' },
          itemStyle: { color: '#94a3b8' }
        }]
      }]
    })
  }

  if (afterEl) {
    radarAfterChart = echarts.init(afterEl)
    radarAfterChart.setOption({
      ...baseOption,
      series: [{
        type: 'radar',
        data: [{
          value: [75, 63, 68, 70, 45, 75, 70],
          name: '学习后',
          lineStyle: { width: 2, color: '#0d9488' },
          areaStyle: { color: 'rgba(13, 148, 136, 0.2)' },
          itemStyle: { color: '#0d9488' }
        }]
      }]
    })
  }
}

onMounted(() => {
  setTimeout(initRadarCharts, 500)
})
</script>

<style scoped>
.learning-flow {
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 20px;
}

.flow-header {
  text-align: center;
  margin-bottom: 40px;
}

.flow-title {
  font-size: 2.5rem;
  font-weight: 800;
  background: linear-gradient(90deg, #0d9488, #0ea5e9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 10px;
}

.flow-subtitle {
  font-size: 1.1rem;
  color: #64748b;
}

.flow-timeline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40px;
  padding: 20px 0;
  border-bottom: 2px solid #e2e8f0;
}

.timeline-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  flex: 1;
}

.step-dot {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: bold;
  color: #94a3b8;
  transition: all 0.3s ease;
  z-index: 1;
}

.timeline-step.completed .step-dot {
  background: #059669;
  color: white;
}

.timeline-step.active .step-dot {
  background: #0d9488;
  color: white;
  transform: scale(1.2);
  box-shadow: 0 0 20px rgba(13, 148, 136, 0.4);
}

.step-line {
  position: absolute;
  top: 20px;
  left: 50%;
  width: calc(100% - 20px);
  height: 3px;
  background: #e2e8f0;
  z-index: 0;
}

.timeline-step.completed .step-line {
  background: #059669;
}

.step-label {
  margin-top: 10px;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-align: center;
  transition: color 0.3s ease;
}

.timeline-step.active .step-label {
  color: #0d9488;
}

.timeline-step.completed .step-label {
  color: #059669;
}

.flow-content {
  min-height: 400px;
}

.step-panel {
  text-align: center;
  padding: 40px 20px;
}

.panel-icon {
  font-size: 4rem;
  margin-bottom: 20px;
}

.step-panel h2 {
  font-size: 1.8rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 15px;
}

.step-panel p {
  font-size: 1.1rem;
  color: #64748b;
  margin-bottom: 30px;
}

.primary-btn {
  padding: 14px 32px;
  font-size: 1.1rem;
  font-weight: 600;
  background: linear-gradient(90deg, #0d9488, #0ea5e9);
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.primary-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(13, 148, 136, 0.3);
}

.primary-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.secondary-btn {
  padding: 10px 20px;
  font-size: 0.95rem;
  font-weight: 500;
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin: 5px;
}

.secondary-btn:hover:not(:disabled) {
  background: #e2e8f0;
}

.secondary-btn:disabled {
  opacity: 0.5;
}

.why-btn {
  margin-top: 20px;
  padding: 8px 16px;
  font-size: 0.9rem;
  background: transparent;
  color: #0ea5e9;
  border: 1px dashed #0ea5e9;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.why-btn:hover {
  background: rgba(14, 165, 233, 0.1);
}

.examples {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
  text-align: left;
}

.examples span {
  padding: 10px 15px;
  background: #f8fafc;
  border-left: 4px solid #0d9488;
  border-radius: 4px;
  font-size: 0.95rem;
  color: #475569;
}

.profile-input {
  width: 100%;
  height: 120px;
  padding: 15px;
  font-size: 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  resize: vertical;
  transition: border-color 0.3s ease;
}

.profile-input:focus {
  outline: none;
  border-color: #0d9488;
}

.button-group {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  margin-bottom: 20px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  margin-bottom: 20px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #0d9488, #0ea5e9);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.question-card {
  background: white;
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  text-align: left;
  margin-bottom: 20px;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.question-number {
  font-size: 0.9rem;
  font-weight: 600;
  color: #0d9488;
}

.question-tag {
  padding: 4px 12px;
  font-size: 0.8rem;
  background: #f0fdf4;
  color: #059669;
  border-radius: 20px;
}

.question-text {
  font-size: 1.2rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 25px;
  line-height: 1.5;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.option-label {
  display: flex;
  align-items: center;
  padding: 15px;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1rem;
  color: #475569;
}

.option-label:hover {
  background: #f0fdfa;
  border-color: #ccfbf1;
}

.option-label.selected {
  background: #f0fdfa;
  border-color: #0d9488;
}

.option-label input {
  margin-right: 15px;
  width: 20px;
  height: 20px;
  accent-color: #0d9488;
}

.complete-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
}

.check-icon-large {
  font-size: 4rem;
  color: #059669;
  margin-bottom: 20px;
}

.weak-points-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.weak-point-card {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.point-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.point-info {
  flex: 1;
}

.point-name {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 5px;
}

.point-desc {
  font-size: 0.9rem;
  color: #64748b;
  margin-bottom: 10px;
}

.point-score {
  font-size: 0.9rem;
  font-weight: 600;
  color: #ef4444;
}

.agent-timeline {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 30px;
}

.agent-step {
  display: flex;
  gap: 15px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  border-left: 4px solid #e2e8f0;
  transition: all 0.3s ease;
}

.agent-step.active {
  border-left-color: #0d9488;
  box-shadow: 0 4px 20px rgba(13, 148, 136, 0.1);
}

.agent-step.completed {
  border-left-color: #059669;
  background: #f0fdf4;
}

.agent-icon {
  font-size: 2rem;
}

.agent-info {
  flex: 1;
}

.agent-name {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 5px;
}

.agent-input,
.agent-output,
.agent-reason {
  font-size: 0.9rem;
  margin-bottom: 3px;
}

.agent-input {
  color: #64748b;
}

.agent-output {
  color: #0d9488;
}

.agent-reason {
  color: #0ea5e9;
  font-style: italic;
}

.resources-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
}

.resource-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: all 0.3s ease;
}

.resource-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.resource-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.resource-info {
  flex: 1;
}

.resource-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 3px;
}

.resource-type {
  font-size: 0.85rem;
  color: #64748b;
  margin-bottom: 8px;
}

.resource-meta {
  display: flex;
  gap: 15px;
  font-size: 0.85rem;
  color: #94a3b8;
}

.resource-action {
  font-size: 1.5rem;
  color: #cbd5e1;
}

.practice-progress {
  text-align: right;
  font-size: 0.9rem;
  color: #64748b;
  margin-bottom: 20px;
}

.practice-input {
  width: 100%;
  height: 100px;
  padding: 15px;
  font-size: 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  resize: vertical;
  margin-bottom: 20px;
}

.practice-input:focus {
  outline: none;
  border-color: #0d9488;
}

.profile-comparison {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
  margin-bottom: 40px;
}

.comparison-section {
  text-align: center;
}

.comparison-section h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 15px;
}

.radar-mini {
  width: 250px;
  height: 200px;
}

.comparison-arrow {
  font-size: 3rem;
  color: #0d9488;
}

.improvement-stats {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin-bottom: 40px;
}

.improvement-card {
  text-align: center;
  padding: 25px 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.improvement-value {
  font-size: 2rem;
  font-weight: 800;
  color: #059669;
  margin-bottom: 5px;
}

.improvement-label {
  font-size: 0.95rem;
  color: #64748b;
}

.why-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 20px;
  padding: 40px;
  max-width: 500px;
  width: 90%;
  text-align: center;
}

.modal-icon {
  font-size: 3rem;
  margin-bottom: 20px;
}

.modal-content h3 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 15px;
}

.modal-content p {
  font-size: 1rem;
  color: #64748b;
  line-height: 1.6;
  margin-bottom: 25px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
</style>
