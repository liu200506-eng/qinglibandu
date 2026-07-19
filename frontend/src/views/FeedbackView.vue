<template>
  <div class="wrongbook">
    <div class="wb-hero">
      <div class="wb-hleft">
        <div class="wb-ic">📕</div>
        <div>
          <div class="wb-h1">我的错题本</div>
          <div class="wb-sub">AI 帮你找出薄弱点，错题重演 + 知识点对照 · 一键加强训练</div>
        </div>
      </div>
      <div class="wb-hright">
        <div class="wb-kpi"><span class="kpi-nm">错题</span><span class="kpi-num">{{ records.length }}</span></div>
        <div class="wb-kpi"><span class="kpi-nm">薄弱</span><span class="kpi-num amber">{{ weakCount }}</span></div>
        <div class="wb-kpi"><span class="kpi-nm">待练</span><span class="kpi-num green">{{ pendingPractice }}</span></div>
        <el-button size="default" :disabled="!records.length" @click="doClear">🗑 清空</el-button>
      </div>
    </div>

    <div v-if="!records.length" class="wb-empty">
      <div class="empty-illus">📘</div>
      <div class="empty-t">错题本空空如也</div>
      <div class="empty-d">做题答错时会自动记录到这里</div>
    </div>

    <div v-else class="wb-grid">
      <div class="col-main">
        <div class="panel">
          <div class="panel-hd">
            <div class="panel-tit">📚 错题列表</div>
            <div class="panel-sb">共 {{ records.length }} 道</div>
          </div>
          <div class="wb-list">
            <div
              v-for="(item, idx) in records"
              :key="item.id"
              class="wb-card"
              :class="{ active: replayId === item.id }"
            >
              <div class="wb-idx" :class="{ replay: replayId === item.id }">
                <template v-if="replayId === item.id">▶</template>
                <template v-else>#{{ idx + 1 }}</template>
              </div>
              <div class="wb-body">
                <div class="wb-q">
                  <span class="q-tag">题目</span>
                  <span>{{ item.question }}</span>
                </div>
                <div class="wb-row">
                  <div class="wb-a wb-a-wrong"><span class="a-tag">你答</span><span>{{ item.user_answer || '（未作答）' }}</span></div>
                  <div class="wb-a wb-a-right"><span class="a-tag">正解</span><span>{{ item.correct_answer }}</span></div>
                </div>
                <div v-if="item.explanation" class="wb-exp">
                  <span class="exp-tag">💡 解析</span>
                  <span>{{ item.explanation }}</span>
                </div>
                <div class="wb-foot">
                  <el-tag v-if="item.knowledge_point" size="small" type="info" effect="light">📌 {{ item.knowledge_point }}</el-tag>
                  <span class="wb-time">{{ fmt(item.created_at) }}</span>
                </div>
              </div>
              <div class="wb-acts">
                <button class="act-btn replay" :class="{ on: replayId === item.id }" @click="toggleReplay(item.id)">
                  🎬 {{ replayId === item.id ? '停止' : '重演' }}
                </button>
                <button class="act-btn train" @click="goTrain(item)">⚡ 练同类</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-side">
        <div class="panel panel-ai">
          <div class="panel-hd">
            <div class="panel-tit">🧠 AI 薄弱点分析</div>
            <span class="ai-tag">Agent · 苏格拉底</span>
          </div>
          <div class="ai-analysis">
            <div v-if="analyzing" class="ai-loading">
              <div class="ai-orbit"><span class="ai-dot"></span></div>
              <div>AI 正在分析你的错题模式…</div>
            </div>
            <div v-else class="ai-content">
              <div class="ai-summary">{{ analysis.summary }}</div>
              <div class="ai-focus">
                <div class="ai-foc-hd">重点薄弱知识</div>
                <div v-for="k in analysis.key_points" :key="k.name" class="ai-kp">
                  <div class="ai-kp-row">
                    <span class="ai-kp-name">📌 {{ k.name }}</span>
                    <span class="ai-kp-pct" :style="{ color: k.color }">{{ k.pct }}%</span>
                  </div>
                  <div class="ai-kp-bar"><div class="ai-kp-fill" :style="{ width: k.pct+'%', background: k.color }"></div></div>
                  <div class="ai-kp-sug">{{ k.suggestion }}</div>
                </div>
              </div>
              <div class="ai-tips">
                <div v-for="(t, i) in analysis.tips" :key="i" class="ai-tip">✨ {{ t }}</div>
              </div>
            </div>
          </div>
          <button class="ai-refresh" @click="runAnalysis" :disabled="analyzing">
            🔄 重新分析
          </button>
        </div>

        <div class="panel panel-replay" v-if="replayId">
          <div class="panel-hd">
            <div class="panel-tit">🎬 错题重演</div>
          </div>
          <div class="replay-box">
            <div class="replay-q">{{ replayItem?.question }}</div>
            <div class="replay-choices" v-if="replayItem?.options?.length">
              <button
                v-for="(o, i) in replayItem.options"
                :key="i"
                class="replay-op"
                :class="{ correct: replaySubmitted && o.startsWith(replayItem.correct_answer), wrong: replaySubmitWrong && o === replayPick }"
                @click="pickReplayOption(o)"
                :disabled="replaySubmitted"
              >{{ o }}</button>
            </div>
            <div v-if="replaySubmitted" class="replay-result">
              <div v-if="replayPick === replayItem?.correct_answer" class="rr-right">✓ 答对啦！这题你已经掌握了 🎉</div>
              <div v-else class="rr-wrong">
                <div>✗ 还是答错了，再来一次解析：</div>
                <div class="rr-exp">{{ replayItem?.explanation }}</div>
                <div class="rr-next">下一题会继续考察同类知识点</div>
              </div>
            </div>
            <div class="replay-actions">
              <el-button v-if="replaySubmitted" size="small" @click="nextReplay">下一题 →</el-button>
              <el-button v-if="replaySubmitted" size="small" type="success" plain @click="closeReplay">完成 ✓</el-button>
            </div>
          </div>
        </div>

        <div class="panel panel-train">
          <div class="panel-hd">
            <div class="panel-tit">⚡ 知识点对照 · 加强训练</div>
            <span class="train-tag">推荐 {{ trainList.length }} 题</span>
          </div>
          <div v-if="!trainList.length" class="train-empty">
            选择左侧任意一道错题 → 点击「⚡ 练同类」按钮，就会推荐同知识点的强化训练
          </div>
          <div v-else class="train-list">
            <div v-for="(t, i) in trainList" :key="i" class="train-item">
              <div class="tidx">{{ i + 1 }}</div>
              <div class="tq">
                <div class="tq-q">{{ t.question }}</div>
                <div class="tq-kp">📌 {{ t.knowledge_point }} · 训练题</div>
              </div>
              <div class="tops" v-if="t.options?.length">
                <div v-for="(o, j) in t.options" :key="j" class="top" @click="pickTrain(t, o)">
                  <span class="top-label">{{ optLabel(j) }}</span>
                  <span>{{ o }}</span>
                  <span class="top-mark" v-if="trainMap[t.id] && trainMap[t.id].picked === optLabel(j) && trainMap[t.id].ok">✓</span>
                  <span class="top-mark wrong" v-else-if="trainMap[t.id] && trainMap[t.id].picked === optLabel(j) && !trainMap[t.id].ok">✗</span>
                </div>
              </div>
              <div v-if="trainMap[t.id]?.showExp" class="texp">💡 {{ t.explanation }}</div>
            </div>
          </div>
          <div class="train-cta">
            <el-button type="primary" @click="$router.push('/resources')">📖 去知识练习做更多</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

