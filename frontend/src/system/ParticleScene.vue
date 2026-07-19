<template>
  <div ref="mountRef" class="particle-scene"></div>
  <div v-if="warping" class="warp-flash"></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as THREE from 'three'

const mountRef = ref<HTMLDivElement>()
const warping = ref(false)
const emit = defineEmits<{ (e: 'warp-done'): void }>()

let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let points: THREE.Points | null = null
let geometry: THREE.BufferGeometry | null = null
let rafId: number | null = null

const PARTICLE_COUNT = 600
const BASE_FOV = 60
let basePositions: Float32Array | null = null
let baseColors: Float32Array | null = null

let breath = 0
let breathTarget = 0.5
let warpFactor = 0
let targetWarp = 0
let burstFactor = 0

function init() {
  if (!mountRef.value) return
  const w = window.innerWidth
  const h = window.innerHeight

  scene = new THREE.Scene()
  scene.background = null
  scene.fog = new THREE.FogExp2('#05060a', 0.008)

  camera = new THREE.PerspectiveCamera(BASE_FOV, w / h, 0.1, 2000)
  camera.position.set(0, 0, 38)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(w, h)
  renderer.setClearColor(0x000000, 0)
  mountRef.value.appendChild(renderer.domElement)

  const positions = new Float32Array(PARTICLE_COUNT * 3)
  const colors = new Float32Array(PARTICLE_COUNT * 3)
  const sizes = new Float32Array(PARTICLE_COUNT)

  let seed = Date.now() & 0xffff
  const rnd = () => { seed = (seed * 9301 + 49297) % 233280; return seed / 233280 }

  for (let i = 0; i < PARTICLE_COUNT; i++) {
    const i3 = i * 3
    const r = 14 + rnd() * 34
    const theta = rnd() * Math.PI * 2
    const phi = Math.acos(2 * rnd() - 1)
    positions[i3]     = r * Math.sin(phi) * Math.cos(theta)
    positions[i3 + 1] = r * Math.sin(phi) * Math.sin(theta)
    positions[i3 + 2] = r * Math.cos(phi)

    const palette = rnd()
    let c: THREE.Color
    if (palette < 0.55) c = new THREE.Color('#7c8cff')
    else if (palette < 0.8) c = new THREE.Color('#4f7cff')
    else if (palette < 0.92) c = new THREE.Color('#7c4dff')
    else c = new THREE.Color('#40c4ff')
    const br = 0.35 + rnd() * 0.4
    colors[i3] = c.r * br; colors[i3 + 1] = c.g * br; colors[i3 + 2] = c.b * br
    sizes[i] = 0.3 + rnd() * 1.6
  }

  basePositions = new Float32Array(positions)
  baseColors = new Float32Array(colors)

  geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
  geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1))

  const canvas = document.createElement('canvas')
  canvas.width = 64; canvas.height = 64
  const ctx = canvas.getContext('2d')!
  const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32)
  g.addColorStop(0, 'rgba(255,255,255,0.9)')
  g.addColorStop(0.3, 'rgba(255,255,255,0.45)')
  g.addColorStop(0.75, 'rgba(255,255,255,0.05)')
  g.addColorStop(1, 'rgba(255,255,255,0)')
  ctx.fillStyle = g; ctx.fillRect(0, 0, 64, 64)
  const tex = new THREE.CanvasTexture(canvas)
  tex.colorSpace = THREE.SRGBColorSpace

  const material = new THREE.PointsMaterial({
    size: 0.5, vertexColors: true, map: tex,
    transparent: true, depthWrite: false,
    blending: THREE.AdditiveBlending, sizeAttenuation: true
  })

  points = new THREE.Points(geometry, material)
  scene.add(points)
  animate()
}

