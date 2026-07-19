<template>
  <div class="planning-view">
    <el-row :gutter="20">
      <el-col :xs="24" :sm="24" :md="8">
        <el-card class="strategy-card">
          <template #header>
            <div class="card-header">
              <el-icon><Operation /></el-icon>
              <span>学习策略</span>
            </div>
          </template>
          <div class="strategy-buttons">
            <div
              v-for="mode in strategies"
              :key="mode.value"
              class="strategy-item"
              :class="{ active: strategy === mode.value }"
              @click="selectStrategy(mode)"
            >
              <div class="strategy-icon">{{ mode.icon }}</div>
              <div class="strategy-content">
                <div class="strategy-name">{{ mode.name }}</div>
                <div class="strategy-desc">{{ mode.description }}</div>
              </div>
              <el-icon v-if="strategy === mode.value" class="check-icon"><CircleCheck /></el-icon>
            </div>
          </div>
          <el-button type="primary" class="generate-btn" @click="openPlanForm">
            <el-icon><Edit /></el-icon>
            生成学习计划
          </el-button>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="24" :md="16">
        <el-card class="plan-card">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>学习计划</span>
            </div>
          </template>

          <div v-if="loading" class="loading-container">
            <el-icon class="is-loading"><Loading /></el-icon>
            <p>正在生成您的个性化学习计划...</p>
          </div>

          <div v-else-if="tasks.length > 0" class="plan-content">
            <el-alert
              type="success"
              :title="planExplanation"
              :closable="false"
              show-icon
              class="plan-alert"
            />

            <div class="plan-summary">
              <div class="summary-item">
                <el-icon><Collection /></el-icon>
                <span>{{ tasks.length }} 个任务</span>
              </div>
              <div class="summary-item">
                <el-icon><Timer /></el-icon>
                <span>约 {{ totalMinutes }} 分钟</span>
              </div>
              <div class="summary-item">
                <el-icon><TrendCharts /></el-icon>
                <span>预计提升 {{ expectedGain }}%</span>
              </div>
            </div>

            <el-timeline>
              <el-timeline-item
                v-for="(task, index) in tasks"
                :key="task.task_id"
                :timestamp="`${task.estimated_minutes}分钟`"
                placement="top"
                :type="getTimelineColor(task.task_type)"
              >
                <el-card class="task-card" shadow="hover">
                  <div class="task-header">
                    <div class="task-title-row">
                      <span class="task-index">{{ index + 1 }}</span>
                      <span class="task-title">{{ task.title }}</span>
                    </div>
                    <el-tag :type="getTaskTypeTag(task.task_type)" size="small">
                      {{ getTaskTypeName(task.task_type) }}
                    </el-tag>
                  </div>

                  <div class="task-meta">
                    <span class="meta-item">
                      <el-icon><Opportunity /></el-icon>
                      难度: {{ getDifficultyLabel(task.difficulty) }}
                    </span>
                    <span class="meta-item">
                      <el-icon><Sunny /></el-icon>
                      预期收益: {{ (task.expected_gain * 100).toFixed(0) }}%
                    </span>
                  </div>

                  <div v-if="task.explanation" class="task-explanation">
                    <el-icon><InfoFilled /></el-icon>
                    {{ task.explanation }}
                  </div>

                  <div class="task-actions">
                    <el-button type="primary" size="small" @click="startTask(task)">
                      <el-icon><VideoPlay /></el-icon>
                      开始学习
                    </el-button>
                    <el-button size="small" @click="markComplete(task)">
                      <el-icon><Check /></el-icon>
                      标记完成
                    </el-button>
                  </div>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </div>

          <div v-else class="empty-container">
            <el-empty description="暂无学习计划">
              <el-button type="primary" @click="openPlanForm">
                <el-icon><Edit /></el-icon>
                立即生成
              </el-button>
            </el-empty>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 生成计划表单弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="生成学习计划"
      width="600px"
      :close-on-click-modal="false"
      class="plan-form-dialog"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="学习科目">
          <el-select v-model="formData.subject" placeholder="请选择学习科目" style="width: 100%">
            <el-option label="计算机网络" value="计算机网络" />
            <el-option label="数学" value="数学" />
            <el-option label="语文" value="语文" />
            <el-option label="英语" value="英语" />
            <el-option label="物理" value="物理" />
            <el-option label="化学" value="化学" />
            <el-option label="生物" value="生物" />
            <el-option label="历史" value="历史" />
            <el-option label="地理" value="地理" />
            <el-option label="政治" value="政治" />
          </el-select>
        </el-form-item>

        <el-form-item label="薄弱知识点">
          <el-input
            v-model="formData.weakPoints"
            type="textarea"
            :rows="3"
            placeholder="请输入您需要加强的知识点，多个知识点用逗号分隔"
          />
        </el-form-item>

        <el-form-item label="目标分数">
          <el-slider
            v-model="formData.targetScore"
            :min="72"
            :max="120"
            :step="5"
            show-stops
            :format-tooltip="(val: number) => `${val}分`"
          />
          <div class="slider-label">目标: {{ formData.targetScore }}分（满分120）</div>
        </el-form-item>

        <el-form-item label="备考周期">
          <el-select v-model="formData.examPeriod" placeholder="请选择备考周期" style="width: 100%">
            <el-option label="1周内" value="1周" />
            <el-option label="2周" value="2周" />
            <el-option label="1个月" value="1个月" />
            <el-option label="3个月" value="3个月" />
            <el-option label="6个月" value="6个月" />
            <el-option label="长期学习" value="长期" />
          </el-select>
        </el-form-item>

        <el-form-item label="学习强度">
          <el-radio-group v-model="formData.intensity">
            <el-radio label="light">轻松</el-radio>
            <el-radio label="medium">适中</el-radio>
            <el-radio label="intense">紧张</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitPlanForm">
          <el-icon v-if="!submitting"><Select /></el-icon>
          确认生成
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Operation,
  CircleCheck,
  Edit,
  Document,
  Loading,
  Collection,
  Timer,
  TrendCharts,
  Opportunity,
  Sunny,
  InfoFilled,
  VideoPlay,
  Check,
  Select
} from '@element-plus/icons-vue'
import type { LearningTask } from '@/types'