interface ErrorItem {
  id: number | string
  question: string
  user_answer: string
  correct_answer: string
  knowledge_point: string
  explanation: string
  created_at?: string
  options?: string[]
}

const MOCK: ErrorItem[] = [
  {
    id: 1, question: '下列 HTTP 方法中，具有幂等性且是【安全】的是？',
    user_answer: 'B', correct_answer: 'C',
    knowledge_point: 'HTTP 请求方法',
    explanation: 'GET 用于获取资源，不应修改服务器状态，因此是【安全】且幂等的。POST 非幂等且不安全，PUT/PATCH 幂等但不安全。',
    created_at: new Date(Date.now() - 1000*60*60*5).toISOString(),
    options: ['A. POST', 'B. PUT', 'C. GET', 'D. DELETE']
  },
  {
    id: 2, question: 'HTTP 状态码 304 的含义是？',
    user_answer: 'A', correct_answer: 'C',
    knowledge_point: 'HTTP 缓存与状态码',
    explanation: '304 Not Modified 表示协商缓存命中，直接使用本地缓存，不必重新下载。',
    created_at: new Date(Date.now() - 1000*60*60*24).toISOString(),
    options: ['A. 资源不存在', 'B. 请求重定向', 'C. 资源未修改，使用缓存', 'D. 请求被拒绝']
  },
  {
    id: 3, question: 'HTTPS 默认端口是多少？',
    user_answer: 'A', correct_answer: 'B',
    knowledge_point: 'HTTPS',
    explanation: 'HTTPS=HTTP+TLS，默认 443；HTTP 默认 80。',
    created_at: new Date(Date.now() - 1000*60*60*24*2).toISOString(),
    options: ['A. 80', 'B. 443', 'C. 8080', 'D. 3000']
  },
  {
    id: 4, question: 'TCP 三次握手的第二次握手由谁发出？标志位是？',
    user_answer: 'SYN', correct_answer: 'SYN+ACK',
    knowledge_point: 'TCP',
    explanation: '第一次：客户端发 SYN；第二次：服务器发 SYN+ACK；第三次：客户端发 ACK。',
    created_at: new Date(Date.now() - 1000*60*60*24*3).toISOString()
  }
]

