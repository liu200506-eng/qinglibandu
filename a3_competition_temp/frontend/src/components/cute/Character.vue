<template>
  <div class="character"
    :class="[
      roleClass,
      {
        inputing, peeking, cheering, shaking,
        blinking, happySquint, focus, thinking, processing,
      }
    ]">
    <div class="ears">
      <span class="ear ear-l"></span>
      <span class="ear ear-r"></span>
    </div>
    <div class="antenna"><span></span></div>
    <div class="body">
      <div class="head">
        <div class="face">
          <div class="eyes">
            <span class="eye eye-l">
              <span class="eyelid top"></span>
              <span class="eyelid bottom"></span>
              <span class="sclera"></span>
              <span class="iris" :style="irisTransformLeft"></span>
              <span class="glint"></span>
            </span>
            <span class="eye eye-r">
              <span class="eyelid top"></span>
              <span class="eyelid bottom"></span>
              <span class="sclera"></span>
              <span class="iris" :style="irisTransformRight"></span>
              <span class="glint"></span>
            </span>
          </div>
          <div class="cheek cheek-l"></div>
          <div class="cheek cheek-r"></div>
          <div class="mouth"><span></span></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

type Role = 'A' | 'B' | 'C'
type AIState = 'idle' | 'focus' | 'thinking' | 'learning' | 'reviewing' | 'processing' | 'success' | 'error'

const props = defineProps<{
  role?: Role
  blink?: boolean
  lookingAt?: { x: number; y: number }
  peeking?: boolean
  inputing?: boolean
  cheer?: boolean
  shake?: boolean
  state?: AIState
}>()

const mouseX = ref(window.innerWidth / 2)
const mouseY = ref(window.innerHeight / 2)
const doBlink = ref(false)
let blinkTimer: number | null = null

function onMove(e: MouseEvent) { mouseX.value = e.clientX; mouseY.value = e.clientY }
function scheduleBlink() {
  const s = props.state || 'idle'
  let interval = 4000 + Math.random() * 4000
  if (s === 'thinking' || s === 'processing') interval = 1500 + Math.random() * 1500
  else if (s === 'reviewing') interval = 7000 + Math.random() * 3000
  blinkTimer = window.setTimeout(() => {
    doBlink.value = true
    window.setTimeout(() => { doBlink.value = false; scheduleBlink() }, 110)
  }, interval)
}

onMounted(() => { window.addEventListener('mousemove', onMove); scheduleBlink() })
onUnmounted(() => {
  window.removeEventListener('mousemove', onMove)
  if (blinkTimer) clearTimeout(blinkTimer)
})
watch(() => props.state, () => { if (!doBlink.value) scheduleBlink() })

const centerX = computed(() => window.innerWidth / 2)
const centerY = computed(() => window.innerHeight / 2)
const dx = computed(() => Math.max(-4, Math.min(4, (mouseX.value - centerX.value) / centerX.value * 4)))
const dy = computed(() => Math.max(-3, Math.min(3, (mouseY.value - centerY.value) / centerY.value * 3)))

const irisTransformLeft = computed(() => {
  if (props.peeking) return 'translate(0,-.5px)'
  return `translate(${dx.value}px, ${dy.value}px)`
})
const irisTransformRight = computed(() => {
  if (props.peeking) return 'translate(0,-.5px)'
  return `translate(${(dx.value + 0.6).toFixed(2)}px, ${(dy.value - 0.3).toFixed(2)}px)`
})

const roleClass = computed(() => `role-${(props.role || 'A').toLowerCase()}`)
const blinking = computed(() => doBlink.value || props.blink)
const happySquint = computed(() => !!props.cheer || props.state === 'success')
const cheering = computed(() => !!props.cheer)
const shaking = computed(() => !!props.shake)
const focus = computed(() => props.state === 'focus')
const thinking = computed(() => props.state === 'thinking')
const processing = computed(() => props.state === 'processing')
</script>