const router = useRouter()
const dialogVisible = ref(false)
const submitting = ref(false)
const loading = ref(false)
const formRef = ref()

const strategy = ref('balanced')
const tasks = ref<LearningTask[]>([])
const planExplanation = ref('')

const formData = ref({
  subject: '',
  weakPoints: '',
  targetScore: 85,
  examPeriod: '1个月',
  intensity: 'medium'
})

const formRules = {
  subject: [{ required: true, message: '请选择学习科目', trigger: 'change' }]
}

const strategies = [
  { value: 'weakness_fix', name: '查漏补缺', description: '专注薄弱知识点', icon: '🎯' },
  { value: 'score_boost', name: '提分冲刺', description: '快速提升分数', icon: '🚀' },
  { value: 'exam_sprint', name: '考试冲刺', description: '考前突击复习', icon: '⏰' },
  { value: 'balanced', name: '平衡发展', description: '全面稳步提升', icon: '⚖️' }
]

const totalMinutes = computed(() =>
  tasks.value.reduce((sum, t) => sum + (t.estimated_minutes || 0), 0)
)

const expectedGain = computed(() => {
  const total = tasks.value.reduce((sum, t) => sum + (t.expected_gain || 0), 0)
  return (total * 100).toFixed(0)
})

function selectStrategy(mode: any) {
  strategy.value = mode.value
}

function openPlanForm() {
  dialogVisible.value = true
}

async function submitPlanForm() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      submitting.value = true
      dialogVisible.value = false

      try {
        const studentId = localStorage.getItem('student_id') || '1'
        const res = await fetch('/api/planning/generate-plan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            student_id: studentId,
            strategy_mode: strategy.value,
            weak_points: formData.value.weakPoints.split(',').map(s => s.trim()).filter(Boolean),
            target_score: formData.value.targetScore,
            exam_period: formData.value.examPeriod,
            subject: formData.value.subject
          })
        })

        const data = await res.json()
        if (data.status === 'success') {
          tasks.value = data.tasks || []
          planExplanation.value = data.explanation || '学习计划已生成'
          ElMessage.success('学习计划生成成功！')

          // 保存计划到数据库
          try {
            await fetch(`/api/db/study-plans/${studentId}`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                title: `${formData.value.subject || '综合'}学习计划`,
                plan_type: strategy.value,
                target_score: formData.value.targetScore,
                study_period: formData.value.examPeriod,
                weak_points: formData.value.weakPoints.split(',').map(s => s.trim()).filter(Boolean),
                content: JSON.stringify(data.tasks)
              })
            })
          } catch (e) {
            console.error('保存计划失败', e)
          }
        } else {
          ElMessage.error(data.message || '生成失败')
        }
      } catch (e) {
        console.error('生成计划失败', e)
        ElMessage.error('网络错误，请重试')
      } finally {
        submitting.value = false
      }
    }
  })
}

