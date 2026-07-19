<template>
  <div class="digital-human-container">
    <div class="dh-header">
      <span class="dh-title">🧑‍🏫 青藜老师</span>
      <el-tag :type="mode === 'socratic' ? 'success' : 'primary'" size="small">
        {{ mode === 'socratic' ? '启发引导' : '直接讲解' }}
      </el-tag>
    </div>

    <div class="dh-character" :class="{ speaking: isSpeaking }">
      <svg viewBox="0 0 200 240" class="dh-svg">
        <defs>
          <radialGradient id="skinGradient" cx="50%" cy="30%" r="70%">
            <stop offset="0%" stop-color="#FFE4D0" />
            <stop offset="100%" stop-color="#E8C4A8" />
          </radialGradient>
          <radialGradient id="hairGradient" cx="50%" cy="20%" r="60%">
            <stop offset="0%" stop-color="#4A4A4A" />
            <stop offset="100%" stop-color="#2D2D2D" />
          </radialGradient>
          <radialGradient id="shirtGradient" cx="50%" cy="30%" r="70%">
            <stop offset="0%" stop-color="#4A90D9" />
            <stop offset="100%" stop-color="#357ABD" />
          </radialGradient>
        </defs>

        <ellipse cx="100" cy="230" rx="60" ry="8" fill="#DDD" opacity="0.5" />

        <ellipse cx="100" cy="200" rx="50" ry="30" fill="url(#shirtGradient)" />
        <path d="M70 170 Q100 165 130 170" stroke="#357ABD" stroke-width="2" fill="none" />

        <circle cx="100" cy="110" r="55" fill="url(#skinGradient)" />

        <ellipse cx="100" cy="65" rx="40" ry="20" fill="url(#hairGradient)" />
        <ellipse cx="60" cy="100" rx="15" ry="25" fill="url(#hairGradient)" />
        <ellipse cx="140" cy="100" rx="15" ry="25" fill="url(#hairGradient)" />

        <circle cx="78" cy="100" r="8" fill="#2D2D2D" />
        <circle cx="78" cy="100" r="3" fill="#FFF" />
        <circle cx="122" cy="100" r="8" fill="#2D2D2D" />
        <circle cx="122" cy="100" r="3" fill="#FFF" />

        <path d="M85 115 Q100 125 115 115" stroke="#D4A5A5" stroke-width="3" fill="none" stroke-linecap="round" />

        <ellipse cx="65" cy="120" rx="8" ry="5" fill="#FFCCCC" opacity="0.6" />
        <ellipse cx="135" cy="120" rx="8" ry="5" fill="#FFCCCC" opacity="0.6" />

        <ellipse cx="100" cy="145" rx="18" ry="12" fill="#FFE4D0" />
        <ellipse
          cx="100"
          :cy="mouthY"
          rx="12"
          :ry="mouthOpen"
          fill="#D4A5A5"
          class="dh-mouth"
        />
      </svg>

      <div class="dh-emotion">
        <span v-if="emotion === 'happy'">😊</span>
        <span v-else-if="emotion === 'thinking'">🤔</span>
        <span v-else-if="emotion === 'explaining'">💡</span>
        <span v-else-if="emotion === 'questioning'">❓</span>
        <span v-else>👋</span>
      </div>
    </div>

    <div class="dh-controls" v-if="hasAudio">
      <el-button
        size="small"
        :icon="isPlaying ? VideoPause : VideoPlay"
        :type="isPlaying ? 'primary' : 'default'"
        circle
        @click="togglePlay"
      />
      <div class="dh-progress">
        <el-slider
          v-model="progress"
          :max="duration"
          @change="seekTo"
          :disabled="!isPlaying"
          size="small"
          style="width: 120px"
        />
      </div>
      <div class="dh-time">
        {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
      </div>
    </div>

    <div class="dh-subtitle" v-if="subtitle">
      <div class="subtitle-text">{{ subtitle }}</div>
    </div>

    <div class="dh-mode-switch">
      <el-radio-group v-model="mode" size="small">
        <el-radio-button label="direct">📖 讲解</el-radio-button>
        <el-radio-button label="socratic">💬 引导</el-radio-button>
      </el-radio-group>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { VideoPlay, VideoPause } from '@element-plus/icons-vue'

const props = defineProps<{
  hasAudio?: boolean
  mode?: 'direct' | 'socratic'
}>()

const emit = defineEmits<{
  (e: 'modeChange', mode: 'direct' | 'socratic'): void
}>()

const isPlaying = ref(false)
const isSpeaking = ref(false)
const progress = ref(0)
const currentTime = ref(0)
const duration = ref(60)
const subtitle = ref('')
const emotion = ref('default')

const mouthOpen = computed(() => {
  return isSpeaking.value ? 8 : 4
})

const mouthY = computed(() => {
  return isSpeaking.value ? 148 : 145
})

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const togglePlay = () => {
  isPlaying.value = !isPlaying.value
  isSpeaking.value = isPlaying.value
}

const seekTo = (value: number) => {
  currentTime.value = value
  progress.value = value
}

watch(() => props.mode, (newMode) => {
  if (newMode === 'socratic') {
    emotion.value = 'questioning'
  } else {
    emotion.value = 'explaining'
  }
})

const simulateSpeaking = () => {
  let count = 0
  const interval = setInterval(() => {
    if (isSpeaking.value) {
      isSpeaking.value = false
      setTimeout(() => {
        isSpeaking.value = true
      }, 100)
      count++
      if (count > 30) {
        clearInterval(interval)
        isSpeaking.value = false
        isPlaying.value = false
      }
    } else {
      clearInterval(interval)
    }
  }, 300)
}

watch(isPlaying, (playing) => {
  if (playing) {
    simulateSpeaking()
    emotion.value = props.mode === 'socratic' ? 'thinking' : 'explaining'
  } else {
    emotion.value = 'default'
  }
})

const mode = ref<'direct' | 'socratic'>(props.mode || 'direct')

watch(mode, (newMode) => {
  emit('modeChange', newMode)
})

defineExpose({
  isPlaying,
  play: () => { isPlaying.value = true },
  pause: () => { isPlaying.value = false },
  setSubtitle: (text: string) => { subtitle.value = text },
  setDuration: (d: number) => { duration.value = d },
})
</script>

<style scoped>
.digital-human-container {
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.dh-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.dh-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.dh-character {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 16px;
}

.dh-svg {
  width: 180px;
  height: 220px;
  transition: transform 0.3s ease;
}

.dh-character.speaking .dh-svg {
  animation: headBob 0.5s ease-in-out infinite;
}

@keyframes headBob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

.dh-mouth {
  transition: ry 0.15s ease, cy 0.15s ease;
}

.dh-emotion {
  position: absolute;
  top: -10px;
  right: 10px;
  font-size: 28px;
  animation: float 2s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

.dh-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 12px;
}

.dh-progress {
  flex: 1;
  max-width: 150px;
}

.dh-time {
  font-size: 12px;
  color: #666;
  min-width: 60px;
}

.dh-subtitle {
  background: rgba(0, 0, 0, 0.7);
  border-radius: 8px;
  padding: 10px 14px;
  margin-bottom: 12px;
}

.subtitle-text {
  color: #fff;
  font-size: 14px;
  text-align: center;
  line-height: 1.5;
}

.dh-mode-switch {
  display: flex;
  justify-content: center;
}
</style>
