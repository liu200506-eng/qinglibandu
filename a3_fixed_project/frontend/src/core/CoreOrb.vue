<template>
  <div class="orb-wrap" :class="ai.state">
    <div class="orb-glow"></div>
    <div class="orb-glow-2"></div>

    <div class="orb-core">
      <div class="orb-face">
        <span class="eye" :class="{ peek: peek, blink: blinking }">
          <span class="pupil"></span>
          <span class="pupil-ring"></span>
        </span>
        <span class="eye" :class="{ peek: peek, blink: blinking }">
          <span class="pupil"></span>
          <span class="pupil-ring"></span>
        </span>
        <span class="mouth" :class="mouthClass"></span>
      </div>

      <div class="orb-ring ring-1"></div>
      <div class="orb-ring ring-2"></div>
      <div class="orb-ring ring-3"></div>
    </div>

    <div class="orb-trail t-a"></div>
    <div class="orb-trail t-b"></div>

    <div class="orb-status">
      <span class="status-dot" :class="ai.energyLevel"></span>
      <span class="status-label">{{ statusLabel }}</span>
    </div>

    <div class="orb-energy">
      <div class="energy-bar"><div class="energy-fill" :style="{ width: ai.energy * 100 + '%' }"></div></div>
      <span class="energy-text">ENERGY · {{ Math.round(ai.energy * 100) }}%</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useAIStore } from '@/stores/ai'

const ai = useAIStore()

const blinking = ref(false)
let blinkTimer: number | null = null
let autoBlink: number | null = null

const statusLabel = computed(() => {
  const base = ai.statusLabel
  if (ai.state === 'thinking')  return `🧠 ${base}…`
  if (ai.state === 'processing') return `⚡ ${base}…`
  if (ai.state === 'success')   return `✨ ${base}`
  if (ai.state === 'error')     return `⚠️ ${base}`
  return base
})

const peek = computed(() => ai.state === 'focus' || ai.state === 'processing')

const mouthClass = computed(() => {
  if (ai.state === 'success') return 'smile'
  if (ai.state === 'error')   return 'worried'
  if (ai.state === 'thinking') return 'small-o'
  if (ai.state === 'focus')    return 'neutral'
  return 'neutral'
})

function scheduleBlink() {
  if (blinkTimer) clearTimeout(blinkTimer)
  const wait = 2800 + Math.random() * 3500
  blinkTimer = window.setTimeout(() => {
    blinking.value = true
    autoBlink = window.setTimeout(() => {
      blinking.value = false
      scheduleBlink()
    }, 180)
  }, wait)
}

onMounted(() => {
  scheduleBlink()
})
onUnmounted(() => {
  if (blinkTimer) clearTimeout(blinkTimer)
  if (autoBlink) clearTimeout(autoBlink)
})
</script>

<style scoped>
.orb-wrap {
  position: relative;
  width: 320px;
  height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  transform-origin: center;
  transition: transform .6s var(--ease-spring), filter .6s ease;
}

.orb-wrap.idle     { animation: idleFloat 6s var(--ease-breath) infinite; }
.orb-wrap.focus    { transform: scale(1.08); filter: brightness(1.15); }
.orb-wrap.thinking { animation: pulse .8s ease-in-out infinite; }
.orb-wrap.processing { animation: warpPulse .9s ease-in-out infinite; }
.orb-wrap.success  { animation: successPulse 1.2s ease; }
.orb-wrap.error    { animation: errorShake .5s ease-in-out; }

.orb-glow, .orb-glow-2 {
  position: absolute;
  inset: -30%;
  border-radius: 50%;
  filter: blur(30px);
  pointer-events: none;
}
.orb-glow {
  background: radial-gradient(circle, rgba(108,92,231,.55), rgba(108,92,231,0) 60%);
  animation: glowFloat 6s var(--ease-breath) infinite;
}
.orb-glow-2 {
  background: radial-gradient(circle, rgba(0,210,255,.35), rgba(0,210,255,0) 60%);
  animation: glowFloat 6s var(--ease-breath) infinite reverse;
  animation-delay: 2s;
}

