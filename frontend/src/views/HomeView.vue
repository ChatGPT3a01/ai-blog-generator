<template>
  <div class="container home-container">
    <!-- 浮動泡泡背景層 -->
    <div class="bubbles-container bubbles-back">
      <div class="bubble" v-for="i in 25" :key="'back-'+i" :style="getBubbleStyle(i, false)"></div>
    </div>

    <!-- 圖片網格輪播背景 -->
    <ShowcaseBackground />

    <!-- 浮動泡泡前景層 -->
    <div class="bubbles-container bubbles-front">
      <div class="bubble" v-for="i in 15" :key="'front-'+i" :style="getBubbleStyle(i, true)"></div>
    </div>

    <!-- Hero Area -->
    <div class="hero-section">
      <div class="hero-content">
        <div class="brand-pill">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 6px;"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>
          亮言AI驅動部落格：一鍵成仙
        </div>
        <div class="platform-slogan">
          讓意念轉化為文字，讓思想刻劃於永恆
        </div>
        <h1 class="page-title">文思泉湧的氾濫</h1>
        <p class="page-subtitle">輸入你的思想，讓 亮言AI 幫你生成精彩標題、內文和配圖，並且一鍵即上部落格</p>
      </div>

      <!-- 主題輸入組合框 -->
      <ComposerInput
        ref="composerRef"
        v-model="topic"
        :loading="loading"
        @generate="handleGenerate"
        @imagesChange="handleImagesChange"
      />
    </div>

    <!-- 版權資訊 -->
    <div class="page-footer">
      <div class="footer-copyright">
        © 2026 亮言AI - 部落格文章一鍵生成
      </div>
      <div class="footer-license">
        阿亮老師
      </div>
    </div>

    <!-- 錯誤提示 -->
    <div v-if="error" class="error-toast">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
      {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGeneratorStore } from '../stores/generator'
import { generateOutline } from '../api'

// 引入元件
import ShowcaseBackground from '../components/home/ShowcaseBackground.vue'
import ComposerInput from '../components/home/ComposerInput.vue'

const router = useRouter()
const store = useGeneratorStore()

// 狀態
const topic = ref('')
const loading = ref(false)
const error = ref('')
const composerRef = ref<InstanceType<typeof ComposerInput> | null>(null)

// 上傳的圖片檔案
const uploadedImageFiles = ref<File[]>([])

// 泡泡顏色陣列（更鮮豔）
const bubbleColors = [
  'rgba(255, 107, 129, 0.6)',  // 粉紅
  'rgba(108, 92, 231, 0.6)',   // 紫色
  'rgba(0, 184, 148, 0.6)',    // 綠色
  'rgba(253, 203, 110, 0.6)',  // 黃色
  'rgba(74, 144, 226, 0.6)',   // 藍色
  'rgba(255, 159, 67, 0.6)',   // 橘色
  'rgba(162, 155, 254, 0.6)',  // 淡紫
  'rgba(129, 236, 236, 0.6)',  // 青色
]

/**
 * 產生泡泡樣式
 * @param index 泡泡索引
 * @param isFront 是否為前景泡泡
 */