function getTaskTypeName(type: string): string {
  const map: Record<string, string> = {
    lecture: '视频讲解',
    exercise: '强化练习',
    review: '知识回顾',
    quiz: '阶段测验',
    practice: '实操演练',
    flashcard: '闪卡记忆'
  }
  return map[type] || type
}

function getTaskTypeTag(type: string): string {
  const map: Record<string, string> = {
    lecture: 'info',
    exercise: 'primary',
    review: 'success',
    quiz: 'warning',
    practice: 'danger',
    flashcard: 'success'
  }
  return map[type] || 'info'
}

function getTimelineColor(type: string): string {
  const map: Record<string, string> = {
    lecture: 'primary',
    exercise: 'success',
    review: 'warning',
    quiz: 'info',
    practice: 'danger',
    flashcard: 'success'
  }
  return map[type] || 'primary'
}

function getDifficultyLabel(difficulty: number): string {
  if (difficulty < 0.4) return '简单'
  if (difficulty < 0.7) return '中等'
  return '困难'
}

function startTask(task: LearningTask) {
  const subjects = (task.knowledge_points || []).length ? task.knowledge_points.join(',') : ''
  localStorage.setItem('planner_pending', JSON.stringify({
    subject: formData.value.subject || '计算机网络',
    title: task.title,
    knowledge: subjects,
    ts: Date.now(),
  }))
  ElMessage.success(`正在进入「${task.title}」学习...`)
  router.push('/resources')
}

function markComplete(task: LearningTask) {
  task.status = 'completed'
  ElMessage.success('任务已标记完成')
}

onMounted(() => {
  // 初始化时加载推荐策略
})
</script>

<style scoped>
.planning-view {
  padding: 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
  font-size: 16px;
}

.strategy-card {
  margin-bottom: 20px;
}

.strategy-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.strategy-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border: 2px solid #e8e8e8;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
}

.strategy-item:hover {
  border-color: #0d9488;
  background: #f8f9ff;
}

.strategy-item.active {
  border-color: #0d9488;
  background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
  color: white;
}

.strategy-item.active .strategy-desc {
  color: rgba(255, 255, 255, 0.8);
}

.strategy-icon {
  font-size: 28px;
  margin-right: 12px;
}

.strategy-content {
  flex: 1;
}

.strategy-name {
  font-weight: bold;
  font-size: 15px;
  margin-bottom: 4px;
}

.strategy-desc {
  font-size: 12px;
  color: #999;
}

.check-icon {
  font-size: 20px;
  color: #67c23a;
}

.generate-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
  border: none;
}

.generate-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.plan-card {
  min-height: 500px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #999;
}

.loading-container .el-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: #0d9488;
}

.plan-alert {
  margin-bottom: 20px;
}

.plan-summary {
  display: flex;
  gap: 24px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 24px;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
  font-size: 14px;
}

.summary-item .el-icon {
  color: #0d9488;
}

.task-card {
  border-radius: 8px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.task-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.task-index {
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}

.task-title {
  font-weight: bold;
  font-size: 15px;
  color: #333;
}

.task-meta {
  display: flex;
  gap: 20px;
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #666;
}

.meta-item .el-icon {
  color: #909399;
}

.task-explanation {
  font-size: 13px;
  color: #999;
  background: #f5f7fa;
  padding: 10px 12px;
  border-radius: 6px;
  margin-bottom: 12px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.task-explanation .el-icon {
  color: #909399;
  margin-top: 2px;
}

.task-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.empty-container {
  padding: 60px 20px;
}

.slider-label {
  text-align: center;
  margin-top: 8px;
  color: #0d9488;
  font-weight: bold;
}

:deep(.el-timeline-item__node--primary) {
  background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
}

:deep(.el-dialog__header) {
  background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
  color: white;
  margin: 0;
  padding: 20px;
}

:deep(.el-dialog__title) {
  color: white;
}

:deep(.el-dialog__close) {
  color: white;
}
</style>