<style scoped>
.character{position:relative;width:120px;height:140px;display:inline-block;vertical-align:middle}
.body{position:absolute;left:50%;bottom:0;transform:translateX(-50%);width:100px;height:92px;border-radius:50% 50% 45% 45%/55% 55% 45% 45%;background:var(--role-body,#e6a9ff);box-shadow:0 8px 24px rgba(120,80,160,.25);z-index:1}
.head{position:absolute;left:50%;top:4px;transform:translateX(-50%);width:92px;height:78px;border-radius:50% 50% 46% 46%/55% 55% 45% 45%;background:var(--role-body,#e6a9ff);box-shadow:inset -6px -6px 14px rgba(0,0,0,.08)}
.face{position:absolute;inset:10px 8px 4px 8px}

.role-a{--role-body:#e6a9ff;--role-inner:#b88cff;--role-ear:#c8a4ff}
.role-b{--role-body:#9ec7ff;--role-inner:#6fa8ff;--role-ear:#bdd7ff}
.role-c{--role-body:#ffcc8e;--role-inner:#ffa95a;--role-ear:#ffd9a8}

.eyes{display:flex;justify-content:space-between;padding:10px 4px 0}
.eye{position:relative;width:28px;height:28px;border-radius:50%;background:rgba(255,255,255,.95);display:flex;align-items:center;justify-content:center;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.12)}
.eyelid{position:absolute;left:0;right:0;height:50%;background:rgba(10,14,30,.92);transition:transform .4s cubic-bezier(.2,.8,.2,1),opacity .2s ease;opacity:0}
.eyelid.top{top:0;transform-origin:top center;transform:scaleY(.02)}
.eyelid.bottom{bottom:0;transform-origin:bottom center;transform:scaleY(.02)}
.eye.blink .eyelid.top,.character.blinking .eyelid.top{transform:scaleY(1);opacity:1}
.eye.blink .eyelid.bottom,.character.blinking .eyelid.bottom{transform:scaleY(1);opacity:1}

.character.happy-squint .eyelid.top{transform:scaleY(.55) scaleX(1.05);opacity:1}
.character.happy-squint .eyelid.bottom{transform:scaleY(.05);opacity:.3}
.character.happy-squint .eye{border-radius:3px 3px 12px 12px/6px 6px 12px 12px;box-shadow:none;background:rgba(255,255,255,.3)}

.character.shaking{animation:shakeB .5s ease-in-out infinite}
@keyframes shakeB{0%,100%{transform:translateX(0) rotate(-2deg)}50%{transform:translateX(0) rotate(2deg)}}

.character.focus .eye{transform:scaleY(.95) scaleX(1.03)}
.character.focus .iris{transform:translate(0,0) scale(1.05)}

.character.processing .iris{width:50%;height:50%}

.character.thinking .iris{animation:thinkEye 1.3s ease-in-out infinite}
@keyframes thinkEye{0%{transform:translate(-2px,-2px)}25%{transform:translate(2px,-2px)}50%{transform:translate(2px,2px)}75%{transform:translate(-2px,2px)}100%{transform:translate(-2px,-2px)}}

.sclera{position:absolute;inset:0;border-radius:50%}
.iris{position:absolute;width:66%;height:66%;border-radius:50%;background:radial-gradient(circle at 65% 65%,#0a0d1a 0%,#1a1e40 80%);transition:transform .12s cubic-bezier(.2,.8,.3,1);will-change:transform}
.glint{position:absolute;top:3px;left:4px;width:5px;height:5px;border-radius:50%;background:rgba(255,255,255,.92);filter:blur(.3px);pointer-events:none;z-index:2}

.character.peeking .eyelid.top{transform:scaleY(.8);opacity:.9}
.character.peeking .eyelid.bottom{transform:scaleY(.15);opacity:.5}
.character.peeking .eye{border-radius:5px 5px 10px 10px/4px 4px 12px 12px}

.cheek{position:absolute;width:14px;height:10px;border-radius:50%;background:rgba(255,140,170,.5);opacity:.85}
.cheek-l{left:-2px;bottom:14px}.cheek-r{right:-2px;bottom:14px}

.mouth{position:absolute;left:50%;bottom:6px;transform:translateX(-50%);width:14px;height:6px;border-radius:0 0 14px 14px;background:#3a1f3a;overflow:hidden}
.mouth span{position:absolute;inset:1px;border-radius:inherit;background:#ff5c8a}
.character.inputing .mouth{width:10px;height:4px;border-radius:0 0 10px 10px;background:#3a1f3a}
.character.inputing .mouth span{animation:whoop .35s ease-in-out infinite}
@keyframes whoop{0%,100%{transform:scaleY(.8)}50%{transform:scaleY(1.1)}}
.character.cheering .mouth{width:20px;height:10px;border-radius:0 0 20px 20px;background:#3a1f3a}
.character.cheering .mouth span{background:linear-gradient(180deg,#ff5c8a,#ff3e70)}
.character.happy-squint .mouth{width:16px;height:6px;border-radius:0 0 16px 16px;background:#3a1f3a}

.ears{position:absolute;top:-2px;left:0;right:0;display:flex;justify-content:space-between;pointer-events:none;z-index:-1}
.ear{width:18px;height:22px;background:var(--role-ear,#c8a4ff);border-radius:50% 50% 20% 20%}
.ear-l{transform:rotate(-20deg)}.ear-r{transform:rotate(20deg)}

.antenna{position:absolute;top:-12px;left:50%;transform:translateX(-50%);width:3px;height:12px;background:var(--role-inner,#b88cff);z-index:2}
.antenna span{position:absolute;top:-2px;left:-5px;width:12px;height:12px;border-radius:50%;background:var(--role-inner,#b88cff);animation:antennaPulse 1.8s ease-in-out infinite}
@keyframes antennaPulse{0%,100%{transform:scale(.7);opacity:.7}50%{transform:scale(1.1);opacity:1}}
</style>