const records = ref<ErrorItem[]>([])

const replayId = ref<number | string | null>(null)
const replaySubmitted = ref(false)
const replaySubmitWrong = ref(false)
const replayPick = ref('')
const replayIdx = ref(0)

const analyzing = ref(false)
const analysis = reactive<{ summary: string; key_points: { name: string; pct: number; color: string; suggestion: string }[]; tips: string[] }>({
  summary: '', key_points: [], tips: []
})

function colorOf(v: number) {
  if (v >= 70) return '#059669'
  if (v >= 40) return '#f59e0b'
  return '#dc2626'
}

function runAnalysis() {
  if (!records.value.length) return
  analyzing.value = true
  analysis.summary = ''
  analysis.key_points = []
  analysis.tips = []
  setTimeout(() => {
    const counts: Record<string, number> = {}
    records.value.forEach(r => {
      const k = r.knowledge_point || '未分类'
      counts[k] = (counts[k] || 0) + 1
    })
    const points = Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 4)
      .map(([name, c]) => {
        const pct = Math.min(Math.round((c / records.value.length) * 100), 95)
        return {
          name, pct,
          color: colorOf(100 - pct),
          suggestion: genSuggestion(name)
        }
      })
    const totalKp = Object.keys(counts).length
    const maxCount = Math.max(...Object.values(counts), 1)
    analysis.summary = `你最近有 ${records.value.length} 道错题，分布在 ${totalKp} 个知识点中。重复出错最多的是「${points[0]?.name || '—'}」（${maxCount} 次），建议优先使用苏格拉底式追问复盘。`
    analysis.key_points = points
    analysis.tips = [
      `「${points[0]?.name}」是当前最薄弱的环节，推荐用 AI 辅导模式做 15 分钟追问式学习`,
      `本周错题集中在网络协议层，建议对照 OSI 七层模型画一张思维导图`,
      `开启「每日一练」每天做 10 道相关题目，一周内正确率通常能回升到 75%+`
    ]
    analyzing.value = false
  }, 1200)
}

