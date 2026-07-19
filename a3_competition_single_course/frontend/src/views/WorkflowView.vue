<template>
  <div class="workflow-view">
    <el-row :gutter="20">
      <!-- 左侧：工作流节点 -->
      <el-col :xs="24" :lg="8">
        <el-card class="workflow-card">
          <template #header>
            <div class="card-header">
              <el-icon><Operation /></el-icon>
              <span>AI学习工作流</span>
              <el-tag type="success" size="small" style="margin-left: auto;">LangGraph引擎</el-tag>
            </div>
          </template>

          <div class="workflow-steps">
            <div
              v-for="(step, index) in steps"
              :key="step.id"
              class="workflow-step"
              :class="{
                completed: workflowStatus === 'completed' && currentStep > index,
                active: workflowStatus === 'running' && currentStep === index,
                pending: workflowStatus === 'pending' || (workflowStatus === 'completed' && currentStep <= index)
              }"
            >
              <div class="step-indicator">
                <div class="step-number">
                  <el-icon v-if="workflowStatus === 'completed' && currentStep > index"><Check /></el-icon>
                  <span v-else>{{ index + 1 }}</span>
                </div>
                <div v-if="index < steps.length - 1" class="step-line"></div>
              </div>
              <div class="step-content">
                <div class="step-icon">{{ step.icon }}</div>
                <div class="step-info">
                  <div class="step-name">{{ step.name }}</div>
                  <div class="step-desc">{{ step.description }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="workflow-actions">
            <el-button
              type="primary"
              size="large"
              :loading="isRunning"
              :disabled="isRunning"
              @click="startWorkflow"
              class="start-btn"
            >
              <el-icon v-if="!isRunning"><VideoPlay /></el-icon>
              {{ isRunning ? '执行中...' : '开始学习流程' }}
            </el-button>
            <el-button size="large" @click="explainWorkflow" :disabled="isRunning">
              <el-icon><InfoFilled /></el-icon>
              解释流程
            </el-button>
          </div>

          <!-- 工作流说明 -->
          <div v-if="workflowExplanation" class="workflow-explanation">
            <el-alert
              :title="workflowExplanation"
              type="info"
              show-icon
              :closable="false"
            />
          </div>
        </el-card>

        <!-- 历史记录 -->
        <el-card class="history-card" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <el-icon><Clock /></el-icon>
              <span>历史工作流</span>
              <el-tag type="info" size="small" style="margin-left: auto;">{{ workflowHistory.length }}条</el-tag>
            </div>
          </template>

          <div v-if="workflowHistory.length" class="history-list">
            <div
              v-for="item in workflowHistory"
              :key="item.id"
              class="history-item"
              @click="loadWorkflow(item)"
            >
              <div class="history-header">
                <span class="history-date">{{ formatDate(item.created_at) }}</span>
                <el-tag :type="item.status === 'completed' ? 'success' : 'info'" size="small">
                  {{ item.status === 'completed' ? '已完成' : '进行中' }}
                </el-tag>
              </div>
              <div class="history-summary">{{ item.summary || '学习流程记录' }}</div>
            </div>
          </div>
          <div v-else class="empty-history">
            <el-icon size="48" color="#ddd"><Document /></el-icon>
            <p>暂无历史记录</p>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：执行结果 -->
      <el-col :xs="24" :lg="16">
        <el-row :gutter="20">
          <!-- 诊断结果 -->
          <el-col :span="12">
            <el-card class="result-card">
              <template #header>
                <div class="card-header">
                  <el-icon><Search /></el-icon>
                  <span>诊断结果</span>
                  <el-tag v-if="diagnosis" type="success" size="small" style="margin-left: auto;">已生成</el-tag>
                </div>
              </template>

              <div v-if="diagnosis" class="diagnosis-content">
                <div class="diagnosis-summary">
                  <h4>总体评价</h4>
                  <p>{{ diagnosis.summary || '学习状态分析完成' }}</p>
                </div>

                <div v-if="diagnosis.weak_areas?.length" class="weak-areas">
                  <h4>薄弱环节</h4>
                  <div class="tag-list">
                    <el-tag
                      v-for="area in diagnosis.weak_areas"
                      :key="area"
                      type="danger"
                      effect="plain"
                    >
                      {{ area }}
                    </el-tag>
                  </div>
                </div>

                <div v-if="diagnosis.suggestions?.length" class="suggestions">
                  <h4>改进建议</h4>
                  <ul>
                    <li v-for="(s, i) in diagnosis.suggestions" :key="i">{{ s }}</li>
                  </ul>
                </div>
              </div>
              <div v-else class="empty-result">
                <el-icon size="48" color="#ddd"><Search /></el-icon>
                <p>点击开始学习流程后显示诊断结果</p>
              </div>
            </el-card>
          </el-col>

          <!-- 学习资源 -->
          <el-col :span="12">
            <el-card class="result-card">
              <template #header>
                <div class="card-header">
                  <el-icon><Reading /></el-icon>
                  <span>学习资源</span>
                  <el-tag v-if="resourcePack" type="success" size="small" style="margin-left: auto;">已生成</el-tag>
                </div>
              </template>

              <div v-if="resourcePack" class="resource-content">
                <div class="resource-lecture">
                  <h4>讲解内容</h4>
                  <div class="lecture-preview" v-html="getLecturePreview()"></div>
                  <el-button type="primary" size="small" @click="syncToPlanning">
                    <el-icon><Link /></el-icon>
                    同步到学习规划
                  </el-button>
                </div>

                <div class="resource-stats">
                  <el-row :gutter="12">
                    <el-col :span="8">
                      <div class="stat-item">
                        <div class="stat-value">{{ resourcePack.exercises_count || 0 }}</div>
                        <div class="stat-label">练习题</div>
                      </div>
                    </el-col>
                    <el-col :span="8">
                      <div class="stat-item">
                        <div class="stat-value">{{ resourcePack.flash_cards_count || 0 }}</div>
                        <div class="stat-label">记忆卡片</div>
                      </div>
                    </el-col>
                    <el-col :span="8">
                      <div class="stat-item">
                        <div class="stat-value">{{ resourcePack.quality_score || 0 }}</div>
                        <div class="stat-label">质量评分</div>
                      </div>
                    </el-col>
                  </el-row>
                </div>
              </div>
              <div v-else class="empty-result">
                <el-icon size="48" color="#ddd"><Reading /></el-icon>
                <p>点击开始学习流程后生成学习资源</p>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- Agent执行轨迹 -->
        <el-card class="traces-card" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <el-icon><Connection /></el-icon>
              <span>Agent执行轨迹</span>
              <el-tag type="info" size="small" style="margin-left: auto;">{{ agentTraces.length }}个Agent</el-tag>
            </div>
          </template>

          <div v-if="agentTraces.length" class="traces-timeline">
            <div
              v-for="(trace, index) in agentTraces"
              :key="index"
              class="trace-item"
              :class="trace.status"
            >
              <div class="trace-indicator">
                <div class="trace-dot"></div>
                <div v-if="index < agentTraces.length - 1" class="trace-line"></div>
              </div>
              <div class="trace-content">
                <div class="trace-header">
                  <el-tag :type="getAgentTag(trace.status)" size="small">
                    {{ trace.agent_name }}
                  </el-tag>
                  <span class="trace-status">{{ getStatusText(trace.status) }}</span>
                </div>
                <div v-if="trace.reasoning" class="trace-reasoning">
                  {{ trace.reasoning }}
                </div>
              </div>
            </div>
          </div>
          <div v-else class="empty-traces">
            <el-icon size="48" color="#ddd"><Connection /></el-icon>
            <p>开始学习流程后显示执行轨迹</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import {
  Operation, Check, VideoPlay, InfoFilled, Clock, Document,
  Search, Reading, Link, Connection
} from '@element-plus/icons-vue'

const router = useRouter()

const steps = [
  { id: 'diagnosis', name: '分析学习状态', description: '诊断知识薄弱点', icon: '🔍' },
  { id: 'planning', name: '制定学习策略', description: '生成个性化计划', icon: '📋' },
  { id: 'resource', name: '生成学习资源', description: '创建讲解和练习', icon: '📚' },
  { id: 'tutoring', name: '智能答疑辅导', description: 'AI一对一带学', icon: '🤖' },
  { id: 'evaluation', name: '评估学习效果', description: '检验学习成果', icon: '📊' }
]

const isRunning = ref(false)
const workflowStatus = ref<'pending' | 'running' | 'completed'>('pending')
const currentStep = ref(0)
const workflowExplanation = ref('')
const diagnosis = ref<any>(null)
const resourcePack = ref<any>(null)
const agentTraces = ref<any[]>([])
const workflowHistory = ref<any[]>([])

async function startWorkflow() {
  if (isRunning.value) return

  isRunning.value = true
  workflowStatus.value = 'running'
  diagnosis.value = null
  resourcePack.value = null
  agentTraces.value = []

  try {
    // 模拟步骤执行
    for (let i = 0; i < steps.length; i++) {
      currentStep.value = i
      await new Promise(resolve => setTimeout(resolve, 600))
    }

    const studentId = localStorage.getItem('student_id') || '1'
    const res = await fetch('/api/workflow/start-learning', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ student_id: studentId })
    })

    const data = await res.json()

    if (data.status === 'success') {
      diagnosis.value = data.diagnosis
      resourcePack.value = data.resource_pack
      agentTraces.value = data.agent_traces || []
      workflowExplanation.value = data.workflow_explanation || ''

      // 保存到历史记录
      saveWorkflowRecord(data)

      ElMessage.success('学习流程执行完成！')
    } else {
      ElMessage.error(data.message || '执行失败')
    }
  } catch (e) {
    ElMessage.error('网络错误，请重试')
  } finally {
    isRunning.value = false
    workflowStatus.value = 'completed'
  }
}

