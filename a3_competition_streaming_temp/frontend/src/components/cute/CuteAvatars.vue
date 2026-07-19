<template>
  <div class="blob-stage">
    <div class="blob" :class="blobClass">
      <div class="blob-inner"></div>
    </div>

    <div class="eyes" :class="eyesClass">
      <div class="eye e-left" :class="eyeClass">
        <span class="eyeball"></span>
      </div>
      <div class="eye e-right" :class="eyeClass">
        <span class="eyeball"></span>
      </div>
    </div>

    <div class="mouth" :class="mouthClass">
      <svg viewBox="0 0 40 22" width="40" height="22">
        <path v-if="mouthShape === 'line'"  d="M2 11 L38 11" stroke="#2a3ea8" stroke-width="2" stroke-linecap="round" fill="none"/>
        <path v-else-if="mouthShape === 'smile'" d="M3 5 Q 20 22 37 5" stroke="#2a3ea8" stroke-width="2.2" stroke-linecap="round" fill="none"/>
        <path v-else-if="mouthShape === 'open'" d="M5 2 Q 20 18 35 2 Q 20 6 5 2 Z" fill="#2a3ea8" opacity=".85"/>
        <path v-else-if="mouthShape === 'x'" d="M8 6 L32 16 M32 6 L8 16" stroke="#2a3ea8" stroke-width="2.2" stroke-linecap="round"/>
        <path v-else d="M3 11 Q 20 20 37 11" stroke="#2a3ea8" stroke-width="2" stroke-linecap="round" fill="none"/>
      </svg>
    </div>

    <div class="cookie">
      <svg viewBox="0 0 72 64" width="72" height="64">
        <defs>
          <radialGradient id="cookieBody" cx="50%" cy="55%" r="60%">
            <stop offset="0%"  stop-color="#f3d39a"/>
            <stop offset="55%" stop-color="#e4b46a"/>
            <stop offset="100%" stop-color="#b9823d"/>
          </radialGradient>
          <linearGradient id="choco" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#6b3a1a"/>
            <stop offset="100%" stop-color="#3d1e0a"/>
          </linearGradient>
        </defs>
        <path d="M36 4 A 28 26 0 0 1 64 30 Q 52 28, 52 34 T 40 34 Q 36 34 32 38 Q 28 42, 22 40 A 28 26 0 0 1 36 4 Z"
              fill="url(#cookieBody)" stroke="#6b3a1a" stroke-width="1.6" stroke-linejoin="round"/>
        <path d="M26 26 Q 22 34, 28 42 Q 34 38, 32 30 Q 30 24, 26 26 Z" fill="url(#choco)" opacity=".85"/>
        <path d="M44 22 Q 40 28, 44 34 Q 48 32, 48 24 Q 47 20, 44 22 Z" fill="url(#choco)" opacity=".85"/>
        <path d="M52 38 Q 48 44, 54 48 Q 58 44, 56 38 Z" fill="url(#choco)" opacity=".8"/>
        <circle cx="20" cy="22" r="2.2" fill="#ff8fb0"/>
        <circle cx="48" cy="14" r="1.8" fill="#9ae5a8"/>
        <circle cx="40" cy="46" r="2" fill="#ffc9a0"/>
        <circle cx="60" cy="30" r="1.6" fill="#ffb3c9"/>
        <circle cx="16" cy="36" r="1.5" fill="#b2f0c8"/>
      </svg>
    </div>

    <div class="blob-trail trail-1"></div>
    <div class="blob-trail trail-2"></div>

    <div class="tags">
      <span class="tag t-main">AI · CORE</span>
      <span class="t-dots"><i></i><i></i><i></i></span>
      <span class="t-sub">NEURONS 128k · live</span>
    </div>

    <div class="stat-row">
      <span class="st"><em class="sd"></em> inference · streaming</span>
      <span class="st"><em class="sd ok"></em> latency · 12ms</span>
    </div>

    <div class="blob-caption">
      <h2>青藜伴读</h2>
      <p>AI 驱动的学习决策与<br>苏格拉底式辅导系统</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

type AIState = 'idle' | 'focus' | 'thinking' | 'learning' | 'reviewing' | 'processing' | 'success' | 'error'
type MouthShape = 'line' | 'smile' | 'open' | 'x' | 'neutral'

const props = defineProps<{
  glowOn?: boolean
  active?: boolean
  pwFocused?: boolean
  pwLength?: number
  state?: AIState
}>()

const blinking = ref(false)
let blinkTimer: number | null = null

function scheduleBlink() {
  const s = props.state || 'idle'
  let interval = 4000 + Math.random() * 4000
  if (s === 'thinking' || s === 'processing') interval = 1500 + Math.random() * 1500
  else if (s === 'reviewing') interval = 6000 + Math.random() * 3000
  else if (props.pwFocused) interval = 99999
  blinkTimer = window.setTimeout(() => {
    blinking.value = true
    window.setTimeout(() => { blinking.value = false; scheduleBlink() }, 130)
  }, interval)
}

onMounted(() => { scheduleBlink() })
onUnmounted(() => { if (blinkTimer) clearTimeout(blinkTimer) })
watch(() => props.pwFocused, (v) => { if (!v) scheduleBlink() })

