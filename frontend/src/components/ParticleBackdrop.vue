<template>
  <div ref="mountRef" class="particle-backdrop"></div>
  <div v-if="showFlash" class="warp-flash"></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, provide } from 'vue'
import * as THREE from 'three'

const emit = defineEmits<{ (e: 'warp-done'): void }>()

const mountRef = ref<HTMLDivElement>()
const folding = ref(false)
const showFlash = ref(false)

let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let points: THREE.Points | null = null
let geometry: THREE.BufferGeometry | null = null
let material: THREE.PointsMaterial | null = null
let rafId: number | null = null

let basePositions: Float32Array | null = null
let breath = 0
let breathTarget = 0.5

let warpFactor = 0
let targetWarp = 0
let warpDoneFired = false

const PARTICLE_COUNT = 600
const BASE_FOV = 60
const BASE_CAMERA_Z = 38

function makeRand(seed: number) {
  let s = seed
  return () => {
    s = (s * 9301 + 49297) % 233280
    return s / 233280
  }
}

function init() {
  if (!mountRef.value) return

  const width = window.innerWidth
  const height = window.innerHeight

  scene = new THREE.Scene()
  scene.background = null
  scene.fog = new THREE.FogExp2('#05060a', 0.02)

  camera = new THREE.PerspectiveCamera(BASE_FOV, width / height, 0.1, 2000)
  camera.position.set(0, 0, BASE_CAMERA_Z)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(width, height)
  renderer.setClearColor(0x000000, 0)
  mountRef.value.appendChild(renderer.domElement)

  const positions = new Float32Array(PARTICLE_COUNT * 3)
  const colors = new Float32Array(PARTICLE_COUNT * 3)
  const sizes = new Float32Array(PARTICLE_COUNT)

  const rand = makeRand(Date.now() & 0xffff)

  for (let i = 0; i < PARTICLE_COUNT; i++) {
    const i3 = i * 3
    const r = 14 + rand() * 34
    const theta = rand() * Math.PI * 2
    const phi = Math.acos(2 * rand() - 1)
    positions[i3] = r * Math.sin(phi) * Math.cos(theta)
    positions[i3 + 1] = r * Math.sin(phi) * Math.sin(theta)
    positions[i3 + 2] = r * Math.cos(phi)

    const palette = rand()
    let c: THREE.Color
    if (palette < 0.55) c = new THREE.Color('#7c8cff')
    else if (palette < 0.8) c = new THREE.Color('#4f7cff')
    else if (palette < 0.92) c = new THREE.Color('#7c4dff')
    else c = new THREE.Color('#40c4ff')

    const brightness = 0.35 + rand() * 0.4
    colors[i3] = c.r * brightness
    colors[i3 + 1] = c.g * brightness
    colors[i3 + 2] = c.b * brightness

    sizes[i] = 0.3 + rand() * 1.6
  }

  basePositions = new Float32Array(positions)

  geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
  geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1))

  const canvas = document.createElement('canvas')
  canvas.width = 64
  canvas.height = 64
  const ctx = canvas.getContext('2d')!
  const grad = ctx.createRadialGradient(32, 32, 0, 32, 32, 32)
  grad.addColorStop(0, 'rgba(255,255,255,0.9)')
  grad.addColorStop(0.3, 'rgba(255,255,255,0.45)')
  grad.addColorStop(0.75, 'rgba(255,255,255,0.05)')
  grad.addColorStop(1, 'rgba(255,255,255,0)')
  ctx.fillStyle = grad
  ctx.fillRect(0, 0, 64, 64)
  const texture = new THREE.CanvasTexture(canvas)
  texture.colorSpace = THREE.SRGBColorSpace

  material = new THREE.PointsMaterial({
    size: 0.5,
    vertexColors: true,
    map: texture,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    sizeAttenuation: true
  })

  points = new THREE.Points(geometry, material)
  scene.add(points)

  animate()
}