async function explainWorkflow() {
  try {
    const res = await fetch('/api/workflow/default/explain')
    const data = await res.json()
    if (data.status === 'success') {
      workflowExplanation.value = data.explanation
    }
  } catch (e) {
    ElMessage.error('获取解释失败')
  }
}

function saveWorkflowRecord(data: any) {
  const record = {
    id: Date.now(),
    created_at: new Date().toISOString(),
    status: 'completed',
    summary: data.diagnosis?.summary?.slice(0, 50) || '学习流程完成',
    diagnosis: data.diagnosis,
    resource_pack: data.resource_pack,
    study_plan: data.study_plan
  }
  workflowHistory.value.unshift(record)
  // 只保留最近10条
  if (workflowHistory.value.length > 10) {
    workflowHistory.value.pop()
  }
}

function loadWorkflow(item: any) {
  diagnosis.value = item.diagnosis
  resourcePack.value = item.resource_pack
}

function syncToPlanning() {
  ElMessage.success('已同步到学习规划页面')
  router.push('/planning')
}

function getLecturePreview(): string {
  if (!resourcePack.value?.lecture_text) return ''
  return resourcePack.value.lecture_text.slice(0, 300) + '...'
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

function getAgentTag(status: string): string {
  const map: Record<string, string> = {
    completed: 'success',
    running: 'warning',
    pending: 'info'
  }
  return map[status] || 'info'
}

function getStatusText(status: string): string {
  const map: Record<string, string> = {
    completed: '执行完成',
    running: '执行中',
    pending: '等待中'
  }
  return map[status] || status
}

onMounted(() => {
  // 加载历史记录（从localStorage）
  const saved = localStorage.getItem('workflow_history')
  if (saved) {
    try {
      workflowHistory.value = JSON.parse(saved)
    } catch (e) {}
  }
})
</script>

<style scoped lang="scss">
.workflow-view {
  padding: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.workflow-card,
.history-card,
.result-card,
.traces-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

// 工作流步骤
.workflow-steps {
  padding: 20px 0;
}

.workflow-step {
  display: flex;
  margin-bottom: 8px;

  &.completed .step-number {
    background: #67c23a;
    color: white;
  }

  &.completed .step-line {
    background: #67c23a;
  }

  &.active .step-number {
    background: #409eff;
    color: white;
    animation: pulse 1.5s infinite;
  }

  &.pending .step-number {
    background: #e0e0e0;
    color: #999;
  }
}

.step-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 40px;
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
  transition: all 0.3s;
}

.step-line {
  width: 2px;
  height: 40px;
  background: #e0e0e0;
  margin: 4px 0;
  transition: background 0.3s;
}

.step-content {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-left: 12px;
  flex: 1;
  transition: all 0.3s;

  .active & {
    background: #ecf5ff;
    border: 1px solid #409eff;
  }

  .completed & {
    background: #f0f9eb;
    border: 1px solid #67c23a;
  }
}

.step-icon {
  font-size: 24px;
}

.step-info {
  flex: 1;
}

.step-name {
  font-weight: 600;
  color: #333;
  margin-bottom: 2px;
}

.step-desc {
  font-size: 12px;
  color: #999;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.workflow-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.start-btn {
  flex: 1;
  background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
  border: none;
}

.workflow-explanation {
  margin-top: 16px;
}

// 诊断结果
.diagnosis-content {
  h4 {
    margin: 0 0 12px 0;
    color: #333;
    font-size: 14px;
  }

  p {
    margin: 0;
    color: #666;
    line-height: 1.6;
  }
}

.diagnosis-summary {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.weak-areas {
  margin-bottom: 16px;

  .tag-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
}

.suggestions {
  ul {
    margin: 0;
    padding-left: 20px;
    color: #666;

    li {
      margin-bottom: 4px;
    }
  }
}

// 学习资源
.resource-content {
  h4 {
    margin: 0 0 12px 0;
    color: #333;
    font-size: 14px;
  }
}

.lecture-preview {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 8px;
  font-size: 13px;
  color: #666;
  max-height: 150px;
  overflow-y: auto;
  margin-bottom: 12px;
}

.resource-stats {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #0d9488;
}

.stat-label {
  font-size: 12px;
  color: #999;
}

// Agent轨迹
.traces-timeline {
  padding: 10px 0;
}

.trace-item {
  display: flex;
  margin-bottom: 16px;

  &.completed .trace-dot {
    background: #67c23a;
  }

  &.running .trace-dot {
    background: #409eff;
    animation: pulse 1s infinite;
  }

  &.pending .trace-dot {
    background: #e0e0e0;
  }
}

.trace-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 20px;
}

.trace-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  transition: background 0.3s;
}

.trace-line {
  width: 2px;
  flex: 1;
  background: #e0e0e0;
  margin-top: 4px;
}

.trace-content {
  flex: 1;
  margin-left: 12px;
  padding-bottom: 16px;
}

.trace-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.trace-status {
  font-size: 12px;
  color: #999;
}

.trace-reasoning {
  font-size: 13px;
  color: #666;
  background: #f5f7fa;
  padding: 10px;
  border-radius: 6px;
  line-height: 1.5;
}

// 空状态
.empty-result,
.empty-history,
.empty-traces {
  text-align: center;
  padding: 40px 20px;
  color: #909399;

  p {
    margin-top: 12px;
    font-size: 14px;
  }
}

// 历史记录
.history-list {
  max-height: 300px;
  overflow-y: auto;
}

.history-item {
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: #f5f7fa;
  }

  &:last-child {
    border-bottom: none;
  }
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.history-date {
  font-size: 12px;
  color: #999;
}

.history-summary {
  font-size: 14px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
