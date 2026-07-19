<template>
  <div class="tutoring-view">
    <el-row :gutter="20">
      <el-col :xs="24" :sm="24" :md="16" :lg="17">
        <el-card class="chat-card">
          <template #header>
            <div class="chat-header">
              <div class="header-left">
                <el-icon size="24" color="#0d9488"><ChatDotRound /></el-icon>
                <span class="chat-title">智能答疑助手</span>
                <el-tag :type="currentMode === 'socratic' ? 'success' : 'primary'" size="small">
                  {{ currentMode === 'socratic' ? '苏格拉底模式' : '直接讲解模式' }}
                </el-tag>
              </div>
              <div class="header-right">
                <el-button size="small" @click="clearHistory">
                  <el-icon><Delete /></el-icon>清空对话
                </el-button>
              </div>
            </div>
          </template>

          <div class="chat-messages" ref="messagesContainer">
            <div v-if="messages.length === 0" class="welcome-container">
              <div class="welcome-icon">🤖</div>
              <h3>你好，我是智能学习助手</h3>
              <p>我可以帮你解答学习问题、分析知识点、制定学习计划</p>
              <div class="quick-questions">
                <el-tag v-for="q in quickQuestions" :key="q" @click="askQuickQuestion(q)" class="quick-tag">
                  {{ q }}
                </el-tag>
              </div>
              <div class="welcome-modes">
                <el-tag type="info" effect="plain">💬 文字提问</el-tag>
                <el-tag type="warning" effect="plain">🎤 语音输入</el-tag>
                <el-tag type="success" effect="plain">🖼️ 图片上传</el-tag>
                <el-tag type="danger" effect="plain">📎 文件上传</el-tag>
              </div>
            </div>

            <div
              v-for="(msg, index) in messages"
              :key="index"
              class="message-item"
              :class="msg.role"
            >
              <div class="message-avatar">{{ msg.role === 'user' ? '👤' : '🎓' }}</div>
              <div class="message-content">
                <div class="message-bubble" v-html="formatMessage(msg.content)"></div>
                <div class="message-actions" v-if="msg.role === 'assistant'">
                  <el-button
                    size="small"
                    :icon="msg.isPlaying ? VideoPause : VideoPlay"
                    :type="msg.isPlaying ? 'primary' : 'default'"
                    circle
                    @click="toggleTTS(msg)"
                  />
                </div>
                <div class="message-attachments" v-if="msg.attachments && msg.attachments.length">
                  <div v-for="(att, ai) in msg.attachments" :key="ai" class="att-item">
                    <el-icon v-if="att.type === 'image'"><Picture /></el-icon>
                    <el-icon v-else-if="att.type === 'audio'"><Microphone /></el-icon>
                    <el-icon v-else><Document /></el-icon>
                    <span>{{ att.name }}</span>
                  </div>
                </div>
                <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
              </div>
            </div>

            <div v-if="isTyping" class="typing-indicator">
              <div class="typing-avatar">🎓</div>
              <div class="typing-content">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
              </div>
            </div>
          </div>

          <div class="chat-input-container">
            <div class="mode-switch-row">
              <el-radio-group v-model="inputKind" size="default">
                <el-radio-button label="text"><el-icon><EditPen /></el-icon> 文字</el-radio-button>
                <el-radio-button label="voice"><el-icon><Microphone /></el-icon> 语音</el-radio-button>
                <el-radio-button label="image"><el-icon><Picture /></el-icon> 图片</el-radio-button>
                <el-radio-button label="file"><el-icon><Document /></el-icon> 文件</el-radio-button>
              </el-radio-group>

              <el-radio-group v-model="currentMode" size="default">
                <el-radio-button label="direct"><el-icon><Reading /></el-icon> 讲解</el-radio-button>
                <el-radio-button label="socratic"><el-icon><QuestionFilled /></el-icon> 引导</el-radio-button>
              </el-radio-group>
            </div>

            <div class="input-area">
              <el-input
                v-if="inputKind === 'text'"
                v-model="inputMessage"
                type="textarea"
                :rows="2"
                placeholder="输入你的问题... (Enter发送 / Ctrl+Enter换行)"
                resize="none"
                @keydown.enter="handleEnter"
                @keydown.enter.ctrl="handleEnterNewline"
              />

              <div v-else-if="inputKind === 'voice'" class="voice-panel">
                <div class="voice-record" :class="{ recording: isRecording }">
                  <el-button
                    v-if="!isRecording"
                    type="success"
                    round
                    size="large"
                    @click="toggleRecord"
                  >
                    <el-icon><Microphone /></el-icon>
                    🎤 开始录音
                  </el-button>
                  <el-button
                    v-if="isRecording"
                    type="danger"
                    round
                    size="large"
                    @click="toggleRecord"
                  >
                    <el-icon><VideoPause /></el-icon>
                    录音中 {{ recordSeconds }}s · 点击停止
                  </el-button>
                  <div class="voice-hint">
                    <span v-if="!isRecording">💡 点击开始，对着麦克风说话，说完再点一次停止（会自动识别成文字）</span>
                    <span v-else>🟠 正在录音…请正常说话，不要提前停止</span>
                  </div>
                </div>
                <el-input
                  v-model="voiceText"
                  type="textarea"
                  :rows="2"
                  placeholder="识别结果会自动填入，可修改后发送"
                  resize="none"
                />
              </div>

              <div v-else-if="inputKind === 'image'" class="media-panel">
                <div v-if="!imageFile" class="upload-box" @click="triggerImageUpload" @dragover.prevent @drop.prevent="onImageDrop">
                  <el-icon size="40" color="#909399"><Picture /></el-icon>
                  <div class="upload-label">点击或拖拽上传图片（拍照/截图均可）</div>
                  <div class="upload-tip">支持 JPG / PNG / WEBP · 建议 ≤5MB</div>
                </div>
                <div v-else class="media-preview">
                  <img :src="imagePreview" class="preview-img" />
                  <div class="preview-info">
                    <div>🖼️ {{ imageFile.name }} · {{ (imageFile.size / 1024).toFixed(1) }} KB</div>
                    <el-button size="small" type="danger" plain @click="clearImage">重新选择</el-button>
                  </div>
                </div>
                <el-input
                  v-model="imagePrompt"
                  type="textarea"
                  :rows="1"
                  placeholder="（可选）针对这张图你想问什么？例如：第2题我哪一步错了？"
                  resize="none"
                />
              </div>

              <div v-else-if="inputKind === 'file'" class="media-panel">
                <div v-if="!fileFile" class="upload-box" @click="triggerFileUpload" @dragover.prevent @drop.prevent="onFileDrop">
                  <el-icon size="40" color="#909399"><Document /></el-icon>
                  <div class="upload-label">点击或拖拽上传学习资料</div>
                  <div class="upload-tip">支持 PDF / DOCX / TXT / MD / 代码 · 建议 ≤10MB</div>
                </div>
                <div v-else class="media-preview">
                  <div class="file-meta">
                    <el-icon :size="32" :color="fileIconColor"><component :is="fileIconComp" /></el-icon>
                    <div>
                      <div class="file-name">{{ fileFile.name }}</div>
                      <div class="file-size">{{ (fileFile.size / 1024).toFixed(1) }} KB</div>
                    </div>
                    <el-button size="small" type="danger" plain @click="clearFile">移除</el-button>
                  </div>
                </div>
                <el-input
                  v-model="filePrompt"
                  type="textarea"
                  :rows="1"
                  placeholder="（可选）想让我重点分析什么？例如：总结考点 / 讲第3章"
                  resize="none"
                />
              </div>

              <input type="file" ref="imageInput" accept="image/*" hidden @change="onImageSelect" />
              <input type="file" ref="fileInput" accept=".pdf,.doc,.docx,.txt,.md,.py,.js,.ts,.java,.c,.cpp,.h,.go,.rs,.html,.css,.json,.xml,.yaml,.yml,.csv" hidden @change="onFileSelect" />
            </div>

            <div class="bottom-row">
              <div class="attachments-row" v-if="hasAttachment">
                <div class="pill" v-if="inputKind === 'voice' && voiceText">🎤 已识别「{{ (voiceText.length > 18 ? voiceText.slice(0,18)+'…' : voiceText) }}」</div>
                <div class="pill" v-if="inputKind === 'image' && imageFile">🖼️ {{ imageFile.name }}</div>
                <div class="pill" v-if="inputKind === 'file' && fileFile">📎 {{ fileFile.name }}</div>
              </div>
              <div class="send-actions">
                <el-tooltip content="清空对话" placement="top">
                  <el-button circle @click="clearHistory"><el-icon><Delete /></el-icon></el-button>
                </el-tooltip>
                <el-button
                  type="primary"
                  round
                  class="send-btn"
                  :loading="isTyping || uploading"
                  :disabled="!canSend"
                  @click="sendMessage"
                >
                  <el-icon><Promotion /></el-icon>发送
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="24" :md="8" :lg="7">
        <DigitalHuman
          :mode="currentMode"
          :has-audio="true"
          style="margin-bottom:16px"
        />

        <AIStatePanel
          :learning-state="aiState.learning_state"
          :strategy-mode="aiState.strategy_mode"
          :tutoring-mode="aiState.tutoring_mode || currentMode"
          :mode-label="aiState.mode_label"
          :agent-traces="aiState.agent_traces"
          :decision-summary="aiState.decision_summary"
          v-model:visible="aiPanelVisible"
          style="margin-bottom:16px"
        />

        <el-card class="emotion-card">
          <template #header>
            <div class="card-header"><el-icon><Sunny /></el-icon><span>情绪感知</span></div>
          </template>
          <div v-if="emotionalFeedback" class="emotion-content">
            <div class="emotion-icon-large">{{ getEmotionEmoji() }}</div>
            <div class="emotion-description">{{ emotionalFeedback }}</div>
            <el-progress :percentage="emotionScore" :status="getEmotionProgressType()" :stroke-width="10" />
            <div class="emotion-tips" v-if="emotionTips">
              <el-icon><InfoFilled /></el-icon>{{ emotionTips }}
            </div>
          </div>
          <div v-else class="emotion-placeholder">
            <el-icon size="48" color="#ddd"><Sunny /></el-icon>
            <p>开始对话后，我会感知你的情绪状态</p>
          </div>
        </el-card>

        <el-card class="tips-card">
          <template #header>
            <div class="card-header"><el-icon><Opportunity /></el-icon><span>学习技巧</span></div>
          </template>
          <div class="tips-list">
            <div v-for="tip in learningTips" :key="tip.title" class="tip-item">
              <div class="tip-icon">{{ tip.icon }}</div>
              <div class="tip-content">
                <div class="tip-title">{{ tip.title }}</div>
                <div class="tip-desc">{{ tip.desc }}</div>
              </div>
            </div>
          </div>
        </el-card>

        <el-card class="history-card">
          <template #header>
            <div class="card-header"><el-icon><Clock /></el-icon><span>最近对话</span></div>
          </template>
          <div v-if="historySessions.length" class="history-list">
            <div v-for="session in historySessions" :key="session.id" class="history-item" @click="loadSession(session)">
              <div class="history-content">{{ session.preview }}</div>
              <div class="history-time">{{ session.time }}</div>
            </div>
          </div>
          <div v-else class="history-placeholder"><p>暂无历史对话</p></div>
        </el-card>
      </el-col>
    </el-row>

    <div class="ai-panel-toggle-bar" @click="toggleAiPanel">
      🔍 查看AI决策
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onBeforeUnmount, computed, watch, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import AIStatePanel from '@/core/AIStatePanel.vue'
import DigitalHuman from '@/components/DigitalHuman.vue'
import {
  ChatDotRound, Delete, Reading, QuestionFilled, Promotion,
  Sunny, Opportunity, Clock, InfoFilled,
  Microphone, VideoPause, Picture, Document, EditPen, VideoPlay
} from '@element-plus/icons-vue'

