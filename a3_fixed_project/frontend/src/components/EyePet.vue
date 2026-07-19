<template>
  <div class="eye-pet" :class="eyeClass">
    <div class="face">
      <div class="face-ring"></div>
      <div class="eyes">
        <span class="eye left" :class="{ closed: eyeState === 'blink' }"></span>
        <span class="eye right" :class="{ closed: eyeState === 'blink' }"></span>
      </div>
      <div class="mouth" :class="mouthClass"></div>
    </div>
    <div class="bubble">
      <span class="bbl-t">{{ eyeText }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'

const props = defineProps<{
  showPassword?: boolean
  mode?: 'idle' | 'input' | 'password' | 'success' | 'error'
}>()

const eyeState = ref<'idle' | 'blink' | 'peek' | 'happy'>('idle')
let blinkTimer: number | null = null

function scheduleBlink() {
  if (blinkTimer) window.clearTimeout(blinkTimer)
  const delay = 3000 + Math.random() * 3500
  blinkTimer = window.setTimeout(() => {
    if (props.mode !== 'password' && !props.showPassword) eyeState.value = 'blink'
    setTimeout(() => {
      if (eyeState.value === 'blink') {
        if (props.mode === 'password' || props.showPassword) eyeState.value = 'peek'
        else if (props.mode === 'success') eyeState.value = 'happy'
        else eyeState.value = 'idle'
      }
    }, 150)
    scheduleBlink()
  }, delay)
}

watch([() => props.mode, () => props.showPassword], () => {
  if (props.mode === 'success') eyeState.value = 'happy'
  else if (props.mode === 'password' || props.showPassword) eyeState.value = 'peek'
  else if (eyeState.value !== 'blink') eyeState.value = 'idle'
}, { immediate: true })

const eyeClass = computed(() => ({
  peek: eyeState.value === 'peek',
  happy: eyeState.value === 'happy',
  blink: eyeState.value === 'blink'
}))

const mouthClass = computed(() => ({
  smile: eyeState.value === 'happy',
  shy: eyeState.value === 'peek',
  neutral: eyeState.value === 'idle' || eyeState.value === 'blink'
}))

const eyeText = computed(() => {
  if (eyeState.value === 'peek') return '我在帮你挡着 👀'
  if (eyeState.value === 'happy') return '登录成功！✓'
  if (eyeState.value === 'blink') return '…'
  return '待命 👁'
})

onMounted(() => scheduleBlink())
onUnmounted(() => { if (blinkTimer) window.clearTimeout(blinkTimer) })
</script>

<style scoped>
.eye-pet {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 10px 5px 6px;
  background: rgba(10, 14, 30, .72);
  border: 1px solid rgba(124, 140, 255, .25);
  border-radius: 14px;
  backdrop-filter: blur(8px);
  vertical-align: middle;
  animation: petPop .4s ease-out both;
}
@keyframes petPop {
  from { opacity: 0; transform: scale(.85); }
  to { opacity: 1; transform: scale(1); }
}

.face {
  position: relative;
  width: 34px; height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.face-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: radial-gradient(circle at 50% 45%, #8a9dff 0%, #4f6fd8 70%, #2a3a90 100%);
  box-shadow: 0 0 14px rgba(124,140,255,.5), inset 0 0 8px rgba(0,0,0,.3);
}
.eyes {
  position: relative;
  display: flex;
  gap: 5px;
  z-index: 2;
  align-items: center;
  margin-top: -2px;
}
.eye {
  width: 6px; height: 8px;
  background: #f3f6ff;
  border-radius: 50%;
  box-shadow: 0 0 3px rgba(255,255,255,.8);
  transform-origin: center center;
  transition: transform .12s ease, height .12s ease, opacity .12s ease;
}
.eye.closed {
  height: 1.2px;
  border-radius: 1px;
  box-shadow: 0 0 2px rgba(255,255,255,.3);
}
.eye.left { transform: translateX(-1px); }
.eye.right { transform: translateX(1px); }

.mouth {
  position: absolute;
  bottom: 7px;
  left: 50%;
  transform: translateX(-50%);
  width: 9px;
  height: 2px;
  border-radius: 50%;
  background: rgba(255,255,255,.8);
  transition: all .2s ease;
  z-index: 2;
}
.mouth.smile {
  width: 10px;
  height: 4px;
  border-radius: 50% 50% 50% 50% / 20% 20% 80% 80%;
  background: rgba(255,255,255,.95);
}
.mouth.shy {
  width: 7px;
  height: 1.5px;
  background: rgba(255,230,230,.65);
}

.bubble {
  display: inline-block;
  max-width: 110px;
  padding: 2px 8px;
  background: rgba(18, 24, 48, .8);
  border: 1px solid rgba(124, 140, 255, .25);
  border-radius: 8px;
  backdrop-filter: blur(6px);
}
.bbl-t {
  display: block;
  font-size: 10px;
  color: #c0ccf0;
  letter-spacing: .4px;
  font-weight: 500;
  line-height: 1.2;
  white-space: nowrap;
}

@media (max-width: 480px) {
  .bubble { display: none; }
}
</style>