function genSuggestion(name: string): string {
  const map: Record<string, string> = {
    'HTTP 请求方法': '建议用苏格拉底式追问：让 AI 一步步带你区分 GET/POST/PUT/PATCH/DELETE 的语义',
    'HTTP 缓存与状态码': '建议看 MDN HTTP Caching 一章 + 图解 200/304/400/500 常见场景',
    'HTTPS': '建议对比 HTTPS=HTTP+TLS+443 vs HTTP=80，并掌握 TLS 握手流程',
    'TCP': '建议手写三次握手/四次分手时序图 + 画 SYN/ACK 标志位',
    '未分类': '建议先给错题打上知识点标签，再进行针对性训练'
  }
  return map[name] || `建议用 15 分钟苏格拉底式追问辅导来把「${name}」彻底吃透`
}

async function loadRecords() {
  const sid = localStorage.getItem('student_id') || '1'
  try {
    const res = await fetch(`/api/db/error-records/${sid}`)
    const data = await res.json()
    if (data?.status === 'success' && (data.items || []).length) {
      records.value = data.items
    } else {
      records.value = [...MOCK]
    }
  } catch {
    records.value = [...MOCK]
  }
  if (records.value.length) runAnalysis()
}

async function doClear() {
  try {
    await ElMessageBox.confirm('确定要清空全部错题吗？', '清空错题本', {
      confirmButtonText: '清空',
      cancelButtonText: '算了',
      type: 'warning'
    })
  } catch { return }
  const sid = localStorage.getItem('student_id') || '1'
  try { await fetch(`/api/db/error-records/clear/${sid}`, { method: 'DELETE' }) } catch {}
  records.value = []
  ElMessage.success('错题本已清空')
}

const weakCount = computed(() => analysis.key_points.filter(k => k.pct >= 40).length)
const pendingPractice = computed(() => Math.min(records.value.length * 2, 12))

const replayItem = computed(() => {
  if (replayId.value == null) return null
  return records.value.find(r => r.id === replayId.value) || null
})

function toggleReplay(id: number | string) {
  if (replayId.value === id) {
    replayId.value = null
  } else {
    replayId.value = id
    replayIdx.value = records.value.findIndex(r => r.id === id)
  }
  replaySubmitted.value = false
  replaySubmitWrong.value = false
  replayPick.value = ''
}

function pickReplayOption(o: string) {
  if (replaySubmitted.value) return
  replayPick.value = o
  replaySubmitted.value = true
  replaySubmitWrong.value = !o.startsWith(replayItem.value?.correct_answer || '')
}

function nextReplay() {
  replayIdx.value++
  if (replayIdx.value >= records.value.length) {
    replayIdx.value = 0
  }
  replayId.value = records.value[replayIdx.value].id
  replaySubmitted.value = false
  replaySubmitWrong.value = false
  replayPick.value = ''
}

function closeReplay() {
  replayId.value = null
}

