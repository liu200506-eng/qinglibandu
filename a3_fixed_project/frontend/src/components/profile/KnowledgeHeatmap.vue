<template>
  <el-table :data="knowledgeList" border>
    <el-table-column prop="name" label="知识点" min-width="150" />
    <el-table-column prop="mastery" label="掌握度" width="120">
      <template #default="{ row }">
        <div class="mastery-bar">
          <div 
            class="mastery-fill" 
            :class="getMasteryClass(row.mastery)"
            :style="{ width: `${row.mastery}%` }"
          ></div>
          <span class="mastery-text">{{ row.mastery }}%</span>
        </div>
      </template>
    </el-table-column>
    <el-table-column prop="error_count" label="错误次数" width="100" />
    <el-table-column prop="correct_count" label="正确次数" width="100" />
    <el-table-column label="操作" width="100">
      <template #default="{ row }">
        <el-button type="primary" link @click="$emit('learn', row.node_id, row.name)">学习</el-button>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { KnowledgeState } from '@/types'

const props = defineProps<{
  knowledgeStates: Record<string, KnowledgeState>
}>()

defineEmits<{
  learn: [nodeId: string, name: string]
}>()

const knowledgeList = computed(() => {
  return Object.values(props.knowledgeStates).map(ks => ({
    ...ks,
    mastery: Math.round(ks.mastery * 100)
  }))
})

function getMasteryClass(mastery: number): string {
  if (mastery >= 80) return 'high'
  if (mastery >= 60) return 'medium'
  return 'low'
}
</script>

<style lang="scss" scoped>
.mastery-bar {
  position: relative;
  height: 20px;
  background: #f0f0f0;
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  align-items: center;
  padding-right: 40px;

  .mastery-fill {
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    border-radius: 10px;
    transition: width 0.3s;

    &.high {
      background: linear-gradient(90deg, #67c23a, #85ce61);
    }

    &.medium {
      background: linear-gradient(90deg, #e6a23c, #ebb563);
    }

    &.low {
      background: linear-gradient(90deg, #f56c6c, #f89898);
    }
  }

  .mastery-text {
    position: relative;
    z-index: 1;
    font-size: 12px;
    color: #666;
    margin-left: 8px;
  }
}
</style>