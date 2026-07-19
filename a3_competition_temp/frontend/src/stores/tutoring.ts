import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTutoringStore = defineStore('tutoring', () => {
  const messages = ref<{ role: 'user' | 'assistant'; content: string }[]>([])
  const mode = ref<'direct' | 'socratic'>('direct')
  const isTyping = ref(false)
  const emotionalFeedback = ref('')

  async function sendMessage(studentId: string, message: string) {
    messages.value.push({ role: 'user', content: message })
    isTyping.value = true
    try {
      const res = await fetch(`/api/tutoring/chat?student_id=${studentId}&message=${encodeURIComponent(message)}&mode=${mode.value}`)
      const data = await res.json()
      if (data.status === 'success') {
        messages.value.push({ role: 'assistant', content: data.response })
        emotionalFeedback.value = data.emotional_feedback || ''
      }
    } catch (e) {
      messages.value.push({ role: 'assistant', content: '抱歉，我现在无法回答，请稍后再试。' })
    } finally {
      isTyping.value = false
    }
  }

  function switchMode(newMode: 'direct' | 'socratic') {
    mode.value = newMode
    emotionalFeedback.value = ''
  }

  function clearMessages() {
    messages.value = []
    emotionalFeedback.value = ''
  }

  return {
    messages,
    mode,
    isTyping,
    emotionalFeedback,
    sendMessage,
    switchMode,
    clearMessages
  }
})