const TRAIN_MAP: Record<string, ErrorItem[]> = {
  'HTTP 请求方法': [
    { id: 't1', question: '下列哪个 HTTP 方法是【幂等】的？', user_answer: '', correct_answer: 'B', knowledge_point: 'HTTP 请求方法', explanation: 'PUT 幂等；POST 非幂等。', options: ['A. POST', 'B. PUT', 'C. PATCH', 'D. 都不是'] },
    { id: 't2', question: '哪个 HTTP 方法最适合"创建新资源"？', user_answer: '', correct_answer: 'A', knowledge_point: 'HTTP 请求方法', explanation: 'POST 用于创建；PUT 用于全量更新/幂等创建。', options: ['A. POST', 'B. PUT', 'C. GET', 'D. DELETE'] },
    { id: 't3', question: 'GET 请求的 URL 长度有限制，因为它把参数放在？', user_answer: '', correct_answer: 'A', knowledge_point: 'HTTP 请求方法', explanation: '参数在 query string（URL 末尾），长度受限；POST 在 request body。', options: ['A. URL query string', 'B. Request body', 'C. Header', 'D. Cookie'] }
  ],
  'HTTP 缓存与状态码': [
    { id: 't4', question: '状态码 304 Not Modified 属于？', user_answer: '', correct_answer: 'B', knowledge_point: 'HTTP 缓存与状态码', explanation: '3xx 重定向/协商类，304 是缓存协商命中。', options: ['A. 2xx 成功', 'B. 3xx 重定向/缓存', 'C. 4xx 客户端错误', 'D. 5xx 服务器错误'] },
    { id: 't5', question: 'Cache-Control: no-cache 表示？', user_answer: '', correct_answer: 'A', knowledge_point: 'HTTP 缓存与状态码', explanation: 'no-cache 不是"不缓存"，而是使用缓存前必须向服务器确认是否过期。', options: ['A. 可缓存但每次必须向服务器验证', 'B. 完全不缓存', 'C. 无限期缓存', 'D. 只允许客户端缓存'] }
  ],
  'HTTPS': [
    { id: 't6', question: 'TLS 握手第一阶段交换的是？', user_answer: '', correct_answer: 'A', knowledge_point: 'HTTPS', explanation: 'ClientHello / ServerHello，交换密码套件、随机数等。', options: ['A. ClientHello / ServerHello', 'B. 公钥加密数据', 'C. 应用层 HTTP 数据', 'D. 证书签名请求'] },
    { id: 't7', question: 'HTTPS 比 HTTP 多了一层 TLS，主要解决什么问题？', user_answer: '', correct_answer: 'D', knowledge_point: 'HTTPS', explanation: 'TLS 提供加密（防窃听）+ 身份认证（证书）+ 完整性（MAC）。', options: ['A. 更快速度', 'B. 更小体积', 'C. 自动压缩', 'D. 机密性 + 身份认证 + 完整性'] }
  ],
  'TCP': [
    { id: 't8', question: 'TCP 三次握手第三次客户端发送的是？', user_answer: '', correct_answer: 'C', knowledge_point: 'TCP', explanation: '第三次仅 ACK 位，序号确认服务器的 SYN。', options: ['A. SYN', 'B. SYN+ACK', 'C. ACK', 'D. FIN'] },
    { id: 't9', question: 'TCP 四次分手比三次握手多一次是因为？', user_answer: '', correct_answer: 'B', knowledge_point: 'TCP', explanation: '服务器收到 FIN 时可能还有数据没发完，所以先发 ACK，等发完再发 FIN，合成两次。', options: ['A. TCP 设计复杂', 'B. 服务器可能还有数据未发送完', 'C. UDP 不需要', 'D. 防火墙要求'] }
  ],
  '未分类': [
    { id: 'tu1', question: '推荐先给错题打标签再训练哦', user_answer: '', correct_answer: 'A', knowledge_point: '未分类', explanation: '请在知识练习中按章节分类练习。', options: ['A. 好的', 'B. 不用了', 'C. 等等', 'D. 随便'] }
  ]
}

const trainList = ref<ErrorItem[]>([])
const trainMap = reactive<Record<string, { picked: string; ok: boolean; showExp: boolean }>>({})

function goTrain(item: ErrorItem) {
  const k = item.knowledge_point || '未分类'
  trainList.value = TRAIN_MAP[k] || TRAIN_MAP['未分类']
  trainList.value.forEach(t => {
    if (!trainMap[t.id]) trainMap[t.id] = { picked: '', ok: false, showExp: false }
  })
  ElMessage.success(`已为你找好 ${k} 的 ${trainList.value.length} 道强化训练`)
}

function optLabel(i: number) {
  return ['A', 'B', 'C', 'D', 'E', 'F'][i] || String(i + 1)
}

