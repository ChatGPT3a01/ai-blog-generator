<template>
  <div class="container">
    <div class="page-header">
      <div>
        <h1 class="page-title">生成結果</h1>
        <p class="page-subtitle">
          <span v-if="isGenerating">正在生成第 {{ store.progress.current + 1 }} / {{ store.progress.total }} 頁</span>
          <span v-else-if="hasFailedImages">{{ failedCount }} 張圖片生成失敗，可點擊重試</span>
          <span v-else>全部 {{ store.progress.total }} 張圖片生成完成</span>
        </p>
      </div>
      <div style="display: flex; gap: 10px;">
        <button
          v-if="hasFailedImages && !isGenerating"
          class="btn btn-primary"
          @click="retryAllFailed"
          :disabled="isRetrying"
        >
          {{ isRetrying ? '補全中...' : '一鍵補全失敗圖片' }}
        </button>
        <button class="btn" @click="router.push('/outline')" style="border:1px solid var(--border-color)">
          返回大綱
        </button>
      </div>
    </div>

    <div class="card">
      <div style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
        <span style="font-weight: 600;">生成進度</span>
        <span style="color: var(--primary); font-weight: 600;">{{ Math.round(progressPercent) }}%</span>
      </div>
      <div class="progress-container">
        <div class="progress-bar" :style="{ width: progressPercent + '%' }" />
      </div>

      <div v-if="error" class="error-msg">
        {{ error }}
      </div>

      <div class="grid-cols-4" style="margin-top: 40px;">
        <div v-for="image in store.images" :key="image.index" class="image-card">
          <!-- 圖片展示區域 -->
          <div v-if="image.url && image.status === 'done'" class="image-preview">
            <img :src="image.url" :alt="`第 ${image.index + 1} 頁`" />
            <!-- 重新生成按鈕（懸停顯示） -->
            <div class="image-overlay">
              <button
                class="overlay-btn"
                @click="regenerateImage(image.index)"
                :disabled="image.status === 'retrying'"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M23 4v6h-6"></path>
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                </svg>
                重新生成
              </button>
            </div>
          </div>

          <!-- 生成中/重試中狀態 -->
          <div v-else-if="image.status === 'generating' || image.status === 'retrying'" class="image-placeholder">
            <div class="spinner"></div>
            <div class="status-text">{{ image.status === 'retrying' ? '重試中...' : '生成中...' }}</div>
          </div>

          <!-- 失敗狀態 -->
          <div v-else-if="image.status === 'error'" class="image-placeholder error-placeholder">
            <div class="error-icon">!</div>
            <div class="status-text">生成失敗</div>
            <button
              class="retry-btn"
              @click="retrySingleImage(image.index)"
              :disabled="isRetrying"
            >
              點擊重試
            </button>
          </div>

          <!-- 等待中狀態 -->
          <div v-else class="image-placeholder">
            <div class="status-text">等待中</div>
          </div>

          <!-- 底部資訊欄 -->
          <div class="image-footer">
            <span class="page-label">Page {{ image.index + 1 }}</span>
            <span class="status-badge" :class="image.status">
              {{ getStatusText(image.status) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGeneratorStore } from '../stores/generator'
import { generateImagesPost, regenerateImage as apiRegenerateImage, retryFailedImages as apiRetryFailed, createHistory, updateHistory, getImageUrl } from '../api'

const router = useRouter()
const store = useGeneratorStore()

const error = ref('')
const isRetrying = ref(false)

const isGenerating = computed(() => store.progress.status === 'generating')

const progressPercent = computed(() => {
  if (store.progress.total === 0) return 0
  return (store.progress.current / store.progress.total) * 100
})

const hasFailedImages = computed(() => store.images.some(img => img.status === 'error'))

const failedCount = computed(() => store.images.filter(img => img.status === 'error').length)

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    generating: '生成中',
    done: '已完成',
    error: '失敗',
    retrying: '重試中'
  }
  return texts[status] || '等待中'
}

// 重試單張圖片（非同步並行執行，不阻塞）
function retrySingleImage(index: number) {
  if (!store.taskId) return

  const page = store.outline.pages.find(p => p.index === index)
  if (!page) return

  // 立即設置為重試狀態
  store.setImageRetrying(index)

  // 構建上下文資訊
  const context = {
    fullOutline: store.outline.raw || '',
    userTopic: store.topic || ''
  }

  // 非同步執行重繪，不阻塞
  apiRegenerateImage(store.taskId, page, true, context)
    .then(result => {
      if (result.success && result.image_url) {
        store.updateImage(index, result.image_url)
      } else {
        store.updateProgress(index, 'error', undefined, result.error)
      }
    })
    .catch(e => {
      store.updateProgress(index, 'error', undefined, String(e))
    })
}

// 重新生成圖片（成功的也可以重新生成，立即返回不等待）
function regenerateImage(index: number) {
  retrySingleImage(index)
}

