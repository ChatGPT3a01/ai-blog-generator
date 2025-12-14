<template>
  <!-- 科技感漸層背景 -->
  <div class="showcase-background">
    <div class="gradient-bg"></div>
    <div class="grid-overlay"></div>
    <div class="glow-orb orb-1"></div>
    <div class="glow-orb orb-2"></div>
  </div>
</template>

<script setup lang="ts">
/**
 * 科技感漸層背景組件
 *
 * 特色：
 * - 深綠色科技感漸層
 * - 網格線效果
 * - 發光球體裝飾
 */
</script>

<style scoped>
/* 背景容器 */
.showcase-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100vh;
  z-index: -1;
  overflow: hidden;
}

/* 主漸層背景 */
.gradient-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    #0a1f1c 0%,
    #0d2818 25%,
    #143d2b 50%,
    #0f2e22 75%,
    #081a15 100%
  );
}

/* 網格線效果 */
.grid-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(16, 185, 129, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(16, 185, 129, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  mask-image: radial-gradient(ellipse at center, black 0%, transparent 70%);
}

/* 發光球體 */
.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: float 8s ease-in-out infinite;
}

.orb-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, #10b981 0%, transparent 70%);
  top: -100px;
  right: -100px;
  animation-delay: 0s;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #059669 0%, transparent 70%);
  bottom: -100px;
  left: -100px;
  animation-delay: 4s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-30px) scale(1.05);
  }
}

/* 覆蓋層讓前景內容更清晰 */
.showcase-background::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to bottom,
    rgba(255, 255, 255, 0.85) 0%,
    rgba(255, 255, 255, 0.9) 50%,
    rgba(255, 255, 255, 0.95) 100%
  );
}
</style>