function animate() {
  if (!renderer || !scene || !camera || !geometry || !points || !basePositions) return

  const clock = performance.now() / 1000
  const posAttr = geometry.getAttribute('position') as THREE.BufferAttribute
  const colAttr = geometry.getAttribute('color') as THREE.BufferAttribute
  const positions = posAttr.array as Float32Array
  const colors = colAttr.array as Float32Array

  breathTarget = 0.5 + Math.sin(clock * 0.35) * 0.5
  breath += (breathTarget - breath) * 0.035

  warpFactor += (targetWarp - warpFactor) * 0.05
  if (targetWarp > 0 && warpFactor >= 0.92) {
    emit('warp-done')
    targetWarp = 0
    burstFactor = 1
  }
  if (burstFactor > 0) {
    burstFactor += (0 - burstFactor) * 0.03
  }

  const spinAng = clock * 0.06
  const breathK = breath

  const centerPull = warpFactor * 0.035
  const zSquash = warpFactor * 0.08
  const swirlAng = warpFactor * 2.2
  const shrinkK = Math.pow(1 - warpFactor * 0.9, 1.5)
  const glowK = 1 + warpFactor * 2.2

  for (let i = 0; i < PARTICLE_COUNT; i++) {
    const i3 = i * 3
    const bx = basePositions[i3]
    const by = basePositions[i3 + 1]
    const bz = basePositions[i3 + 2]

    let x = bx, y = by, z = bz

    if (warpFactor > 0 || burstFactor > 0) {
      let rx = bx * shrinkK
      let ry = by * shrinkK
      let rz = bz * shrinkK
      if (warpFactor > 0) {
        rx *= (1 - centerPull)
        ry *= (1 - centerPull)
        rz *= (1 - zSquash)
        const cA = Math.cos(swirlAng + i * 0.008)
        const sA = Math.sin(swirlAng + i * 0.008)
        const tx = rx * cA - ry * sA
        const ty = rx * sA + ry * cA
        rx = tx; ry = ty
        rz *= (0.4 + 0.6 * (1 - warpFactor)) - warpFactor * 2.8
      }
      if (burstFactor > 0) {
        const br = burstFactor * 2.5
        const rng1 = Math.sin(clock * 17 + i * 0.13)
        const rng2 = Math.cos(clock * 13 + i * 0.21)
        const rng3 = Math.sin(clock * 19 + i * 0.17)
        rx += rng1 * br
        ry += rng2 * br
        rz += rng3 * br
      }
      x = rx; y = ry; z = rz
    } else {
      const cosS = Math.cos(spinAng); const sinS = Math.sin(spinAng)
      const rx = x * cosS - y * sinS
      const ry = x * sinS + y * cosS
      x = rx; y = ry
      const inhaleOut = 1 + breathK * 0.12
      const offset = Math.sin(clock * 0.4 + i * 0.018) * 0.02 + breathK * 0.035
      x *= (inhaleOut + offset)
      y *= (inhaleOut + offset)
      z = z * (inhaleOut + offset) + Math.sin(clock * 0.15 + i * 0.13) * 0.06
    }

    positions[i3] = x
    positions[i3 + 1] = y
    positions[i3 + 2] = z

    const bi3 = i3
    const baseBr = Math.max(0.35, Math.sqrt(baseColors![bi3] ** 2 + baseColors![bi3 + 1] ** 2 + baseColors![bi3 + 2] ** 2)) / 3
    const boost = baseBr * glowK
    colors[bi3] = baseColors![bi3] + boost * 0.4
    colors[bi3 + 1] = baseColors![bi3 + 1] + boost * 0.4
    colors[bi3 + 2] = baseColors![bi3 + 2] + boost * 0.4 + warpFactor * 0.3
  }

  posAttr.needsUpdate = true
  colAttr.needsUpdate = true

  if (points) {
    const s = 1 + breathK * 0.06 + warpFactor * 0.25
    points.scale.set(s, s, s)
  }

  if (camera) {
    const targetFov = BASE_FOV + warpFactor * 95
    camera.fov += (targetFov - camera.fov) * 0.05
    camera.position.z = 38 - warpFactor * 20
    camera.updateProjectionMatrix()
  }

  if (scene && scene.fog instanceof THREE.FogExp2) {
    scene.fog.density = 0.008 + warpFactor * 0.12
  }

  if (renderer) renderer.render(scene, camera)
  rafId = requestAnimationFrame(animate)
}

function startWarp() {
  targetWarp = 1
  warping.value = true
}

defineExpose({ startWarp })

watch(() => warpFactor, (v: number) => {
  if (v < 0.01) warping.value = false
})

function onResize() {
  if (!renderer || !camera) return
  const w = window.innerWidth
  const h = window.innerHeight
  renderer.setSize(w, h)
  camera.aspect = w / h
  camera.updateProjectionMatrix()
}

onMounted(() => { init(); window.addEventListener('resize', onResize) })
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  if (rafId) cancelAnimationFrame(rafId)
  if (renderer) {
    renderer.dispose()
    if (renderer.domElement && renderer.domElement.parentElement) {
      renderer.domElement.parentElement.removeChild(renderer.domElement)
    }
  }
  if (geometry) geometry.dispose()
})
</script>

<style scoped>
.particle-scene {
  position: fixed; inset: 0;
  z-index: 0; pointer-events: none; overflow: hidden;
}
.particle-scene :deep(canvas) { display: block; width: 100%; height: 100%; }
.warp-flash {
  position: fixed; inset: 0;
  pointer-events: none;
  z-index: 999;
  background: radial-gradient(circle at center, rgba(255,255,255,.85) 0%, rgba(200,220,255,.35) 25%, transparent 55%);
  animation: flashIn 1.1s ease-out forwards;
}
@keyframes flashIn {
  0%   { opacity: 0; transform: scale(.6); }
  35%  { opacity: 1; transform: scale(1.05); }
  100% { opacity: 0; transform: scale(1.4); }
}
</style>
