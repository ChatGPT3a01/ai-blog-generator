<template>
  <canvas ref="canvas" class="particle-canvas"></canvas>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  life: number
  maxLife: number
  size: number
  color: string
}

const canvas = ref<HTMLCanvasElement | null>(null)
let ctx: CanvasRenderingContext2D | null = null
let particles: Particle[] = []
let animationId: number | null = null
let mouseX = 0
let mouseY = 0

// 粒子顏色 - 使用漸層主色調
const colors = [
  'rgba(255, 36, 66, 0.8)',   // 主色
  'rgba(255, 107, 107, 0.7)', // 淺紅
  'rgba(255, 166, 166, 0.6)', // 粉紅
  'rgba(255, 200, 87, 0.7)',  // 金色
  'rgba(255, 255, 255, 0.5)'  // 白色
]

function createParticle(x: number, y: number): Particle {
  const angle = Math.random() * Math.PI * 2
  const speed = Math.random() * 2 + 0.5
  return {
    x,
    y,
    vx: Math.cos(angle) * speed,
    vy: Math.sin(angle) * speed - 1, // 稍微往上飄
    life: 0,
    maxLife: Math.random() * 30 + 20, // 20-50 幀
    size: Math.random() * 4 + 2,
    color: colors[Math.floor(Math.random() * colors.length)]
  }
}

function updateParticles() {
  particles = particles.filter(p => p.life < p.maxLife)

  for (const p of particles) {
    p.x += p.vx
    p.y += p.vy
    p.vy += 0.05 // 微小重力
    p.life++
  }
}

function drawParticles() {
  if (!ctx || !canvas.value) return

  ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)

  for (const p of particles) {
    const progress = p.life / p.maxLife
    const alpha = 1 - progress
    const size = p.size * (1 - progress * 0.5)

    ctx.beginPath()
    ctx.arc(p.x, p.y, size, 0, Math.PI * 2)
    ctx.fillStyle = p.color.replace(/[\d.]+\)$/, `${alpha})`)
    ctx.fill()
  }
}

function animate() {
  updateParticles()
  drawParticles()
  animationId = requestAnimationFrame(animate)
}

function handleMouseMove(e: MouseEvent) {
  mouseX = e.clientX
  mouseY = e.clientY

  // 每次移動產生 2-3 個粒子
  const count = Math.floor(Math.random() * 2) + 2
  for (let i = 0; i < count; i++) {
    particles.push(createParticle(mouseX, mouseY))
  }

  // 限制粒子數量避免效能問題
  if (particles.length > 100) {
    particles = particles.slice(-100)
  }
}

function handleResize() {
  if (canvas.value) {
    canvas.value.width = window.innerWidth
    canvas.value.height = window.innerHeight
  }
}

onMounted(() => {
  if (canvas.value) {
    ctx = canvas.value.getContext('2d')
    handleResize()
    window.addEventListener('resize', handleResize)
    window.addEventListener('mousemove', handleMouseMove)
    animate()
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('mousemove', handleMouseMove)
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
})
</script>

<style scoped>
.particle-canvas {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  pointer-events: none;
  z-index: 9999;
}
</style>