// 批量重試所有失敗的圖片
async function retryAllFailed() {
  if (!store.taskId) return

  const failedPages = store.getFailedPages()
  if (failedPages.length === 0) return

  isRetrying.value = true

  // 設置所有失敗的圖片為重試狀態
  failedPages.forEach(page => {
    store.setImageRetrying(page.index)
  })

  try {
    await apiRetryFailed(
      store.taskId,
      failedPages,
      // onProgress
      () => {},
      // onComplete
      (event) => {
        if (event.image_url) {
          store.updateImage(event.index, event.image_url)
        }
      },
      // onError
      (event) => {
        store.updateProgress(event.index, 'error', undefined, event.message)
      },
      // onFinish
      () => {
        isRetrying.value = false
      },
      // onStreamError
      (err) => {
        console.error('重試失敗:', err)
        isRetrying.value = false
        error.value = '重試失敗: ' + err.message
      }
    )
  } catch (e) {
    isRetrying.value = false
    error.value = '重試失敗: ' + String(e)
  }
}

onMounted(async () => {
  if (store.outline.pages.length === 0) {
    router.push('/')
    return
  }

  // 建立歷史記錄（如果還沒有）
  if (!store.recordId) {
    try {
      const result = await createHistory(store.topic, {
        raw: store.outline.raw,
        pages: store.outline.pages
      })
      if (result.success && result.record_id) {
        store.recordId = result.record_id
        console.log('建立歷史記錄:', store.recordId)
      }
    } catch (e) {
      console.error('建立歷史記錄失敗:', e)
    }
  }

  store.startGeneration()

  generateImagesPost(
    store.outline.pages,
    null,
    store.outline.raw,  // 傳入完整大綱文字
    // onProgress
    (event) => {
      console.log('Progress:', event)
    },
    // onComplete
    (event) => {
      console.log('Complete:', event)
      if (event.image_url) {
        store.updateProgress(event.index, 'done', event.image_url)
      }
    },
    // onError
    (event) => {
      console.error('Error:', event)
      store.updateProgress(event.index, 'error', undefined, event.message)
    },
    // onFinish
    async (event) => {
      console.log('Finish:', event)
      store.finishGeneration(event.task_id)

      // 更新歷史記錄
      if (store.recordId) {
        try {
          // 收集所有生成的圖片檔案名稱
          const generatedImages = event.images.filter(img => img !== null)

          // 確定狀態
          let status = 'completed'
          if (hasFailedImages.value) {
            status = generatedImages.length > 0 ? 'partial' : 'draft'
          }

          // 取得封面圖作為縮圖（只儲存檔案名稱，不是完整URL）
          const thumbnail = generatedImages.length > 0 ? generatedImages[0] : null

          await updateHistory(store.recordId, {
            images: {
              task_id: event.task_id,
              generated: generatedImages
            },
            status: status,
            thumbnail: thumbnail
          })
          console.log('歷史記錄已更新')
        } catch (e) {
          console.error('更新歷史記錄失敗:', e)
        }
      }

      // 如果沒有失敗的，跳轉到結果頁
      if (!hasFailedImages.value) {
        setTimeout(() => {
          router.push('/result')
        }, 1000)
      }
    },
    // onStreamError
    (err) => {
      console.error('Stream Error:', err)
      error.value = '生成失敗: ' + err.message
    },
    // userImages - 使用者上傳的參考圖片
    store.userImages.length > 0 ? store.userImages : undefined,
    // userTopic - 使用者原始輸入
    store.topic,
    // imageStyle - 圖片風格
    store.imageStyle
  )
})
</script>

<style scoped>
.image-preview {
  aspect-ratio: 3/4;
  overflow: hidden;
  position: relative;
  flex: 1; /* 填充卡片剩余空间 */
}

.image-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.image-preview:hover .image-overlay {
  opacity: 1;
}

.overlay-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #333;
  transition: all 0.2s;
}

.overlay-btn:hover {
  background: var(--primary);
  color: white;
}

.overlay-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.image-placeholder {
  aspect-ratio: 3/4;
  background: #f9f9f9;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex: 1; /* 填充卡片剩余空间 */
  min-height: 240px; /* 确保有最小高度 */
}

.error-placeholder {
  background: #fff5f5;
}

.error-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #ff4d4f;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
}

.status-text {
  font-size: 13px;
  color: var(--text-sub);
}

.retry-btn {
  margin-top: 8px;
  padding: 6px 16px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.retry-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.retry-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.image-footer {
  padding: 12px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-label {
  font-size: 12px;
  color: var(--text-sub);
}

.status-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
}

.status-badge.done {
  background: #E6F7ED;
  color: #52C41A;
}

.status-badge.generating,
.status-badge.retrying {
  background: #E6F4FF;
  color: #1890FF;
}

.status-badge.error {
  background: #FFF1F0;
  color: #FF4D4F;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--primary);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
