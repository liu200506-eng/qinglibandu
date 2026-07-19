import { defineStore } from 'pinia'

export type AIState =
  | 'idle'
  | 'focus'
  | 'thinking'
  | 'learning'
  | 'reviewing'
  | 'processing'
  | 'success'
  | 'error'

export type Emotion = 'calm' | 'focused' | 'curious' | 'confident' | 'excited' | 'tired' | 'concerned'

export interface AITrace {
  agent: string
  status: 'running' | 'completed' | 'failed'
  started_at?: string
  finished_at?: string
  summary?: string
  reasoning?: string
}

export const useAIStore = defineStore('ai', {
  state: () => ({
    state: 'idle' as AIState,
    emotion: 'calm' as Emotion,
    energy: 0.75,
    warp: false,
    traces: [] as AITrace[],
    lastSyncAt: 0
  }),

  getters: {
    statusLabel(s): string {
      const map: Record<AIState, string> = {
        idle: '就绪',
        focus: '聆听中',
        thinking: '思考中',
        learning: '学习中',
        reviewing: '复盘中',
        processing: '执行中',
        success: '完成',
        error: '异常'
      }
      return map[s.state]
    },
    emotionLabel(s): string {
      const map: Record<Emotion, string> = {
        calm: '平静',
        focused: '专注',
        curious: '好奇',
        confident: '自信',
        excited: '兴奋',
        tired: '有些累了',
        concerned: '担心'
      }
      return map[s.emotion]
    },
    emotionEmoji(s): string {
      const map: Record<Emotion, string> = {
        calm: '😌',
        focused: '🧠',
        curious: '🤔',
        confident: '😎',
        excited: '🤩',
        tired: '😴',
        concerned: '😰'
      }
      return map[s.emotion]
    },
    energyLevel(s): string {
      if (s.energy >= 0.8) return 'high'
      if (s.energy >= 0.45) return 'mid'
      return 'low'
    }
  },

  actions: {
    transitionTo(next: AIState, emotion?: Emotion) {
      this.state = next
      if (emotion) this.emotion = emotion
      if (next === 'learning') this.energy = Math.min(1, this.energy + 0.05)
      if (next === 'reviewing') this.energy = Math.max(0.1, this.energy - 0.08)
      this.lastSyncAt = Date.now()
    },

    async emit(event: string, payload: any = {}) {
      try {
        await fetch('http://localhost:8001/api/event', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ type: event, ...payload })
        })
      } catch {}
      await this.sync()
    },

    async sync() {
      try {
        const res = await fetch('http://localhost:8001/api/state')
        const data = await res.json()
        if (data.state) this.state = data.state
        if (data.emotion) this.emotion = data.emotion
        if (typeof data.energy === 'number') this.energy = data.energy
        if (Array.isArray(data.traces)) this.traces = data.traces
        this.lastSyncAt = Date.now()
      } catch {}
    },

    async getTraces() {
      try {
        const res = await fetch('http://localhost:8001/api/workflow/traces')
        const data = await res.json()
        this.traces = Array.isArray(data.traces) ? data.traces : []
      } catch {}
    }
  }
})
