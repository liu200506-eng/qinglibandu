import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useFeedbackStore = defineStore('feedback', () => {
  const errorPatterns = ref<{ type: string; count: number; description: string }[]>([])
  const improvementHistory = ref<{ date: string; accuracy: number; score: number }[]>([])
  const latestFeedback = ref<{ accuracy: number; score: number; summary: string } | null>(null)

  async function fetchErrorPatterns(studentId: string) {
    try {
      const res = await fetch(`/api/feedback/${studentId}/error-patterns`)
      const data = await res.json()
      if (data.status === 'success') {
        errorPatterns.value = data.patterns
      }
    } catch (e) {
      console.error('获取错误模式失败', e)
    }
  }

  async function submitAnswer(studentId: string, questionId: string, answer: string, isCorrect: boolean) {
    try {
      const res = await fetch(`/api/feedback/submit-answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: studentId, question_id: questionId, answer, is_correct: isCorrect })
      })
      const data = await res.json()
      return data.status === 'success'
    } catch (e) {
      console.error('提交答案失败', e)
      return false
    }
  }

  async function submitFeedback(studentId: string, taskId: string, accuracy: number, score: number) {
    try {
      const res = await fetch(`/api/feedback/submit-feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: studentId, task_id: taskId, accuracy, score })
      })
      const data = await res.json()
      if (data.status === 'success') {
        latestFeedback.value = { accuracy, score, summary: data.improvement_summary }
        improvementHistory.value.push({
          date: new Date().toISOString().split('T')[0],
          accuracy: accuracy * 100,
          score
        })
      }
    } catch (e) {
      console.error('提交反馈失败', e)
    }
  }

  return {
    errorPatterns,
    improvementHistory,
    latestFeedback,
    fetchErrorPatterns,
    submitAnswer,
    submitFeedback
  }
})