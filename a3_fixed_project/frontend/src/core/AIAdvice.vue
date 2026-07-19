<template>
  <div class="advice-card glass">
    <div class="card-head">
      <span class="ic">🧾</span>
      <span class="title">AI 学习建议</span>
    </div>

    <div class="advice-list">
      <div v-for="(a, i) in advices" :key="i" class="advice-item" :class="{ high: a.priority === 'high' }">
        <span class="a-ic">{{ a.ic }}</span>
        <div class="a-body">
          <div class="a-title">{{ a.title }}</div>
          <div class="a-reason">{{ a.reason }}</div>
          <div class="a-action">
            <span class="a-btn" @click="$emit('goto', a.path)">{{ a.btn }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineEmits<(e: 'goto', path: string) => void>()

interface Advice {
  ic: string
  title: string
  reason: string
  btn: string
  path: string
  priority?: 'high' | 'normal'
}

const advices = ref<Advice[]>([
  {
    ic: '🔥',
    title: '三角函数需重点巩固',
    reason: '近3次练习正确率 42%，建议用苏格拉底式追问辅导',
    btn: '去 AI 答疑',
    path: '/tutoring',
    priority: 'high'
  },
  {
    ic: '📖',
    title: '今日推荐：导数链式法则 15 题',
    reason: '你已掌握基础导数，进阶训练能推进迁移能力',
    btn: '开始练习',
    path: '/resources'
  },
  {
    ic: '😴',
    title: '学习时长已达 2h+，建议休息 5 分钟',
    reason: '能量 0.68，疲劳积累中，深呼吸或站起走动',
    btn: '好的',
    path: '/'
  }
])
</script>

<style scoped>
.advice-card { padding: 18px 20px; grid-column: span 1; }
.card-head { display: flex; align-items: center; gap: 8px; font-family: ui-monospace, monospace; font-size: 11px; letter-spacing: 2px; color: #5a68a0; margin-bottom: 12px; }
.card-head .title { font-weight: 700; color: #0d9488; }

.advice-list { display: flex; flex-direction: column; gap: 10px; }
.advice-item {
  display: flex; gap: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(10,14,30,.55);
  border: 1px solid rgba(124,140,255,.14);
  transition: all .2s ease;
}
.advice-item:hover { background: rgba(124,140,255,.08); border-color: rgba(124,140,255,.3); }
.advice-item.high { border-color: rgba(255,184,96,.4); background: rgba(255,184,96,.08); }
.a-ic { font-size: 20px; flex-shrink: 0; }
.a-body { display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 0; }
.a-title { font-size: 13px; font-weight: 700; color: #e6ebff; letter-spacing: .3px; }
.a-reason { font-size: 11px; color: #0d9488; line-height: 1.5; }
.a-action { margin-top: 4px; }
.a-btn {
  display: inline-block;
  padding: 3px 10px;
  background: linear-gradient(90deg, #4f7cff, #7c4dff);
  border-radius: 999px;
  font-size: 11px; font-weight: 600; color: #e6ebff; letter-spacing: .5px;
  cursor: pointer;
  transition: all .2s ease;
}
.a-btn:hover { transform: translateY(-1px); box-shadow: 0 0 18px rgba(124,140,255,.5); }
</style>