function getBubbleStyle(index: number, isFront: boolean = false) {
  // 前景泡泡更大、更模糊
  const baseSize = isFront ? 50 : 30
  const sizeRange = isFront ? 100 : 80
  const size = Math.random() * sizeRange + baseSize

  const left = Math.random() * 100  // 0-100%
  const delay = Math.random() * 6  // 0-6s delay
  const duration = Math.random() * 5 + (isFront ? 8 : 6)  // 前景泡泡飄得慢一點
  const color = bubbleColors[index % bubbleColors.length]

  // 前景泡泡更透明，有朦朧感
  const opacity = isFront ? 0.4 : 0.6
  const colorWithOpacity = color.replace(/[\d.]+\)$/, `${opacity})`)

  return {
    width: `${size}px`,
    height: `${size}px`,
    left: `${left}%`,
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`,
    background: `radial-gradient(circle at 30% 30%, rgba(255,255,255,${isFront ? 0.7 : 0.9}), ${colorWithOpacity})`,
    filter: isFront ? 'blur(2px)' : 'none',
  }
}

/**
 * 處理圖片變化
 */
function handleImagesChange(images: File[]) {
  uploadedImageFiles.value = images
}

/**
 * 生成大綱
 */
async function handleGenerate(textStyle: string = 'professional') {
  if (!topic.value.trim()) return

  loading.value = true
  error.value = ''

  try {
    const imageFiles = uploadedImageFiles.value

    const result = await generateOutline(
      topic.value.trim(),
      imageFiles.length > 0 ? imageFiles : undefined,
      textStyle
    )

    if (result.success && result.pages) {
      store.setTopic(topic.value.trim())
      store.setOutline(result.outline || '', result.pages)
      store.recordId = null

      // 儲存使用者上傳的圖片到 store
      if (imageFiles.length > 0) {
        store.userImages = imageFiles
      } else {
        store.userImages = []
      }

      // 清理 ComposerInput 的預覽
      composerRef.value?.clearPreviews()
      uploadedImageFiles.value = []

      router.push('/outline')
    } else {
      error.value = result.error || '生成大綱失敗'
    }
  } catch (err: any) {
    error.value = err.message || '網路錯誤，請重試'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.home-container {
  max-width: 1100px;
  padding-top: 10px;
  position: relative;
  z-index: 1;
}

/* 泡泡容器 */
.bubbles-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  pointer-events: none;
}

/* 背景層泡泡 */
.bubbles-back {
  z-index: 0;
}

/* 前景層泡泡 */
.bubbles-front {
  z-index: 100;
}

/* 泡泡樣式 */
.bubble {
  position: absolute;
  bottom: -100px;
  border-radius: 50%;
  opacity: 0;
  animation: floatUp linear infinite;
  box-shadow:
    inset 0 -5px 20px rgba(255, 255, 255, 0.4),
    inset 5px 0 20px rgba(255, 255, 255, 0.2),
    0 0 10px rgba(255, 255, 255, 0.2);
}

/* 泡泡上浮動畫（更明顯） */
@keyframes floatUp {
  0% {
    bottom: -100px;
    opacity: 0;
    transform: scale(0.4) translateX(0);
  }
  10% {
    opacity: 0.85;
  }
  30% {
    opacity: 0.9;
    transform: scale(0.9) translateX(15px);
  }
  50% {
    transform: scale(1) translateX(-15px);
  }
  70% {
    opacity: 0.7;
    transform: scale(1.1) translateX(10px);
  }
  85% {
    opacity: 0.3;
  }
  100% {
    bottom: 110vh;
    opacity: 0;
    transform: scale(1.2) translateX(0);
  }
}

/* Hero Section */
.hero-section {
  text-align: center;
  margin-bottom: 40px;
  padding: 50px 60px;
  animation: fadeIn 0.6s ease-out;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
  backdrop-filter: blur(10px);
}

.hero-content {
  margin-bottom: 36px;
}

.brand-pill {
  display: inline-block;
  padding: 6px 16px;
  background: rgba(255, 36, 66, 0.08);
  color: var(--primary);
  border-radius: 100px;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 20px;
  letter-spacing: 0.5px;
}

.platform-slogan {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-main);
  margin-bottom: 24px;
  line-height: 1.6;
  letter-spacing: 0.5px;
}

.page-subtitle {
  font-size: 16px;
  color: var(--text-sub);
  margin-top: 12px;
}

/* Page Footer */
.page-footer {
  text-align: center;
  padding: 24px 0 16px;
  margin-top: 20px;
}

.footer-copyright {
  font-size: 15px;
  color: #333;
  font-weight: 500;
  margin-bottom: 6px;
}

.footer-copyright a {
  color: var(--primary);
  text-decoration: none;
  font-weight: 600;
}

.footer-copyright a:hover {
  text-decoration: underline;
}

.footer-license {
  font-size: 13px;
  color: #999;
}

.footer-license a {
  color: #666;
  text-decoration: none;
}

.footer-license a:hover {
  color: var(--primary);
}

/* Error Toast */
.error-toast {
  position: fixed;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  background: #FF4D4F;
  color: white;
  padding: 12px 24px;
  border-radius: 50px;
  box-shadow: 0 8px 24px rgba(255, 77, 79, 0.3);
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 1000;
  animation: slideUp 0.3s ease-out;
}

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
