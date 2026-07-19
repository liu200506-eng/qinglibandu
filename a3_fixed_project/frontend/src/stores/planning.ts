import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { LearningTask } from '@/types'

export const usePlanningStore = defineStore('planning', () => {
  const strategy = ref('balanced')
  const tasks = ref<LearningTask[]>([])
  const isGenerating = ref(false)
  const explanation = ref('')

  async function generatePlan(studentId: string, mode: string = 'balanced') {
    isGenerating.value = true
    try {
      const res = await fetch(`/api/planning/generate-plan?student_id=${studentId}&strategy_mode=${mode}`)
      const data = await res.json()
      if (data.status === 'success') {
        strategy.value = data.strategy
        tasks.value = data.tasks
        explanation.value = data.explanation || ''
      }
    } catch (e) {
      console.error('生成计划失败', e)
    } finally {
      isGenerating.value = false
    }
  }

  async function recommendStrategy(studentId: string) {
    try {
      const res = await fetch(`/api/planning/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: studentId })
      })
      const data = await res.json()
      if (data.status === 'success') {
        strategy.value = data.strategy
      }
    } catch (e) {
      console.error('推荐策略失败', e)
    }
  }

  async function adjustPlan(studentId: string, taskResults: object[]) {
    try {
      const res = await fetch(`/api/planning/adjust-plan?student_id=${studentId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskResults)
      })
      const data = await res.json()
      if (data.status === 'success') {
        tasks.value = data.adjusted_tasks
      }
    } catch (e) {
      console.error('调整计划失败', e)
    }
  }

  return {
    strategy,
    tasks,
    isGenerating,
    explanation,
    generatePlan,
    recommendStrategy,
    adjustPlan
  }
})