export interface KnowledgeState {
  node_id: string
  name: string
  mastery: number
  stability: number
  error_count: number
  correct_count: number
}

export interface LearningProfile {
  student_id: string
  knowledge_mastery: number
  learning_stability: number
  response_speed: number
  error_pattern_score: number
  cognitive_preference: string
  self_driven_score: number
  transfer_ability: number
  emotional_state: number
  knowledge_states: Record<string, KnowledgeState>
  error_distribution: Record<string, number>
  grade: string
  subject: string
  learning_goal: string
}

export interface LearningTask {
  task_id: string
  title: string
  task_type: string
  knowledge_points: string[]
  difficulty: number
  estimated_minutes: number
  expected_gain: number
  status: string
  priority: number
  explanation: string
}

export interface ResourcePack {
  pack_id: string
  lecture_text: string
  exercises: { question: string; options?: string[]; answer: string; difficulty: string }[]
  mind_map: Record<string, unknown> | null
  flash_cards: { front: string; back: string; difficulty: string }[]
  quality_score: number
}

export interface DiagnosisResult {
  summary: string
  weak_areas: string[]
  primary_error_cause: string
  confidence: number
  suggestions: string[]
}

export interface AgentTrace {
  agent_name: string
  status: string
  reasoning: string
}