interface Attachment { type: 'image' | 'audio' | 'file'; name: string; url?: string }
interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  attachments?: Attachment[]
  isPlaying?: boolean
}

const messagesContainer = ref<HTMLElement>()
const inputMessage = ref('')
const currentMode = ref<'direct' | 'socratic'>('direct')
const isTyping = ref(false)
const messages = ref<Message[]>([])
const emotionalFeedback = ref('')
const emotionScore = ref(75)
const emotionTips = ref('')

const inputKind = ref<'text' | 'voice' | 'image' | 'file'>('text')
const uploading = ref(false)

const imageInput = ref<HTMLInputElement>()
const fileInput = ref<HTMLInputElement>()
const imageFile = ref<File | null>(null)
const fileFile = ref<File | null>(null)
const imagePreview = ref('')
const imagePrompt = ref('')
const filePrompt = ref('')

const isRecording = ref(false)
const recordSeconds = ref(0)
const voiceText = ref('')
let recordTimer: number | null = null
let mediaRecorder: MediaRecorder | null = null
let recordedChunks: Blob[] = []
let audioStream: MediaStream | null = null
let webSpeechRecognition: any = null

let ttsAudio: HTMLAudioElement | null = null

const aiPanelVisible = ref(true)
const aiState = reactive({
  learning_state: null as any,
  strategy_mode: '' as string,
  tutoring_mode: '' as string,
  mode_label: '' as string,
  agent_traces: [] as Array<{ agent_name: string; status?: string }>,
  decision_summary: '' as string
})

