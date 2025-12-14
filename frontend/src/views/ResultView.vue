<template>
  <div class="container">
    <div class="page-header">
      <div>
        <h1 class="page-title">創作完成</h1>
        <p class="page-subtitle">恭喜！你的部落格圖文已生成完畢，共 {{ store.images.length }} 張</p>
      </div>
      <div style="display: flex; gap: 12px;">
        <button class="btn" @click="startOver" style="background: white; border: 1px solid var(--border-color);">
          再來一篇
        </button>
        <button
          class="btn"
          @click="uploadAllImages"
          :disabled="isUploading || allUploaded"
          style="background: #4CAF50; color: white; border: none;"
        >
          <svg v-if="isUploading" class="spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/></svg>
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
          {{ isUploading ? '上傳中...' : (allUploaded ? '已全部上傳' : '一鍵上傳圖床') }}
        </button>
        <button class="btn" @click="showPublishModal = true" style="background: #ff7043; color: white; border: none;">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
          發布到 Blogger
        </button>
        <button class="btn btn-primary" @click="downloadAll">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
          一鍵下載
        </button>
      </div>
    </div>

    <!-- 上傳狀態提示 -->
    <div v-if="uploadedCount > 0" class="upload-status-bar">
      <span>已上傳: {{ uploadedCount }} / {{ store.images.length }} 張圖片</span>
      <span v-if="allUploaded" style="color: #4CAF50;">可使用「發布到 Blogger」功能</span>
    </div>

    <div class="card">
      <div class="grid-cols-4">
        <div v-for="image in store.images" :key="image.index" class="image-card group">
          <!-- Image Area -->
          <div 
            v-if="image.url" 
            style="position: relative; aspect-ratio: 3/4; overflow: hidden; cursor: pointer;" 
            @click="viewImage(image.url)"
          >
            <img
              :src="image.url"
              :alt="`第 ${image.index + 1} 頁`"
              style="width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s;"
            />
            <!-- Regenerating Overlay -->
            <div v-if="regeneratingIndex === image.index" style="position: absolute; inset: 0; background: rgba(255,255,255,0.8); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 10;">
               <div class="spinner" style="width: 24px; height: 24px; border-width: 2px; border-color: var(--primary); border-top-color: transparent;"></div>
               <span style="font-size: 12px; color: var(--primary); margin-top: 8px; font-weight: 600;">重繪中...</span>
            </div>

            <!-- Hover Overlay -->
            <div v-else style="position: absolute; inset: 0; background: rgba(0,0,0,0.3); opacity: 0; transition: opacity 0.2s; display: flex; align-items: center; justify-content: center; color: white; font-weight: 600;" class="hover-overlay">
              預覽大圖
            </div>
          </div>
          
          <!-- Action Bar -->
          <div style="padding: 12px; border-top: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 12px; color: var(--text-sub);">Page {{ image.index + 1 }}</span>
            <div style="display: flex; gap: 8px; align-items: center;">
              <!-- 上傳狀態/按鈕 -->
              <template v-if="image.uploadedUrl">
                <span class="upload-badge done" title="點擊複製連結" @click="copyUrl(image.uploadedUrl!)">
                  已上傳
                </span>
              </template>
              <template v-else-if="image.uploadStatus === 'uploading'">
                <span class="upload-badge uploading">上傳中</span>
              </template>
              <template v-else-if="image.uploadStatus === 'error'">
                <span class="upload-badge error" :title="image.uploadError">失敗</span>
              </template>
              <template v-else>
                <button
                  class="upload-btn"
                  title="上傳到 ImgBB"
                  @click="uploadSingleImage(image)"
                  :disabled="isUploading"
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                </button>
              </template>
              <button
                style="border: none; background: none; color: var(--text-sub); cursor: pointer; display: flex; align-items: center;"
                title="重新生成此圖"
                @click="handleRegenerate(image)"
                :disabled="regeneratingIndex === image.index"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 4v6h-6"></path><path d="M1 20v-6h6"></path><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
              </button>
              <button
                style="border: none; background: none; color: var(--primary); cursor: pointer; font-size: 12px;"
                @click="downloadOne(image)"
              >
                下載
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Blogger 發布彈窗 -->
    <PublishModal
      :visible="showPublishModal"
      :title="store.topic"
      :outline="store.outline?.raw || ''"
      :images="imageUrls"
      @close="showPublishModal = false"
    />
  </div>
</template>

<style scoped>
/* 確保圖片預覽區域正確填充 */
.image-card > div:first-child {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.image-card:hover .hover-overlay {
  opacity: 1;
}
.image-card:hover img {
  transform: scale(1.05);
}

/* 上傳狀態條 */
.upload-status-bar {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #0369a1;
}

/* 上傳徽章 */
.upload-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  cursor: pointer;
}

.upload-badge.done {
  background: #dcfce7;
  color: #16a34a;
}

.upload-badge.uploading {
  background: #e0f2fe;
  color: #0284c7;
  animation: pulse 1.5s ease-in-out infinite;
}

.upload-badge.error {
  background: #fef2f2;
  color: #dc2626;
}

/* 上傳按鈕 */
.upload-btn {
  border: none;
  background: #e0f2fe;
  color: #0284c7;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  transition: all 0.2s;
}

.upload-btn:hover {
  background: #0284c7;
  color: white;
}

.upload-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 旋轉動畫 */
.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useGeneratorStore } from '../stores/generator'
import { regenerateImage, uploadToImgBB, getUploadConfig } from '../api'
import PublishModal from '../components/PublishModal.vue'