function animate() {
  if (!renderer || !scene || !camera || !geometry || !points || !basePositions || !material) return

  const clock = performance.now() / 1000

  breathTarget = 0.5 + Math.sin(clock * 0.35) * 0.5
  breath += (breathTarget - breath) * 0.035
  const breathK = breath

  warpFactor += (targetWarp - warpFactor) * 0.05
  const w = warpFactor

  if (targetWarp > 0 && w >= 0.92 && !warpDoneFired) {
    warpDoneFired = true
    showFlash.value = true
  }

  const posAttr = geometry.getAttribute('position') as THREE.BufferAttribute
  const positions = posAttr.array as Float32Array

  const spinAng = clock * 0.06

  const colorAttr = geometry.getAttribute('color') as THREE.BufferAttribute
  const colors = colorAttr.array as Float32Array

  for (let i = 0; i < PARTICLE_COUNT; i++) {
    const i3 = i * 3

    let x = basePositions[i3]
    let y = basePositions[i3 + 1]
    let z = basePositions[i3 + 2]

    const cosS = Math.cos(spinAng)
    const sinS = Math.sin(spinAng)
    const rx = x * cosS - y * sinS
    const ry = x * sinS + y * cosS
    x = rx
    y = ry

    const inhaleOut = 1 + breathK * 0.12
    const breathOffset = Math.sin(clock * 0.4 + i * 0.018) * 0.02 + breathK * 0.035
    x *= (inhaleOut + breathOffset)
    y *= (inhaleOut + breathOffset)
    const breathZ = z * (inhaleOut + breathOffset) + Math.sin(clock * 0.15 + i * 0.13) * 0.06
    z = breathZ

    if (w > 0.001) {
      x = x * (1 - w * 0.02)
      y = y * (1 - w * 0.02)
      z = z * (1 - w * 0.08)

      const angle = w * 2.0
      const rx2 = x * Math.cos(angle) - y * Math.sin(angle)
      const ry2 = x * Math.sin(angle) + y * Math.cos(angle)
      x = rx2
      y = ry2

      z -= w * 6
      x *= (1 + w * 0.3)
      y *= (1 + w * 0.3)
    }

    positions[i3] = x
    positions[i3 + 1] = y
    positions[i3 + 2] = z

    if (w > 0.001) {
      const i3c = i * 3
      const boost = 1 + w * 1.2
      colors[i3c] = Math.min(1, colors[i3c] * boost + w * 0.4)
      colors[i3c + 1] = Math.min(1, colors[i3c + 1] * boost + w * 0.4)
      colors[i3c + 2] = Math.min(1, colors[i3c + 2] * boost + w * 0.45)
    }
  }

  posAttr.needsUpdate = true
  colorAttr.needsUpdate = true

  if (points) {
    const s = 1 + breathK * 0.06 - w * 0.4
    points.scale.set(s, s, s)
  }

  if (camera) {
    const targetFov = BASE_FOV + w * 90
    camera.fov += (targetFov - camera.fov) * 0.05
    camera.updateProjectionMatrix()

    if (w > 0.5) {
      const targetZ = BASE_CAMERA_Z - w * 22
      camera.position.z += (targetZ - camera.position.z) * 0.04
    } else {
      camera.position.z += (BASE_CAMERA_Z - camera.position.z) * 0.05
    }
  }

  if (scene && scene.fog && scene.fog instanceof THREE.FogExp2) {
    scene.fog.density = 0.02 + w * 0.1
  }

  if (showFlash.value) {
    emit('warp-done')
  }

  if (renderer) renderer.render(scene, camera)
  rafId = requestAnimationFrame(animate)
}

function startWarp() {
  folding.value = true
  targetWarp = 1
  warpDoneFired = false
  showFlash.value = false
}

function resetState() {
  warpFactor = 0
  targetWarp = 0
  warpDoneFired = false
  showFlash.value = false
  folding.value = false
  if (camera) {
    camera.fov = BASE_FOV
    camera.position.set(0, 0, BASE_CAMERA_Z)
    camera.updateProjectionMatrix()
  }
  if (scene && scene.fog && scene.fog instanceof THREE.FogExp2) {
    scene.fog.density = 0.02
  }
}

provide('warpControl', { startWarp, resetState })

function onResize() {
  if (!renderer || !camera) return
  const w = window.innerWidth
  const h = window.innerHeight
  renderer.setSize(w, h)
  camera.aspect = w / h
  camera.updateProjectionMatrix()
}

onMounted(() => {
  init()
  window.addEventListener('resize', onResize)
})

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
  if (material) material.dispose()
})

defineExpose({ startWarp, resetState })
</script>

<style scoped>
.particle-backdrop {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}

.particle-backdrop :deep(canvas) {
  display: block;
  width: 100%;
  height: 100%;
}

.warp-flash {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: radial-gradient(circle, rgba(255,255,255,1) 0%, rgba(240,245,255,.95) 25%, rgba(180,190,255,.6) 55%, rgba(124,140,255,.2) 80%, transparent 100%);
  pointer-events: none;
  animation: flashOut .5s ease-out forwards;
}
@keyframes flashOut {
  0% { opacity: 0; transform: scale(0.6); }
  20% { opacity: 1; transform: scale(1); }
  100% { opacity: 0; transform: scale(1.4); }
}
</style>