async function toggleRecord() {
  if (!isRecording.value) {
    if (!navigator.mediaDevices?.getUserMedia) {
      ElMessage.error('当前浏览器不支持录音，请使用 Chrome / Edge');
      return
    }
    try {
      audioStream = await navigator.mediaDevices.getUserMedia({ audio: true })
      isRecording.value = true
      recordSeconds.value = 0
      voiceText.value = ''
      recordTimer = window.setInterval(() => { recordSeconds.value++ }, 1000)

      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
      if (SpeechRecognition) {
        webSpeechRecognition = new SpeechRecognition()
        webSpeechRecognition.continuous = true
        webSpeechRecognition.interimResults = true
        webSpeechRecognition.lang = 'zh-CN'

        webSpeechRecognition.onresult = (event: any) => {
          let interimTranscript = ''
          let finalTranscript = ''
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              finalTranscript += event.results[i][0].transcript
            } else {
              interimTranscript += event.results[i][0].transcript
            }
          }
          voiceText.value = finalTranscript + interimTranscript
        }

        webSpeechRecognition.onerror = (event: any) => {
          if (event.error !== 'no-speech' && event.error !== 'aborted') {
            console.warn('Web Speech API error:', event.error)
          }
        }

        webSpeechRecognition.onend = () => {
          if (isRecording.value) {
            try {
              webSpeechRecognition.start()
            } catch {}
          }
        }

        webSpeechRecognition.start()
        ElMessage.info('🎤 已开启实时语音识别，请直接说话')
      } else {
        let mime = ''
        const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4']
        for (const t of types) {
          if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported?.(t)) { mime = t; break }
        }
        mediaRecorder = mime ? new MediaRecorder(audioStream, { mimeType: mime }) : new MediaRecorder(audioStream)
        recordedChunks = []
        mediaRecorder.ondataavailable = (ev) => {
          if (ev.data && ev.data.size > 0) recordedChunks.push(ev.data)
        }
        mediaRecorder.onerror = (e: any) => {
          ElMessage.warning('录音出错：' + (e?.error || e))
        }
        mediaRecorder.onstop = async () => {
          if (recordTimer) { clearInterval(recordTimer); recordTimer = null }
          isRecording.value = false
          audioStream?.getTracks().forEach(t => t.stop())
          audioStream = null
          const blob = new Blob(recordedChunks, { type: mediaRecorder!.mimeType || 'audio/webm' })
          if (blob.size < 300) {
            ElMessage.warning('录音太短，请多说几句再停止')
            return
          }
          ElMessage.info('🎤 录音完成（' + (blob.size/1024).toFixed(1) + 'KB），正在识别…')
          await doTranscribe(blob)
        }
        mediaRecorder.start(1000)
        ElMessage.info('🎤 开始录音，请对着麦克风说话')
      }
    } catch (err: any) {
      ElMessage.error('无法打开麦克风：' + (err?.message || err) + '\n请检查浏览器麦克风权限')
    }
  } else {
    isRecording.value = false
    if (recordTimer) { clearInterval(recordTimer); recordTimer = null }

    if (webSpeechRecognition) {
      try { webSpeechRecognition.stop() } catch {}
      webSpeechRecognition = null
    }

    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      try { mediaRecorder.stop() } catch {}
    }

    audioStream?.getTracks().forEach(t => t.stop())
    audioStream = null

    if (voiceText.value.trim()) {
      ElMessage.success('🎤 语音识别完成：' + voiceText.value.slice(0, 30) + (voiceText.value.length > 30 ? '…' : ''))
    } else if (!webSpeechRecognition) {
      ElMessage.warning('没有识别到语音内容，请重试或直接打字')
    }
  }
}

