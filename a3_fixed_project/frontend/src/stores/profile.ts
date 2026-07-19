import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { LearningProfile, KnowledgeState } from '@/types'

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const useProfileStore = defineStore('profile', () => {
  const profile = ref<LearningProfile | null>(null)
  const isLoading = ref(false)
  const error = ref('')

  const radarData = computed(() => {
    if (!profile.value) return []
    return [
      { name: '知识掌握', value: profile.value.knowledge_mastery },
      { name: '学习稳定性', value: profile.value.learning_stability },
      { name: '反应速度', value: profile.value.response_speed },
      { name: '错因健康度', value: profile.value.error_pattern_score },
      { name: '自主学习', value: profile.value.self_driven_score },
      { name: '迁移能力', value: profile.value.transfer_ability },
      { name: '情绪状态', value: profile.value.emotional_state }
    ]
  })

  const weakPoints = computed(() => {
    if (!profile.value) return []
    return Object.values(profile.value.knowledge_states).filter(
      (ks: KnowledgeState) => ks.mastery < 60
    )
  })

  async function fetchProfile(studentId: string) {
    isLoading.value = true
    error.value = ''
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 8000)

      const res = await fetch(`/api/profile/${studentId}`, {
        signal: controller.signal,
        headers: authHeaders()
      })
      clearTimeout(timeoutId)

      const data = await res.json()
      if (data.status === 'success') {
        profile.value = data.profile
      }
    } catch (e) {
      error.value = '获取画像失败或超时'
    } finally {
      isLoading.value = false
    }
  }

  async function updateProfile(studentId: string, updates: object) {
    try {
      const res = await fetch(`/api/profile/${studentId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      })
      const data = await res.json()
      if (data.status === 'success') {
        profile.value = data.profile
      }
    } catch (e) {
      error.value = '更新画像失败'
    }
  }

  return {
    profile,
    isLoading,
    error,
    radarData,
    weakPoints,
    fetchProfile,
    updateProfile
  }
})