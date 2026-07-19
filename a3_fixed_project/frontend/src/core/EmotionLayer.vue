<template>
  <div class="emotion-layer" :class="{ fade: fading }">
    <div v-if="show" class="emotion-bubble" :class="ai.emotion">
      <span class="emo-ic">{{ emo }}</span>
      <span class="emo-text">{{ caption }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useAIStore } from '@/stores/ai'

const ai = useAIStore()
const show = ref(false)
const fading = ref(false)

const emo = computed(() => {
  const map: Record<string, string> = {
    neutral: '😌', curious: '🤔', confident: '😎',
    happy: '😊', concerned: '😰', excited: '🤩'
  }
  return map[ai.emotion] || '😌'
})

const caption = computed(() => {
  if (ai.state === 'thinking')  return '让我想想…'
  if (ai.state === 'processing') return '正在执行…'
  if (ai.state === 'success')   return '完成啦 ✨'
  if (ai.state === 'error')     return '好像哪里不对'
  if (ai.state === 'focus')     return '我在听 👂'
  return '随时待命'
})

watch(() => ai.state, () => {
  show.value = true
  fading.value = false
})
</script>

<style scoped>
.emotion-layer {
  position: fixed;
  bottom: 24px;
  left: 24px;
  z-index: 900;
}
.emotion-bubble {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(20, 20, 35, 0.55);
  backdrop-filter: blur(14px);
  border: 1px solid rgba(180,195,255,.25);
  border-radius: 999px;
  font-size: 13px;
  color: #e6ebff;
  box-shadow: 0 0 30px rgba(108,92,231,.2);
  animation: bubbleIn .4s var(--ease-spring);
}
.emotion-bubble.happy,
.emotion-bubble.excited { border-color: rgba(96,255,176,.4); box-shadow: 0 0 30px rgba(96,255,176,.3); }
.emotion-bubble.concerned { border-color: rgba(255,111,140,.35); box-shadow: 0 0 30px rgba(255,111,140,.25); }

.emo-ic { font-size: 16px; }
.emo-text { font-weight: 600; letter-spacing: .5px; }

@keyframes bubbleIn {
  0% { opacity: 0; transform: translateY(16px) scale(.9); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}
</style>
