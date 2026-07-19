<template>
  <div class="rag-container">
    <div class="rag-header">
      <div>
        <h2>📚 计算机网络知识库</h2>
        <div class="course-hint">比赛示范课程 · 当前仅检索计算机网络内容</div>
      </div>
      <div class="stats-badge" v-if="stats.total_points">
        已入库 {{ stats.total_points }} 个文档片段
      </div>
    </div>

    <div class="rag-upload">
      <el-upload
        class="upload-demo"
        drag
        multiple
        :auto-upload="false"
        :on-change="handleFileChange"
        :file-list="fileList"
        accept=".pdf,.docx,.doc,.png,.jpg,.jpeg,.txt,.md"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 PDF、Word、图片、文本等格式
          </div>
        </template>
      </el-upload>
      <el-button
        v-if="fileList.length > 0"
        type="primary"
        :loading="uploading"
        @click="handleUpload"
      >
        开始入库
      </el-button>
      <el-button
        v-if="fileList.length > 0"
        @click="clearFiles"
      >
        清空
      </el-button>
    </div>

    <div class="rag-search">
      <el-input
        v-model="query"
        placeholder="输入问题检索知识库..."
        :loading="searching"
        @keyup.enter="handleSearch"
      >
        <template #append>
          <el-button @click="handleSearch">
            <el-icon><Search /></el-icon>
          </el-button>
        </template>
      </el-input>
      <el-select v-model="topK" style="width: 120px; margin-left: 10px">
        <el-option label="返回3条" :value="3" />
        <el-option label="返回5条" :value="5" />
        <el-option label="返回10条" :value="10" />
      </el-select>
    </div>

    <div class="rag-results" v-if="results.length > 0">
      <div class="result-header">
        <span>检索结果</span>
        <span class="count">共 {{ results.length }} 条</span>
      </div>
      <div
        v-for="(result, index) in results"
        :key="index"
        class="result-item"
      >
        <div class="result-rank">#{{ index + 1 }}</div>
        <div class="result-content">
          <MarkdownContent class="result-text" :content="result.text" />
          <div class="result-meta">
            <span class="score">重排分数: {{ result.rerank_score?.toFixed(4) }}</span>
            <span class="sources">来源: {{ result.source_file || result.node_name || '计算机网络知识库' }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="rag-empty" v-if="!searching && results.length === 0 && query">
      <el-empty description="未找到相关结果，请尝试其他关键词或上传文档" />
    </div>

    <div class="rag-actions" v-if="stats.total_points">
      <el-button
        type="danger"
        size="small"
        @click="handleClear"
      >
        清空知识库
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { UploadFilled, Search } from '@element-plus/icons-vue'
import { aiApi } from '@/api/ai'
import { ElMessage } from 'element-plus'
import MarkdownContent from '@/components/MarkdownContent.vue'

const PRIMARY_SUBJECT = '计算机网络'

const query = ref('')
const topK = ref(5)
const results = ref<any[]>([])
const searching = ref(false)
const uploading = ref(false)
const fileList = ref<any[]>([])
const stats = ref({ total_points: 0 })

onMounted(async () => {
  await loadStats()
})

async function loadStats() {
  try {
    const data = await aiApi.ragStats(PRIMARY_SUBJECT)
    stats.value = data
  } catch {}
}

function handleFileChange(_file: any, list: any[]) {
  fileList.value = list
}

function clearFiles() {
  fileList.value = []
}

async function handleUpload() {
  uploading.value = true
  try {
    const files = fileList.value.map(f => f.raw)
    const data = await aiApi.ragUpload(files, PRIMARY_SUBJECT)
    if (data.results) {
      data.results.forEach((r: any) => {
        if (r.success) {
          ElMessage.success(`${r.filename} 入库成功，共 ${r.chunks_count} 个片段`)
        } else {
          ElMessage.error(`${r.filename} 入库失败: ${r.message}`)
        }
      })
    }
    clearFiles()
    await loadStats()
  } catch (e: any) {
    ElMessage.error('上传失败: ' + e.message)
  } finally {
    uploading.value = false
  }
}

async function handleSearch() {
  if (!query.value.trim()) return
  searching.value = true
  results.value = []
  try {
    const data = await aiApi.ragQuery(query.value, topK.value, PRIMARY_SUBJECT)
    results.value = data.results || []
  } catch (e: any) {
    ElMessage.error('检索失败: ' + e.message)
  } finally {
    searching.value = false
  }
}

async function handleClear() {
  await aiApi.ragClear()
  ElMessage.success('知识库已清空')
  await loadStats()
  results.value = []
}
</script>

<style scoped>
.rag-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.rag-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.course-hint { margin-top: 4px; color: #64748b; font-size: 13px; }

.stats-badge {
  background: #e6f7ff;
  color: #1890ff;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 14px;
}

.rag-upload {
  margin-bottom: 20px;
}

.rag-search {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.rag-results {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
}

.result-header {
  background: #f5f7fa;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.count {
  color: #909399;
  font-weight: normal;
}

.result-item {
  display: flex;
  padding: 16px;
  border-bottom: 1px solid #ebeef5;
  transition: background 0.2s;
}

.result-item:last-child {
  border-bottom: none;
}

.result-item:hover {
  background: #fafafa;
}

.result-rank {
  width: 32px;
  height: 32px;
  background: #1890ff;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
  margin-right: 16px;
}

.result-content {
  flex: 1;
}

.result-text {
  color: #303133;
  line-height: 1.6;
  margin-bottom: 8px;
}

.result-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #909399;
}

.score {
  color: #52c41a;
}

.sources {
  color: #1890ff;
}

.rag-empty {
  padding: 40px;
}

.rag-actions {
  margin-top: 20px;
  text-align: right;
}
</style>
