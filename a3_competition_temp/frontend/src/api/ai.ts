const API_BASE = '/api'
const TIMEOUT_MS = 10000

function token(): string | null {
  return localStorage.getItem('token')
}

function authHeaders(): Record<string, string> {
  const t = token()
  return t ? { Authorization: `Bearer ${t}` } : {}
}

function createFetchOptions(options: RequestInit = {}): RequestInit {
  const controller = new AbortController()
  setTimeout(() => controller.abort(), TIMEOUT_MS)

  const headers: Record<string, string> = {
    ...authHeaders(),
    ...(options.headers as Record<string, string> || {})
  }
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }
  Object.keys(headers).forEach(key => {
    if (!headers[key]) delete headers[key]
  })

  return {
    ...options,
    signal: controller.signal,
    headers
  }
}

export const aiApi = {
  async emit(event: string, payload: any = {}): Promise<void> {
    try {
      const opts = createFetchOptions({
        method: 'POST',
        body: JSON.stringify({ type: event, ...payload })
      })
      await fetch(`${API_BASE}/event`, opts)
    } catch { }
  },

  async state(): Promise<any> {
    try {
      const res = await fetch(`${API_BASE}/state`, createFetchOptions())
      return await res.json()
    } catch {
      return null
    }
  },

  async traces(): Promise<any> {
    try {
      const res = await fetch(`${API_BASE}/workflow/traces`, createFetchOptions())
      return await res.json()
    } catch {
      return null
    }
  },

  async chat(studentId: string, message: string, mode = 'direct') {
    try {
      const opts = createFetchOptions({
        method: 'POST',
        body: JSON.stringify({ student_id: studentId, message, mode })
      })
      const res = await fetch(`${API_BASE}/tutoring/chat`, opts)
      return await res.json()
    } catch (e) {
      return { status: 'error', message: '请求超时或失败' }
    }
  },

  async profile(studentId: string) {
    try {
      const res = await fetch(`${API_BASE}/db/profile/${studentId}`, createFetchOptions())
      return await res.json()
    } catch (e) {
      return { status: 'error', message: '获取画像失败' }
    }
  },

  async login(username: string, password: string, role: string = 'student', education_level?: string, grade?: string) {
    try {
      const opts = createFetchOptions({
        method: 'POST',
        body: JSON.stringify({ username, password, role, education_level: education_level || null, grade: grade || null })
      })
      const res = await fetch(`${API_BASE}/auth/login`, opts)
      return await res.json()
    } catch (e) {
      return { status: 'error', message: '登录失败' }
    }
  },

  async register(username: string, email: string, password: string, role: string = 'student', education_level: string = 'high_school', grade: string = '') {
    try {
      const opts = createFetchOptions({
        method: 'POST',
        body: JSON.stringify({ username, email, password, role, education_level, grade })
      })
      const res = await fetch(`${API_BASE}/auth/register`, opts)
      return await res.json()
    } catch (e) {
      return { status: 'error', message: '注册失败' }
    }
  },

  async setEducation(studentId: string, education_level: string, grade: string = '', role: string = 'student') {
    try {
      const opts = createFetchOptions({
        method: 'POST',
        body: JSON.stringify({ student_id: studentId, education_level, grade, role })
      })
      const res = await fetch(`${API_BASE}/auth/set-education`, opts)
      return await res.json()
    } catch (e) {
      return { status: 'error', message: '设置失败' }
    }
  },

  async ragUpload(files: File[], subject = '计算机网络') {
    try {
      const formData = new FormData()
      files.forEach(file => formData.append('files', file))
      formData.append('subject', subject)
      const opts = createFetchOptions({
        method: 'POST',
        body: formData
      })
      const res = await fetch(`${API_BASE}/rag/upload`, opts)
      return await res.json()
    } catch (e) {
      return { status: 'error', message: '上传失败' }
    }
  },

  async ragQuery(query: string, topK: number = 5, subject = '计算机网络') {
    try {
      const opts = createFetchOptions({ method: 'POST' })
      const res = await fetch(`${API_BASE}/rag/query?query=${encodeURIComponent(query)}&top_k=${topK}&subject=${encodeURIComponent(subject)}`, opts)
      return await res.json()
    } catch (e) {
      return { status: 'error', message: '检索失败', results: [] }
    }
  },

  async ragStats(subject = '计算机网络') {
    try {
      const res = await fetch(`${API_BASE}/rag/stats?subject=${encodeURIComponent(subject)}`, createFetchOptions())
      return await res.json()
    } catch (e) {
      return null
    }
  },

  async ragClear() {
    try {
      const opts = createFetchOptions({ method: 'DELETE' })
      const res = await fetch(`${API_BASE}/rag/clear`, opts)
      return await res.json()
    } catch (e) {
      return { status: 'error', message: '清除失败' }
    }
  },

  async ragHealth() {
    try {
      const res = await fetch(`${API_BASE}/rag/health`, createFetchOptions())
      return await res.json()
    } catch (e) {
      return { status: 'error', message: '连接失败' }
    }
  }
}