const hasAttachment = computed(() => {
  if (inputKind.value === 'voice') return !!voiceText.value.trim()
  if (inputKind.value === 'image') return !!imageFile.value
  if (inputKind.value === 'file') return !!fileFile.value
  return !!inputMessage.value.trim()
})

const canSend = computed(() => {
  if (isTyping.value) return false
  if (inputKind.value === 'text') return !!inputMessage.value.trim()
  if (inputKind.value === 'voice') return !!voiceText.value.trim()
  if (inputKind.value === 'image') return !!imageFile.value
  if (inputKind.value === 'file') return !!fileFile.value
  return false
})

const quickQuestions = [
  '如何提高数学成绩？',
  '一元二次方程怎么解？',
  '帮我制定学习计划',
  '英语语法怎么学？'
]

const learningTips = [
  { icon: '💡', title: '分解问题', desc: '把复杂问题拆成小问题' },
  { icon: '📝', title: '主动思考', desc: '先自己尝试，再寻求帮助' },
  { icon: '🔄', title: '重复练习', desc: '温故知新，加深记忆' },
  { icon: '🎯', title: '明确目标', desc: '知道学什么，为什么学' }
]

const historySessions = ref([
  { id: 1, preview: '关于函数的问题', time: '今天 10:30' },
  { id: 2, preview: '数学解题技巧', time: '昨天 15:20' },
  { id: 3, preview: '学习方法咨询', time: '3天前' }
])

const fileIconComp = computed(() => {
  const n = (fileFile.value?.name || '').toLowerCase()
  if (n.endsWith('.pdf')) return Document
  if (n.endsWith('.docx') || n.endsWith('.doc')) return Document
  return Document
})
const fileIconColor = computed(() => {
  const n = (fileFile.value?.name || '').toLowerCase()
  if (n.endsWith('.pdf')) return '#ef4444'
  if (n.endsWith('.docx') || n.endsWith('.doc')) return '#2b579a'
  if (n.endsWith('.md')) return '#083fa1'
  return '#10b981'
})

function handleEnter(e: KeyboardEvent) { e.preventDefault(); sendMessage() }
function handleEnterNewline(_e: KeyboardEvent) {}

function triggerImageUpload() { imageInput.value?.click() }
function triggerFileUpload() { fileInput.value?.click() }

function onImageSelect(e: Event) {
  const inp = e.target as HTMLInputElement
  if (!inp.files?.length) return
  const f = inp.files[0]
  if (f.size > 8 * 1024 * 1024) { ElMessage.warning('图片建议小于 8MB，过大可能识别失败'); return }
  imageFile.value = f
  const url = URL.createObjectURL(f)
  imagePreview.value = url
}