const state = computed<AIState>(() => props.state || 'idle')

const pwPeeking = computed(() =>
  props.pwFocused && (props.pwLength ?? 0) > 6
)

const blobClass = computed(() => ({
  active: true,
  racing: state.value === 'processing' || state.value === 'thinking',
  happy:  state.value === 'success',
  oops:   state.value === 'error',
}))

const eyesClass = computed(() => ({
  'pw-eyes': props.pwFocused && !pwPeeking.value,
  'peeking': pwPeeking.value,
  'blink': blinking.value && !props.pwFocused,
  'success': state.value === 'success' && !props.pwFocused,
  'error': state.value === 'error' && !props.pwFocused,
  'focused': state.value === 'focus' && !props.pwFocused,
  'thinking': state.value === 'thinking' && !props.pwFocused,
  'processing': state.value === 'processing' && !props.pwFocused,
  'learning': state.value === 'learning' && !props.pwFocused,
}))

const eyeClass = computed(() => ({
  closed: props.pwFocused && !pwPeeking.value,
  squint: pwPeeking.value,
  happy: state.value === 'success',
  shake: state.value === 'error',
}))

const mouthShape = computed<MouthShape>(() => {
  if (props.pwFocused) return 'line'
  switch (state.value) {
    case 'success':   return 'smile'
    case 'error':     return 'x'
    case 'processing':return 'open'
    case 'thinking':  return 'neutral'
    case 'learning':  return 'open'
    default:          return 'neutral'
  }
})

const mouthClass = computed(() => ({
  happy: state.value === 'success' && !props.pwFocused,
  oops:  state.value === 'error' && !props.pwFocused,
  open:  (state.value === 'processing' || state.value === 'learning') && !props.pwFocused,
}))
</script>

<style scoped>
.blob-stage{position:relative;width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;user-select:none;pointer-events:none}