const router = useRouter()
const store = useGeneratorStore()
const regeneratingIndex = ref<number | null>(null)
const showPublishModal = ref(false)
const isUploading = ref(false)
const hasImgBBKey = ref(false)

// 已上傳的圖片數量
const uploadedCount = computed(() => store.images.filter(img => img.uploadedUrl).length)
const allUploaded = computed(() => store.images.every(img => img.uploadedUrl))

// 取得圖片的完整 URL 列表（用於發布）
// 優先使用已上傳的 URL
const imageUrls = computed(() => {
  return store.images
    .filter(img => img.url)
    .sort((a, b) => a.index - b.index)
    .map(img => {
      // 優先使用已上傳的 URL
      if (img.uploadedUrl) {
        return img.uploadedUrl
      }
      const baseUrl = img.url.split('?')[0]
      return window.location.origin + baseUrl + '?thumbnail=false'
    })
})

// 檢查 ImgBB 配置
async function checkImgBBConfig() {
  try {
    const result = await getUploadConfig()
    hasImgBBKey.value = result.has_imgbb_key || false
  } catch (e) {
    hasImgBBKey.value = false
  }
}

// 單張圖片上傳
async function uploadSingleImage(image: any) {
  if (!store.taskId || image.uploadedUrl) return

  // 先檢查是否有 API Key
  if (!hasImgBBKey.value) {
    alert('請先在設定頁面配置 ImgBB API Key')
    return
  }

  store.setImageUploading(image.index)

  try {
    // 從 URL 解析出 filename
    const urlPath = image.url.split('?')[0]
    const filename = urlPath.split('/').pop() || `${image.index}.png`

    const result = await uploadToImgBB({
      taskId: store.taskId,
      filename: filename
    })

    if (result.success && result.url) {
      store.setImageUploaded(image.index, result.url)
    } else {
      store.setImageUploadError(image.index, result.error || '上傳失敗')
    }
  } catch (e: any) {
    store.setImageUploadError(image.index, e.message || '上傳失敗')
  }
}

// 一鍵上傳所有圖片
async function uploadAllImages() {
  if (!store.taskId || isUploading.value) return

  // 先檢查是否有 API Key
  if (!hasImgBBKey.value) {
    alert('請先在設定頁面配置 ImgBB API Key')
    return
  }

  isUploading.value = true

  // 取得尚未上傳的圖片
  const pendingImages = store.images.filter(img => !img.uploadedUrl && img.url)

  for (const image of pendingImages) {
    store.setImageUploading(image.index)

    try {
      const urlPath = image.url.split('?')[0]
      const filename = urlPath.split('/').pop() || `${image.index}.png`

      const result = await uploadToImgBB({
        taskId: store.taskId!,
        filename: filename
      })

      if (result.success && result.url) {
        store.setImageUploaded(image.index, result.url)
      } else {
        store.setImageUploadError(image.index, result.error || '上傳失敗')
      }
    } catch (e: any) {
      store.setImageUploadError(image.index, e.message || '上傳失敗')
    }

    // 稍微延遲避免 API 限制
    await new Promise(resolve => setTimeout(resolve, 500))
  }

  isUploading.value = false
}

// 複製 URL 到剪貼簿
function copyUrl(url: string) {
  navigator.clipboard.writeText(url).then(() => {
    // 可以加入 toast 提示
    console.log('已複製連結')
  })
}

// 頁面載入時檢查配置
checkImgBBConfig()

const viewImage = (url: string) => {
  const baseUrl = url.split('?')[0]
  window.open(baseUrl + '?thumbnail=false', '_blank')
}

const startOver = () => {
  store.reset()
  router.push('/')
}

const downloadOne = (image: any) => {
  if (image.url) {
    const link = document.createElement('a')
    const baseUrl = image.url.split('?')[0]
    link.href = baseUrl + '?thumbnail=false'
    link.download = `blog_page_${image.index + 1}.png`
    link.click()
  }
}

const downloadAll = () => {
  if (store.recordId) {
    const link = document.createElement('a')
    link.href = `/api/history/${store.recordId}/download`
    link.click()
  } else {
    store.images.forEach((image, index) => {
      if (image.url) {
        setTimeout(() => {
          const link = document.createElement('a')
          const baseUrl = image.url.split('?')[0]
          link.href = baseUrl + '?thumbnail=false'
          link.download = `blog_page_${image.index + 1}.png`
          link.click()
        }, index * 300)
      }
    })
  }
}

const handleRegenerate = async (image: any) => {
  if (!store.taskId || regeneratingIndex.value !== null) return

  regeneratingIndex.value = image.index
  try {
    // Find the page content from outline
    const pageContent = store.outline.pages.find(p => p.index === image.index)
    if (!pageContent) {
       alert('無法找到對應頁面的內容')
       return
    }

    // 構建上下文資訊
    const context = {
      fullOutline: store.outline.raw || '',
      userTopic: store.topic || ''
    }

    const result = await regenerateImage(store.taskId, pageContent, true, context)
    if (result.success && result.image_url) {
       const newUrl = result.image_url
       store.updateImage(image.index, newUrl)
    } else {
       alert('重繪失敗: ' + (result.error || '未知錯誤'))
    }
  } catch (e: any) {
    alert('重繪失敗: ' + e.message)
  } finally {
    regeneratingIndex.value = null
  }
}
</script>