function onFileSelect(e: Event) {
  const inp = e.target as HTMLInputElement
  if (!inp.files?.length) return
  const f = inp.files[0]
  if (f.size > 20 * 1024 * 1024) { ElMessage.warning('文件建议小于 20MB'); return }
  fileFile.value = f
}

function onImageDrop(e: DragEvent) {
  const f = e.dataTransfer?.files?.[0]
  if (!f || !f.type.startsWith('image/')) { ElMessage.warning('请拖拽图片文件'); return }
  imageFile.value = f
  imagePreview.value = URL.createObjectURL(f)
}
function onFileDrop(e: DragEvent) {
  const f = e.dataTransfer?.files?.[0]
  if (!f) { ElMessage.warning('请拖拽文件'); return }
  fileFile.value = f
}

function clearImage() { imageFile.value = null; imagePreview.value = ''; imagePrompt.value = '' }
function clearFile() { fileFile.value = null; filePrompt.value = '' }

async function doTranscribe(blob: Blob) {
  uploading.value = true
  const ctrl = new AbortController()
  const t = setTimeout(() => ctrl.abort(), 45000)
  try {
    const fd = new FormData()
    fd.append('audio_file', blob, 'voice.webm')
    const r = await fetch('/api/voice/transcribe', { method: 'POST', body: fd, signal: ctrl.signal })
    if (!r.ok) {
      ElMessage.error('识别请求失败（HTTP ' + r.status + '），可直接打字提问')
      voiceText.value = ''
      return
    }
    const d = await r.json()
    if (d.status === 'success' && d.text && d.text.trim()) {
      voiceText.value = d.text.trim()
      ElMessage.success('🎤 已识别：' + voiceText.value.slice(0, 30) + (voiceText.value.length > 30 ? '…' : ''))
    } else {
      ElMessage.warning('识别结果为空（可能没录到声音），请重录或手动打字')
      voiceText.value = ''
    }
  } catch (e: any) {
    ElMessage.error('语音识别失败：' + (e?.name === 'AbortError' ? '超时' : (e?.message || '网络异常')) + '。可手动输入问题')
    voiceText.value = ''
  } finally {
    clearTimeout(t)
    uploading.value = false
  }
}

