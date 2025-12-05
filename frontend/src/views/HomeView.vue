<template>
  <div class="container home-container">
    <!-- 圖片網格輪播背景 -->
    <ShowcaseBackground />

    <!-- Hero Area -->
    <div class="hero-section">
      <div class="hero-content">
        <div class="brand-pill">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 6px;"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>
          AI 驅動的部落格創作助手
        </div>
        <div class="platform-slogan">
          讓創作不再有門檻，讓寫作從未如此簡單
        </div>
        <h1 class="page-title">靈感一觸即發</h1>
        <p class="page-subtitle">輸入你的創意主題，讓 AI 幫你生成精彩標題、內文和配圖</p>
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
        © 2025 AI 圖文生成器 - 部落格文章一鍵生成
      </div>
      <div class="footer-license">
        Based on <a href="https://github.com/HisMax/RedInk" target="_blank" rel="noopener noreferrer">RedInk</a> | Licensed under <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" target="_blank" rel="noopener noreferrer">CC BY-NC-SA 4.0</a>
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

/**
 * 處理圖片變化
 */
function handleImagesChange(images: File[]) {
  uploadedImageFiles.value = images
}

/**
 * 生成大綱
 */
async function handleGenerate() {
  if (!topic.value.trim()) return

  loading.value = true
  error.value = ''

  try {
    const imageFiles = uploadedImageFiles.value

    const result = await generateOutline(
      topic.value.trim(),
      imageFiles.length > 0 ? imageFiles : undefined
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