function pickTrain(t: ErrorItem, o: string) {
  if (trainMap[t.id]?.showExp) return
  const i = (t.options || []).indexOf(o)
  const label = optLabel(i)
  const ok = label === t.correct_answer
  trainMap[t.id] = { picked: label, ok, showExp: true }
  if (ok) ElMessage.success('✓ 答对啦')
  else ElMessage.warning('✗ 看下解析再试一道')
}

function fmt(s?: string) {
  if (!s) return ''
  const d = new Date(s)
  const n = new Date()
  const diff = n.getTime() - d.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return d.toLocaleDateString('zh-CN')
}

onMounted(loadRecords)
</script>

<style scoped>
.wrongbook {
  padding: 20px 28px 28px;
  display: flex; flex-direction: column; gap: 16px;
  min-height: 0;
}

.wb-hero {
  display: flex; justify-content: space-between; align-items: center; gap: 14px;
  padding: 18px 22px;
  background: linear-gradient(135deg, #fff7ed 0%, #ffffff 60%);
  border: 1px solid #fed7aa;
  border-radius: var(--r-lg, 16px);
  box-shadow: 0 4px 16px rgba(245,158,11,.06);
}
.wb-hleft { display: flex; align-items: center; gap: 14px; }
.wb-ic {
  width: 46px; height: 46px; border-radius: 14px;
  background: #fff7ed; color: #ea580c;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 22px; border: 1px solid #fed7aa;
}
.wb-h1 { font-size: 20px; font-weight: 700; color: #1e293b; letter-spacing: 1px; }
.wb-sub { font-size: 12px; color: #94a3b8; margin-top: 2px; }

.wb-hright { display: flex; align-items: center; gap: 8px; }
.wb-kpi {
  display: inline-flex; align-items: baseline; gap: 4px;
  padding: 4px 10px; border-radius: 999px;
  background: #fff; border: 1px solid #fed7aa;
}
.kpi-nm { font-size: 10px; color: #94a3b8; letter-spacing: 1px; }
.kpi-num { font-size: 14px; font-weight: 800; font-family: var(--font-mono, monospace); color: #ea580c; }
.kpi-num.amber { color: #f59e0b; }
.kpi-num.green { color: #059669; }

.wb-empty {
  padding: 80px 20px; text-align: center;
  border: 1.5px dashed var(--c-border, #e7e5e2);
  border-radius: var(--r-lg, 16px); background: #fff;
}
.empty-illus { font-size: 64px; margin-bottom: 14px; }
.empty-t { font-size: 16px; font-weight: 600; color: #475569; }
.empty-d { font-size: 13px; color: #94a3b8; margin-top: 6px; }

.wb-grid { display: grid; grid-template-columns: 1.3fr 1fr; gap: 14px; }
@media (max-width: 1100px) { .wb-grid { grid-template-columns: 1fr; } }

.panel {
  background: #fff; border: 1px solid #e7e5e2; border-radius: 16px;
  padding: 16px 18px;
  box-shadow: 0 2px 10px rgba(0,0,0,.04);
}
.panel-hd { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.panel-tit { font-size: 14px; font-weight: 800; letter-spacing: .5px; color: #0f172a; }
.panel-sb { margin-left: auto; font-size: 11px; color: #94a3b8; letter-spacing: 1px; }

.panel-ai {
  background: linear-gradient(160deg, #f0fdfa 0%, #ffffff 70%);
  border-color: #ccfbf1;
}
.ai-tag {
  padding: 2px 10px; border-radius: 999px;
  background: #0d9488; color: #fff;
  font-size: 10px; font-weight: 700; letter-spacing: 1px;
}
.train-tag {
  padding: 2px 10px; border-radius: 999px;
  background: #fef3c7; color: #92400e;
  font-size: 10px; font-weight: 700; letter-spacing: 1px;
}

.ai-loading {
  padding: 40px; text-align: center; color: #64748b; font-size: 13px;
}
.ai-orbit {
  width: 48px; height: 48px; margin: 0 auto 10px;
  border: 3px solid #ccfbf1; border-top-color: #0d9488;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin { from{transform:rotate(0)}to{transform:rotate(360deg)} }
.ai-content { display: flex; flex-direction: column; gap: 12px; }
.ai-summary {
  padding: 12px 14px;
  background: #fffbeb; border-left: 3px solid #f59e0b;
  border-radius: 10px;
  font-size: 13px; color: #78350f; line-height: 1.65;
}
.ai-foc-hd { font-size: 11px; font-weight: 700; color: #0d9488; letter-spacing: 2px; margin-bottom: 8px; }
.ai-kp { margin-bottom: 10px; }
.ai-kp-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 3px; }
.ai-kp-name { font-size: 12px; font-weight: 600; color: #0f172a; }
.ai-kp-pct { font-size: 12px; font-weight: 800; font-family: var(--font-mono, monospace); }
.ai-kp-bar { height: 6px; background: #f1f5f4; border-radius: 999px; overflow: hidden; margin-bottom: 4px; }
.ai-kp-fill { height: 100%; border-radius: 999px; transition: width .6s ease; }
.ai-kp-sug { font-size: 11px; color: #64748b; line-height: 1.5; }

.ai-tips { display: flex; flex-direction: column; gap: 6px; }
.ai-tip {
  padding: 6px 10px;
  background: #f0fdfa; border-radius: 8px;
  font-size: 12px; color: #0f766e; line-height: 1.5;
}

.ai-refresh {
  margin-top: 10px; width: 100%; padding: 8px;
  background: transparent; border: 1px dashed #0d9488; border-radius: 10px;
  color: #0d9488; font-weight: 600; letter-spacing: 1px; cursor: pointer;
  transition: all .2s ease;
}
.ai-refresh:hover { background: #f0fdfa; border-style: solid; }

.wb-list { display: flex; flex-direction: column; gap: 10px; }
.wb-card {
  display: flex; gap: 12px; padding: 14px 16px;
  background: #fff; border: 1px solid #e7e5e2;
  border-left: 4px solid #f97316; border-radius: 12px;
  transition: all .15s ease;
}
.wb-card:hover { box-shadow: 0 6px 18px rgba(249,115,22,.08); }
.wb-card.active { border-left-color: #0d9488; background: #f0fdfa; }

.wb-idx {
  flex-shrink: 0; width: 34px; height: 34px; border-radius: 10px;
  background: #fff7ed; color: #ea580c;
  font-weight: 700; font-size: 13px; font-family: var(--font-mono, monospace);
  display: inline-flex; align-items: center; justify-content: center;
  border: 1px solid #fed7aa;
}
.wb-idx.replay { background: #0d9488; color: #fff; border-color: #0d9488; }

.wb-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 8px; }
.wb-q { display: flex; align-items: flex-start; gap: 8px; font-size: 13px; color: #0f172a; line-height: 1.6; font-weight: 500; }
.q-tag { flex-shrink: 0; padding: 2px 8px; border-radius: 6px; background: #ffedd5; color: #c2410c; font-size: 11px; font-weight: 600; letter-spacing: 1px; margin-top: 1px; }
.wb-row { display: flex; gap: 10px; flex-wrap: wrap; }
.wb-a { display: inline-flex; align-items: center; gap: 6px; padding: 5px 10px; border-radius: 8px; font-size: 12px; }
.wb-a-wrong { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.wb-a-right { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
.a-tag { font-size: 10px; font-weight: 600; letter-spacing: 1px; opacity: .9; }

.wb-exp { padding: 8px 10px; background: #fafaf8; border: 1px dashed #cbd5e1; border-radius: 10px; font-size: 12px; color: #475569; line-height: 1.6; display: flex; align-items: flex-start; gap: 6px; }
.exp-tag { font-weight: 600; color: #475569; flex-shrink: 0; }

.wb-foot { display: flex; justify-content: space-between; align-items: center; }
.wb-time { font-size: 10px; color: #94a3b8; letter-spacing: .5px; }

.wb-acts { display: flex; flex-direction: column; gap: 6px; flex-shrink: 0; }
.act-btn {
  padding: 6px 10px; border: 1px solid #e7e5e2; border-radius: 10px;
  background: #fff; font-size: 11px; font-weight: 600; cursor: pointer;
  letter-spacing: 1px;
  transition: all .15s ease;
}
.act-btn.replay { color: #0ea5e9; }
.act-btn.replay.on { background: #0ea5e9; color: #fff; border-color: #0ea5e9; }
.act-btn.train { color: #059669; border-color: #bbf7d0; background: #f0fdf4; }
.act-btn.train:hover { background: #059669; color: #fff; border-color: #059669; }

.panel-replay { margin-top: 14px; background: linear-gradient(160deg, #f0f9ff 0%, #ffffff 70%); border-color: #bfdbfe; }
.replay-box { display: flex; flex-direction: column; gap: 10px; }
.replay-q { padding: 10px 12px; background: #fff; border-radius: 10px; font-size: 14px; color: #0f172a; line-height: 1.6; font-weight: 500; border: 1px solid #bfdbfe; }
.replay-choices { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.replay-op { padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 8px; background: #fff; font-size: 12px; color: #1e293b; cursor: pointer; text-align: left; transition: all .1s ease; }
.replay-op:hover:not(:disabled) { background: #f0fdfa; border-color: #0d9488; }
.replay-op.correct { border-color: #059669; background: #f0fdf4; color: #059669; font-weight: 600; }
.replay-op.wrong { border-color: #dc2626; background: #fef2f2; color: #dc2626; }
.replay-op:disabled { cursor: default; }
.replay-result { padding: 8px 12px; border-radius: 10px; background: #fffbeb; border: 1px solid #fde68a; font-size: 12px; line-height: 1.6; }
.rr-right { color: #059669; font-weight: 600; }
.rr-wrong { color: #b45309; }
.rr-exp { margin-top: 6px; padding: 8px 10px; background: #fef3c7; border-radius: 8px; font-size: 12px; color: #78350f; line-height: 1.6; }
.rr-next { margin-top: 6px; font-size: 11px; color: #0d9488; font-weight: 600; }
.replay-actions { display: flex; gap: 8px; margin-top: 4px; }

.panel-train { margin-top: 14px; background: linear-gradient(160deg, #f0fdf4 0%, #ffffff 70%); border-color: #bbf7d0; }
.train-empty { padding: 20px; text-align: center; color: #64748b; font-size: 12px; line-height: 1.6; }
.train-list { display: flex; flex-direction: column; gap: 12px; }
.train-item { padding: 10px 12px; background: #fff; border-radius: 10px; border: 1px solid #e5e7eb; }
.tidx { font-size: 10px; font-weight: 700; color: #059669; font-family: var(--font-mono, monospace); margin-bottom: 4px; }
.tq-q { font-size: 12px; color: #0f172a; line-height: 1.6; font-weight: 500; }
.tq-kp { font-size: 10px; color: #059669; margin-top: 3px; letter-spacing: .5px; }
.tops { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; margin-top: 8px; }
.top { padding: 5px 8px; font-size: 11px; color: #1e293b; border: 1px solid #e5e7eb; border-radius: 6px; cursor: pointer; background: #fff; display: flex; justify-content: space-between; align-items: center; transition: all .1s ease; }
.top:hover { border-color: #059669; background: #f0fdf4; }
.top-label { font-weight: 600; color: #059669; margin-right: 4px; }
.top-mark { color: #059669; font-weight: 700; }
.top-mark.wrong { color: #dc2626; }
.texp { margin-top: 6px; padding: 6px 8px; background: #f0fdf4; border-radius: 6px; font-size: 11px; color: #059669; line-height: 1.6; border: 1px dashed #86efac; }

.train-cta { margin-top: 10px; display: flex; justify-content: center; }
</style>