async function toggleTTS(msg: Message) {
  if (msg.isPlaying) {
    if (ttsAudio) {
      ttsAudio.pause()
      ttsAudio = null
    }
    msg.isPlaying = false
    messages.value = [...messages.value]
    return
  }

  msg.isPlaying = true
  messages.value = [...messages.value]

  try {
    const content = msg.content.replace(/[*#`]/g, '').replace(/\n+/g, ' ')
    const fd = new FormData()
    fd.append('text', content)
    fd.append('voice', 'default')

    const r = await fetch('/api/voice/synthesize', { method: 'POST', body: fd })
    if (!r.ok) {
      ElMessage.error('语音合成失败')
      msg.isPlaying = false
      messages.value = [...messages.value]
      return
    }

    const blob = await r.blob()
    const audioUrl = URL.createObjectURL(blob)

    ttsAudio = new Audio(audioUrl)
    ttsAudio.onended = () => {
      msg.isPlaying = false
      messages.value = [...messages.value]
      if (ttsAudio) {
        URL.revokeObjectURL(ttsAudio.src)
        ttsAudio = null
      }
    }
    ttsAudio.onerror = () => {
      msg.isPlaying = false
      messages.value = [...messages.value]
      ElMessage.warning('音频播放失败')
    }

    await ttsAudio.play()
  } catch (e: any) {
    msg.isPlaying = false
    messages.value = [...messages.value]
    ElMessage.error('语音播放失败：' + (e?.message || '未知错误'))
  }
}

function attachAttachmentsToUserMsg(msg: Message) {
  const atts: Attachment[] = []
  if (inputKind.value === 'voice' && voiceText.value.trim()) {
    atts.push({ type: 'audio', name: '语音识别' })
  }
  if (inputKind.value === 'image' && imageFile.value) {
    atts.push({ type: 'image', name: imageFile.value.name, url: imagePreview.value })
  }
  if (inputKind.value === 'file' && fileFile.value) {
    atts.push({ type: 'file', name: fileFile.value.name })
  }
  msg.attachments = atts
}

async function sendMessage() {
  if (!canSend.value || isTyping.value) return

  let userContent = ''
  if (inputKind.value === 'text') {
    userContent = inputMessage.value.trim()
  } else if (inputKind.value === 'voice') {
    userContent = voiceText.value.trim()
  } else if (inputKind.value === 'image') {
    userContent = (imagePrompt.value || '请帮我分析这张图片的内容，并解答相关学习问题。').trim()
  } else if (inputKind.value === 'file') {
    userContent = (filePrompt.value || '请帮我分析这份文件，提取核心知识点并讲解。').trim()
  }

  if (!userContent) {
    if (inputKind.value === 'voice') {
      ElMessage.warning('语音识别结果为空，请对着麦克风说清楚一点，或直接改用文字提问');
    } else if (inputKind.value === 'text') {
      ElMessage.info('请输入你的问题');
    } else if (inputKind.value === 'image') {
      ElMessage.info('请先上传一张图片');
    } else if (inputKind.value === 'file') {
      ElMessage.info('请先上传一个文件');
    }
    return
  }

  // 上传文件必须在清空选择状态前保存引用，否则请求会错误降级为普通文本答疑。
  const pendingImage = imageFile.value
  const pendingFile = fileFile.value
  const requestKind = inputKind.value
  const userMsg: Message = { role: 'user', content: userContent, timestamp: new Date() }
  attachAttachmentsToUserMsg(userMsg)
  messages.value.push(userMsg)

  if (inputKind.value === 'text') inputMessage.value = ''
  else if (inputKind.value === 'voice') voiceText.value = ''
  else if (inputKind.value === 'image') { imagePrompt.value = ''; imageFile.value = null; imagePreview.value = '' }
  else if (inputKind.value === 'file') { filePrompt.value = ''; fileFile.value = null }

  await nextTick()
  scrollToBottom()
  isTyping.value = true

  const studentId = localStorage.getItem('student_id') || '1'
  try {
    let data: any
    if (requestKind === 'image' && pendingImage) {
      const fd = new FormData()
      fd.append('file', pendingImage)
      fd.append('student_id', studentId)
      fd.append('mode', currentMode.value)
      fd.append('extra_prompt', userContent)
      uploading.value = true
      const r = await fetch('/api/multimodal/analyze', { method: 'POST', body: fd })
      data = await r.json()
      uploading.value = false
    } else if (requestKind === 'file' && pendingFile) {
      const fd = new FormData()
      fd.append('file', pendingFile)
      fd.append('student_id', studentId)
      fd.append('mode', currentMode.value)
      fd.append('extra_prompt', userContent)
      uploading.value = true
      const r = await fetch('/api/multimodal/analyze', { method: 'POST', body: fd })
      data = await r.json()
      uploading.value = false
    } else if (requestKind === 'voice') {
      const r = await fetch('/api/multimodal/voice-chat' +
        `?student_id=${encodeURIComponent(studentId)}&mode=${encodeURIComponent(currentMode.value)}&text=${encodeURIComponent(userContent)}`,
        { method: 'POST' })
      data = await r.json()
    } else {
      const r = await fetch('/api/tutoring/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: studentId, message: userContent, mode: currentMode.value })
      })
      if (!r.ok) throw new Error(`AI答疑接口异常：HTTP ${r.status}`)
      data = await r.json()
    }

    isTyping.value = false

    if (data.learning_state !== undefined) aiState.learning_state = data.learning_state
    if (data.strategy_mode !== undefined) aiState.strategy_mode = data.strategy_mode
    if (data.tutoring_mode !== undefined) aiState.tutoring_mode = data.tutoring_mode
    if (data.mode_label !== undefined) aiState.mode_label = data.mode_label
    if (data.agent_traces !== undefined) aiState.agent_traces = data.agent_traces
    if (data.decision_summary !== undefined) aiState.decision_summary = data.decision_summary

    if (data.status === 'success' && data.response) {
      messages.value.push({ role: 'assistant', content: data.response, timestamp: new Date() })
      if (data.emotional_feedback) {
        emotionalFeedback.value = data.emotional_feedback
        emotionTips.value = data.emotional_tip || ''
      }
      if (data.recognized_text && inputKind.value === 'voice') {
        ElMessage.success('🎤 语音识别成功，已获AI解答')
      }
    } else {
      messages.value.push({ role: 'assistant', content: getFallbackResponse(userContent).content, timestamp: new Date() })
    }
  } catch (e) {
    isTyping.value = false
    uploading.value = false
    messages.value.push({ role: 'assistant', content: '网络错误，请检查网络连接后重试。', timestamp: new Date() })
  }
  await nextTick()
  scrollToBottom()
}

function scrollToBottom() {
  if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
}

function getFallbackResponse(question: string): { content: string; emotion: string; tip: string } {
  const q = question.toLowerCase()
  if (q.includes('数学') || q.includes('计算') || q.includes('方程') || q.includes('函数')) {
    return { content: '数学学习建议：\n**1. 夯实基础** 熟练掌握概念和公式\n**2. 多做练习** 整理错题本分析错因\n**3. 掌握技巧** 学会分析条件与思路', emotion: '你正在积极思考数学问题，这很好！', tip: '建议每天坚持做5道数学题，逐步提高' }
  }
  if (q.includes('英语') || q.includes('语法') || q.includes('单词')) {
    return { content: '英语学习建议：\n**1. 词汇** 每天20-30个，联想记忆\n**2. 语法** 掌握基本句型，多读多写\n**3. 听说** 每天听英语音频', emotion: '你正在积极学习英语，保持好状态！', tip: '建议每天早起背诵单词，效果更好' }
  }
  return { content: '好的，我来帮你分析这个问题。\n\n为了更准确地帮你，可以告诉我：\n- 这是什么学科的问题？\n- 是概念理解还是具体题目？\n\n你也可以切换到「苏格拉底引导」模式，我会一步步提问帮你自己找到答案！', emotion: '你正在积极提问，这很好！', tip: '描述问题越具体，得到的帮助越大' }
}

function askQuickQuestion(question: string) { inputMessage.value = question; sendMessage() }

function clearHistory() {
  messages.value = []
  emotionalFeedback.value = ''
  ElMessage.success('对话已清空')
}

function loadSession(session: any) { ElMessage.info(`加载对话：${session.preview}`) }

function toggleAiPanel() { aiPanelVisible.value = !aiPanelVisible.value }

function formatMessage(content: string): string {
  return (content || '')
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
    .replace(/- /g, '&nbsp;&nbsp;&nbsp;&nbsp;• ')
}

function formatTime(date: Date): string {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
}

function getEmotionEmoji(): string {
  const s = emotionScore.value
  if (s >= 80) return '😊'
  if (s >= 60) return '🙂'
  if (s >= 40) return '🤔'
  if (s >= 20) return '😟'
  return '😔'
}
function getEmotionProgressType(): string {
  const s = emotionScore.value
  if (s >= 70) return 'success'
  if (s >= 40) return 'warning'
  return 'exception'
}

onMounted(() => {
  messages.value.push({
    role: 'assistant',
    content: '你好！我是你的智能学习助手 🎓\n\n📣 我支持 4 种提问方式：\n- 💬 **文字**：直接输入问题\n- 🎤 **语音**：录音说话，自动AI转文字\n- 🖼️ **图片**：上传题目截图自动OCR\n- 📎 **文件**：PDF/DOCX/TXT 一键解析\n\n请告诉我你有什么学习疑问？',
    timestamp: new Date()
  })
})

onBeforeUnmount(() => {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') { try { mediaRecorder.stop() } catch {} }
  if (webSpeechRecognition) { try { webSpeechRecognition.stop() } catch {} }
  audioStream?.getTracks().forEach(t => t.stop())
  if (recordTimer) clearInterval(recordTimer)
})

watch(inputKind, () => {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') { try { mediaRecorder.stop() } catch {} }
  if (webSpeechRecognition) { try { webSpeechRecognition.stop() } catch {} }
  audioStream?.getTracks().forEach(t => t.stop())
  if (recordTimer) { clearInterval(recordTimer); recordTimer = null }
  isRecording.value = false
})
</script>

<style scoped>
.tutoring-view { padding: 0; }

.chat-card { height: calc(100vh - 140px); display: flex; flex-direction: column; }

.chat-header { display: flex; justify-content: space-between; align-items: center; }
.header-left { display: flex; align-items: center; gap: 12px; }
.chat-title { font-size: 18px; font-weight: bold; }

.chat-messages { flex: 1; overflow-y: auto; padding: 20px; background: #f5f7fa; }

.welcome-container { text-align: center; padding: 40px 20px; }
.welcome-icon { font-size: 64px; margin-bottom: 20px; }
.welcome-container h3 { margin: 0 0 12px 0; color: #333; }
.welcome-container p { color: #999; margin-bottom: 20px; }
.quick-questions { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; margin-bottom: 16px; }
.quick-tag { cursor: pointer; padding: 8px 16px; }
.quick-tag:hover { background: #0d9488; color: white; }
.welcome-modes { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }

.message-item { display: flex; margin-bottom: 18px; }
.message-item.user { flex-direction: row-reverse; }
.message-avatar { width: 40px; height: 40px; border-radius: 50%; background: white; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.message-content { max-width: 75%; margin: 0 12px; }
.message-bubble { padding: 14px 18px; border-radius: 16px; line-height: 1.7; font-size: 14px; }
.message-actions { display: flex; justify-content: flex-end; margin-top: 4px; }
.message-actions button { opacity: 0; transition: opacity 0.2s; }
.message-item:hover .message-actions button { opacity: 1; }
.message-attachments { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
.att-item { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; background: rgba(13,148,136,.08); color: #0d9488; padding: 4px 10px; border-radius: 14px; }
.user .message-bubble { background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%); color: white; border-bottom-right-radius: 4px; }
.assistant .message-bubble { background: white; color: #333; border-bottom-left-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.message-bubble h1 { font-size: 18px; font-weight: 700; color: #0d9488; margin: 12px 0 8px; padding-bottom: 4px; border-bottom: 2px solid #0d9488; }
.message-bubble h2 { font-size: 16px; font-weight: 600; color: #0f766e; margin: 10px 0 6px; padding-left: 8px; border-left: 3px solid #0d9488; }
.message-bubble h3 { font-size: 14px; font-weight: 600; color: #0d9488; margin: 8px 0 4px; }
.message-time { font-size: 11px; color: #999; margin-top: 6px; }
.user .message-time { text-align: right; }

.typing-indicator { display: flex; align-items: center; gap: 12px; }
.typing-avatar { width: 40px; height: 40px; border-radius: 50%; background: white; display: flex; align-items: center; justify-content: center; font-size: 20px; }
.typing-content { background: white; padding: 14px 20px; border-radius: 16px; border-bottom-left-radius: 4px; display: flex; gap: 4px; }
.typing-dot { width: 8px; height: 8px; background: #0d9488; border-radius: 50%; animation: typing 1.4s infinite ease-in-out; }
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.chat-input-container { padding: 12px 16px; background: white; border-top: 1px solid #eee; display: flex; flex-direction: column; gap: 10px; }

.mode-switch-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }

.input-area { min-height: 86px; }

.voice-panel { display: flex; flex-direction: column; gap: 10px; }
.voice-record { display: flex; align-items: center; gap: 16px; }
.voice-record.recording button { animation: pulse 1s infinite; }
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(245,101,101,0.7); }
  50% { box-shadow: 0 0 0 12px rgba(245,101,101,0); }
}
.voice-hint { font-size: 12px; color: #909399; }
.voice-live { padding: 8px 12px; background: #f0f9ff; border: 1px dashed #91caff; border-radius: 8px; margin-top: 4px; }
.voice-interim { font-size: 13px; color: #409eff; font-style: italic; }
.voice-final { font-size: 14px; color: #303133; margin-top: 4px; font-weight: 500; }
.blink { display: inline-block; animation: blink 1s infinite; color: #f56c6c; margin-left: 2px; }
@keyframes blink { 0%,50% { opacity: 1 } 50.01%,100% { opacity: 0 } }

.media-panel { display: flex; flex-direction: column; gap: 8px; }
.upload-box { border: 2px dashed #c0c4cc; border-radius: 12px; padding: 22px; text-align: center; cursor: pointer; background: #fafbfc; transition: all 0.2s; }
.upload-box:hover { border-color: #0d9488; background: #f0fdfa; }
.upload-label { margin-top: 8px; font-size: 14px; color: #303133; }
.upload-tip { margin-top: 4px; font-size: 12px; color: #909399; }
.media-preview { display: flex; flex-direction: column; gap: 8px; }
.preview-img { max-width: 100%; max-height: 260px; border-radius: 10px; border: 1px solid #eee; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }
.preview-info { display: flex; justify-content: space-between; align-items: center; font-size: 13px; color: #606266; }
.file-meta { display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: #f6f7fb; border-radius: 10px; border: 1px solid #ebedf0; }
.file-name { font-weight: 600; font-size: 14px; color: #303133; }
.file-size { font-size: 12px; color: #909399; }

.bottom-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.attachments-row { display: flex; flex-wrap: wrap; gap: 8px; }
.pill { display: inline-flex; align-items: center; background: #f0fdfa; color: #0d9488; padding: 4px 12px; border-radius: 16px; font-size: 12px; border: 1px solid #ccfbf1; }
.send-actions { display: flex; gap: 8px; align-items: center; }
.send-btn { padding: 0 22px; background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%); border: none; }

.card-header { display: flex; align-items: center; gap: 8px; font-weight: bold; }

.emotion-card, .tips-card, .history-card { margin-bottom: 16px; }
.emotion-content { text-align: center; padding: 16px 0; }
.emotion-icon-large { font-size: 64px; margin-bottom: 12px; }
.emotion-description { color: #666; font-size: 14px; margin-bottom: 16px; line-height: 1.6; }
.emotion-tips { margin-top: 16px; padding: 12px; background: #f0f9eb; border-radius: 8px; font-size: 13px; color: #67c23a; display: flex; align-items: center; gap: 8px; }
.emotion-placeholder { text-align: center; padding: 32px; color: #999; }

.tips-list { display: flex; flex-direction: column; gap: 16px; }
.tip-item { display: flex; gap: 12px; }
.tip-icon { font-size: 24px; flex-shrink: 0; }
.tip-title { font-weight: bold; font-size: 14px; margin-bottom: 4px; }
.tip-desc { font-size: 12px; color: #999; }

.history-list { display: flex; flex-direction: column; gap: 12px; }
.history-item { padding: 12px; background: #f5f7fa; border-radius: 8px; cursor: pointer; transition: all 0.3s; }
.history-item:hover { background: #ecf5ff; }
.history-content { font-size: 13px; color: #333; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.history-time { font-size: 11px; color: #999; }
.history-placeholder { text-align: center; padding: 24px; color: #999; }

.ai-panel-toggle-bar {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 20;
  background: rgba(20,35,80,.72);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(130,160,240,.35);
  color: #e6ecff;
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  box-shadow: 0 8px 22px rgba(16,24,60,.45);
  transition: transform .15s, background .15s;
}
.ai-panel-toggle-bar:hover { background: rgba(102,126,234,.45); transform: translateY(-2px); }

:deep(.el-radio-button__content) { display: flex; align-items: center; gap: 6px; }
</style>