.blob{position:relative;width:320px;height:320px;top:50%;left:50%;transform:translate(-50%,-50%);margin-top:-30px;border-radius:60% 40% 30% 70%/60% 30% 70% 40%;background:radial-gradient(circle at 28% 28%,#14b8a6 0%,#14b8a6 55%,#5b84e8 100%);box-shadow:0 0 50px rgba(123,168,255,.45),0 0 120px rgba(91,132,232,.22),inset 0 0 40px rgba(255,255,255,.35),inset 0 -20px 60px rgba(40,60,140,.2);animation:blobFloat 6s ease-in-out infinite;overflow:hidden}
.blob.happy{background:radial-gradient(circle at 30% 30%,#ffd99a 0%,#ffb67a 55%,#ff8c5a 100%);box-shadow:0 0 50px rgba(255,160,100,.45),0 0 120px rgba(255,120,80,.22);animation:blobBounce 1.2s ease-in-out infinite}
.blob.oops{background:radial-gradient(circle at 30% 30%,#ff98aa 0%,#e6789a 55%,#b84a70 100%);box-shadow:0 0 50px rgba(230,120,154,.45),0 0 120px rgba(184,74,112,.22)}
.blob.racing{animation:blobFloat 2.2s ease-in-out infinite}
.blob-inner{position:absolute;inset:18%;border-radius:60% 40% 30% 70%/60% 30% 70% 40%;background:radial-gradient(circle at 60% 55%,rgba(255,255,255,.85),rgba(255,255,255,0) 60%);mix-blend-mode:screen;animation:blobFloat 6s ease-in-out infinite reverse;pointer-events:none}

.eyes{position:absolute;top:calc(50% - 24px);left:50%;transform:translate(-50%,0);width:118px;display:flex;justify-content:space-between;z-index:10}

.eye{position:relative;width:34px;height:30px;background:none;transition:transform .3s cubic-bezier(.2,.9,.2,1);animation:eyeIdle 7s ease-in-out infinite}
.eye.e-right{animation-delay:.7s}
@keyframes eyeIdle{0%,100%{transform:translateY(0)}50%{transform:translateY(-1px)}}

.eyeball{position:absolute;left:0;top:0;width:100%;height:100%;border-radius:50% 50% 0 0/60% 60% 0 0;background:#2a3ea8;box-shadow:0 2px 6px rgba(30,50,160,.35);transition:opacity .25s ease}

.pw-eyes .eyeball,.eye.closed .eyeball{height:2px;border-radius:2px;background:#2a3ea8;box-shadow:none}

.peeking .eyeball{height:10px;border-radius:50% 50% 0 0/60% 60% 0 0;background:#2a3ea8}

.blink .eyeball{height:2px;border-radius:2px;background:#2a3ea8;box-shadow:none}

.success .eyeball{width:100%;height:14px;border-radius:50% 50% 0 0/60% 60% 0 0;background:linear-gradient(180deg,#ffa264,#c56428)}

.error .eyeball{background:#2a3ea8;transform:rotate(-6deg)}
.error.e-right .eyeball{transform:rotate(6deg)}
.error{animation:eyeShake .5s ease-in-out infinite}
@keyframes eyeShake{0%,100%{transform:translateX(0) rotate(-1deg)}50%{transform:translateX(0) rotate(1deg)}}

.thinking .eyeball{animation:thinkEye 2.6s ease-in-out infinite}
@keyframes thinkEye{0%,100%{transform:translateX(0)}50%{transform:translateX(1px)}}
.processing .eyeball{animation:scanEye 1.2s ease-in-out infinite}
@keyframes scanEye{0%,100%{transform:translateX(0)}50%{transform:translateX(2px)}}

.mouth{position:absolute;top:calc(50% + 44px);left:50%;transform:translateX(-50%);z-index:10;filter:drop-shadow(0 1px 2px rgba(42,62,168,.18));animation:mouthIdle 6s ease-in-out infinite}
@keyframes mouthIdle{0%,100%{transform:translateX(-50%) scaleY(1)}50%{transform:translateX(-50%) scaleY(1.05)}}
.mouth.happy{animation:mouthHappy 2.2s ease-in-out infinite}
@keyframes mouthHappy{0%,100%{transform:translateX(-50%) scaleY(1)}50%{transform:translateX(-50%) scaleY(1.12)}}
.mouth.open{animation:mouthOpen 1.2s ease-in-out infinite}
@keyframes mouthOpen{0%,100%{transform:translateX(-50%) scaleY(1)}50%{transform:translateX(-50%) scaleY(1.08)}}
.mouth.oops{animation:mouthOops 1.5s ease-in-out infinite}
@keyframes mouthOops{0%,100%{transform:translateX(-50%) rotate(0)}25%{transform:translateX(-50%) rotate(-2deg)}75%{transform:translateX(-50%) rotate(2deg)}}

.cookie{position:absolute;top:calc(50% + 76px);left:50%;transform:translateX(-50%);width:72px;height:64px;z-index:10;animation:cookieFloat 5.5s ease-in-out infinite;filter:drop-shadow(0 3px 8px rgba(80,40,20,.35))}
@keyframes cookieFloat{0%,100%{transform:translateX(-50%) translateY(0)}50%{transform:translateX(-50%) translateY(-4px)}}

.blob-trail{position:absolute;width:420px;height:420px;border-radius:50%;filter:blur(40px);opacity:.3;animation:trailPulse 7s ease-in-out infinite;pointer-events:none}
.trail-1{background:radial-gradient(circle,#14b8a6,transparent 60%);top:25%;left:25%}
.trail-2{background:radial-gradient(circle,#14b8a6,transparent 60%);bottom:15%;right:20%;animation-delay:2s}
@keyframes trailPulse{0%,100%{opacity:.18;transform:scale(1)}50%{opacity:.4;transform:scale(1.08)}}

@keyframes blobFloat{0%{transform:translate(-50%,-50%) scale(1);border-radius:60% 40% 30% 70%/60% 30% 70% 40%}50%{transform:translate(-50%,-52%) scale(1.05);border-radius:30% 60% 70% 40%/50% 60% 30% 60%}100%{transform:translate(-50%,-50%) scale(1);border-radius:60% 40% 30% 70%/60% 30% 70% 40%}}
@keyframes blobBounce{0%,100%{transform:translate(-50%,-50%) scale(1)}50%{transform:translate(-50%,-46%) scale(1.08)}}

.tags{display:inline-flex;align-items:center;gap:8px;padding:4px 12px;background:rgba(20,35,80,.6);border:1px solid rgba(150,195,255,.35);border-radius:999px;backdrop-filter:blur(10px);font-family:ui-monospace,monospace;font-size:11px;letter-spacing:2.5px;z-index:3}
.t-main{color:#14b8a6;font-weight:700}.t-sub{color:#7a94d0;font-weight:500;font-size:10px}
.t-dots{display:inline-flex;gap:3px;align-items:center}
.t-dots i{width:4px;height:4px;border-radius:50%;background:#14b8a6;box-shadow:0 0 6px rgba(123,168,255,.7);animation:dotPulse 1.6s ease-in-out infinite}
.t-dots i:nth-child(2){animation-delay:.25s}.t-dots i:nth-child(3){animation-delay:.5s}
@keyframes dotPulse{0%,100%{opacity:.4;transform:scale(.7)}50%{opacity:1;transform:scale(1.1)}}

.stat-row{display:flex;gap:16px;font-family:ui-monospace,monospace;font-size:10px;letter-spacing:1px;color:#7a94d0;z-index:3}
.st{display:inline-flex;align-items:center;gap:5px}
.sd{width:5px;height:5px;border-radius:50%;background:#14b8a6;opacity:.7}.sd.ok{background:#8fe0b0;box-shadow:0 0 6px rgba(143,224,176,.7)}

.blob-caption{text-align:center;margin-top:14px;z-index:3}
.blob-caption h2{margin:0;font-size:20px;font-weight:800;letter-spacing:3px;background:linear-gradient(90deg,#14b8a6,#0d9488);-webkit-background-clip:text;background-clip:text;color:transparent}
.blob-caption p{margin:6px 0 0;font-size:11px;color:#6a80b5;letter-spacing:1px;line-height:1.6}

@media (max-width: 820px) { .blob-stage{display:none} }
</style>