.orb-core {
  position: relative;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, #6C5CE7 0%, #00D2FF 100%);
  box-shadow:
    0 0 60px rgba(108,92,231,0.5),
    0 0 120px rgba(0,210,255,0.25),
    inset 0 0 40px rgba(255,255,255,0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.orb-face {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 26px;
  z-index: 2;
}

.eye {
  position: relative;
  width: 22px;
  height: 26px;
  background: rgba(255,255,255,.95);
  border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
  transition: transform .25s ease, height .14s ease;
  box-shadow: 0 0 10px rgba(0,0,0,.15);
}
.eye .pupil {
  position: absolute;
  width: 10px;
  height: 10px;
  left: 50%; top: 55%;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, #1a1a2a, #6c5ce7);
  border-radius: 50%;
  transition: transform .25s ease;
}
.eye .pupil-ring {
  position: absolute;
  inset: -2px;
  border-radius: 50%;
  border: 1px dashed rgba(0,0,0,.15);
  animation: pupilOrbit 4s linear infinite;
}
.eye.blink { height: 2px; }
.eye.peek .pupil { transform: translate(-40%, -50%); }

.mouth {
  position: absolute;
  bottom: -26px;
  left: 50%;
  transform: translateX(-50%);
  width: 28px;
  height: 3px;
  background: rgba(0,0,0,.55);
  border-radius: 2px;
  transition: all .25s ease;
}
.mouth.smile {
  height: 12px;
  background: transparent;
  border-radius: 0;
  border-bottom: 3px solid rgba(255,255,255,.9);
}
.mouth.worried {
  height: 12px;
  background: transparent;
  border-radius: 0;
  border-top: 3px solid rgba(255,255,255,.9);
}
.mouth.small-o {
  width: 8px; height: 8px;
  background: rgba(0,0,0,.55);
  border-radius: 50%;
}

.orb-ring {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}
.ring-1 {
  inset: -14px;
  border: 1px dashed rgba(255,255,255,.35);
  animation: ringRot 14s linear infinite;
}
.ring-2 {
  inset: 14px;
  border: 1px solid rgba(255,255,255,.2);
  animation: ringRot 8s linear infinite reverse;
}
.ring-3 {
  inset: 40px;
  border: 1px dotted rgba(255,255,255,.12);
  animation: ringRot 20s linear infinite;
}

.orb-trail {
  position: absolute;
  width: 320px; height: 320px;
  border-radius: 50%;
  filter: blur(40px);
  opacity: .25;
  pointer-events: none;
}
.t-a { background: radial-gradient(circle, #6C5CE7, transparent 60%); top: -40px; left: -40px; }
.t-b { background: radial-gradient(circle, #00D2FF, transparent 60%); bottom: -40px; right: -40px; animation-delay: 2s; }

.orb-status {
  position: absolute;
  bottom: 26px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  background: rgba(10,14,30,.75);
  border: 1px solid rgba(180,195,255,.3);
  border-radius: 999px;
  font-family: ui-monospace, monospace;
  font-size: 11px;
  letter-spacing: 2px;
  backdrop-filter: blur(8px);
  z-index: 3;
}
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: #60ffb0; box-shadow: 0 0 8px rgba(96,255,176,.8); }
.status-dot.high { background: #60ffb0; }
.status-dot.mid  { background: #ffb860; }
.status-dot.low  { background: #ff6f8c; }
.status-label { color: #c0c9f0; font-weight: 600; }

.orb-energy {
  position: absolute;
  top: 26px;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 4px 12px;
  background: rgba(10,14,30,.75);
  border: 1px solid rgba(180,195,255,.3);
  border-radius: 999px;
  font-family: ui-monospace, monospace;
  font-size: 10px;
  letter-spacing: 1.5px;
  backdrop-filter: blur(8px);
  z-index: 3;
}
.energy-bar { width: 80px; height: 5px; background: rgba(255,255,255,.1); border-radius: 999px; overflow: hidden; }
.energy-fill { height: 100%; background: linear-gradient(90deg, #6C5CE7, #00D2FF, #60ffb0); transition: width .4s ease; }
.energy-text { color: #0d9488; }

@keyframes idleFloat {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(-10px); }
}
@keyframes pulse {
  0%, 100% { filter: brightness(1) saturate(1); }
  50%      { filter: brightness(1.25) saturate(1.5); }
}
@keyframes warpPulse {
  0%, 100% { transform: scale(1); }
  50%      { transform: scale(1.06) rotate(1.5deg); }
}
@keyframes successPulse {
  0%   { filter: drop-shadow(0 0 10px #60ffb0); transform: scale(1); }
  50%  { filter: drop-shadow(0 0 40px #60ffb0); transform: scale(1.1); }
  100% { filter: drop-shadow(0 0 10px #60ffb0); transform: scale(1); }
}
@keyframes errorShake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-8px); }
  50% { transform: translateX(8px); }
  75% { transform: translateX(-4px); }
}
@keyframes glowFloat {
  0%, 100% { opacity: .3; transform: scale(1); }
  50%      { opacity: .6; transform: scale(1.06); }
}
@keyframes ringRot {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
@keyframes pupilOrbit {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
</style>
