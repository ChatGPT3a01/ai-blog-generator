<template>
  <!-- 備用圖片選擇彈窗 -->
  <div v-if="visible" class="modal-overlay" @click="handleClose">
    <div class="modal-content" @click.stop>
      <!-- 標頭 -->
      <div class="modal-header">
        <div>
          <h3>選擇替代圖片</h3>
          <p class="header-subtitle">第 {{ pageIndex + 1 }} 頁圖片生成失敗，請選擇替代方案</p>
        </div>
        <button class="close-btn" @click="handleClose">&times;</button>
      </div>

      <!-- 選項卡 -->
      <div class="modal-tabs">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'unsplash' }"
          @click="activeTab = 'unsplash'"
        >
          Unsplash 圖庫
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'upload' }"
          @click="activeTab = 'upload'"
        >
          上傳圖片
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'skip' }"
          @click="activeTab = 'skip'"
        >
          跳過
        </button>
      </div>

      <!-- 主體內容 -->
      <div class="modal-body">
        <!-- Unsplash 搜尋 -->
        <div v-if="activeTab === 'unsplash'" class="unsplash-section">
          <!-- 搜尋框 -->
          <div class="search-bar">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="輸入關鍵字搜尋..."
              @keyup.enter="searchPhotos"
              class="search-input"
            />
            <button
              class="btn btn-primary"
              @click="searchPhotos"
              :disabled="searching || !searchQuery.trim()"
            >
              {{ searching ? '搜尋中...' : '搜尋' }}
            </button>
          </div>

          <!-- 沒有設定 API Key 提示 -->
          <div v-if="!hasUnsplashKey" class="no-key-hint">
            <p>尚未設定 Unsplash API Key</p>
            <router-link to="/settings" class="link" @click="handleClose">前往設定</router-link>
          </div>

          <!-- 圖片網格 -->
          <div v-else-if="photos.length > 0" class="photo-grid">
            <div
              v-for="photo in photos"
              :key="photo.id"
              class="photo-item"
              :class="{ selected: selectedPhoto?.id === photo.id }"
              @click="selectPhoto(photo)"
            >
              <img :src="photo.small" :alt="photo.alt" loading="lazy" />
              <div class="photo-credit">
                Photo by {{ photo.photographer }}
              </div>
              <div v-if="selectedPhoto?.id === photo.id" class="selected-badge">
                已選擇
              </div>
            </div>
          </div>

          <!-- 空狀態 -->
          <div v-else-if="searched" class="empty-state">
            <p>找不到相關圖片，請嘗試其他關鍵字</p>
          </div>

          <!-- 初始提示 -->
          <div v-else class="empty-state">
            <p>輸入關鍵字搜尋免費高品質圖片</p>
          </div>
        </div>

        <!-- 上傳圖片 -->
        <div v-if="activeTab === 'upload'" class="upload-section">
          <div
            class="upload-area"
            :class="{ dragover: isDragging }"
            @drop.prevent="handleDrop"
            @dragover.prevent="isDragging = true"
            @dragleave="isDragging = false"
            @click="triggerFileInput"
          >
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              @change="handleFileSelect"
              style="display: none;"
            />
            <div v-if="uploadPreview" class="preview-container">
              <img :src="uploadPreview" alt="預覽" />
              <button class="remove-btn" @click.stop="clearUpload">移除</button>
            </div>
            <div v-else class="upload-placeholder">
              <div class="upload-icon">+</div>
              <p>拖曳圖片至此或點擊上傳</p>
              <p class="hint">支援 JPG、PNG 格式</p>
            </div>
          </div>
        </div>

        <!-- 跳過選項 -->
        <div v-if="activeTab === 'skip'" class="skip-section">
          <div class="skip-content">
            <div class="skip-icon">—</div>
            <p>選擇跳過將不會為此頁面使用任何圖片</p>
            <p class="hint">您之後仍可重新生成或選擇替代圖片</p>
          </div>
        </div>
      </div>

      <!-- 底部按鈕 -->
      <div class="modal-footer">
        <button class="btn" @click="handleClose">取消</button>
        <button
          class="btn btn-primary"
          @click="handleConfirm"
          :disabled="!canConfirm || confirming"
        >
          {{ confirming ? '處理中...' : confirmText }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  searchUnsplashPhotos,
  downloadUnsplashPhoto,
  getUnsplashConfig,
  type UnsplashPhoto
} from '../api'

const props = defineProps<{
  visible: boolean
  pageIndex: number
  taskId: string
  suggestedKeyword?: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'select', data: { type: 'unsplash' | 'upload' | 'skip', imageUrl?: string }): void
}>()

// 狀態
const activeTab = ref<'unsplash' | 'upload' | 'skip'>('unsplash')
const hasUnsplashKey = ref(false)
const searchQuery = ref('')
const searching = ref(false)
const searched = ref(false)
const photos = ref<UnsplashPhoto[]>([])
const selectedPhoto = ref<UnsplashPhoto | null>(null)
const uploadPreview = ref<string | null>(null)
const uploadFile = ref<File | null>(null)
const isDragging = ref(false)
const confirming = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

// 計算屬性
const canConfirm = computed(() => {
  if (activeTab.value === 'unsplash') return !!selectedPhoto.value
  if (activeTab.value === 'upload') return !!uploadFile.value
  if (activeTab.value === 'skip') return true
  return false
})

const confirmText = computed(() => {
  if (activeTab.value === 'unsplash') return '使用此圖片'
  if (activeTab.value === 'upload') return '上傳並使用'
  if (activeTab.value === 'skip') return '跳過此張'
  return '確認'
})

// 初始化
onMounted(async () => {
  try {
    const config = await getUnsplashConfig()
    hasUnsplashKey.value = config.has_api_key || false
  } catch (e) {
    hasUnsplashKey.value = false
  }

  if (props.suggestedKeyword) {
    searchQuery.value = props.suggestedKeyword
    if (hasUnsplashKey.value) {
      searchPhotos()
    }
  }
})

// 監聽顯示狀態
watch(() => props.visible, (newVal) => {
  if (newVal && props.suggestedKeyword && !searchQuery.value) {
    searchQuery.value = props.suggestedKeyword
  }
})

// 搜尋圖片
async function searchPhotos() {
  if (!searchQuery.value.trim() || searching.value) return

  searching.value = true
  searched.value = false
  selectedPhoto.value = null

  try {
    const result = await searchUnsplashPhotos({
      query: searchQuery.value,
      perPage: 8,
      orientation: 'landscape'
    })

    if (result.success && result.photos) {
      photos.value = result.photos
    } else {
      photos.value = []
    }
    searched.value = true
  } catch (e) {
    console.error('搜尋失敗:', e)
    photos.value = []
  } finally {
    searching.value = false
  }
}

// 選擇圖片
function selectPhoto(photo: UnsplashPhoto) {
  if (selectedPhoto.value?.id === photo.id) {
    selectedPhoto.value = null
  } else {
    selectedPhoto.value = photo
  }
}

// 檔案上傳相關
function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    processFile(input.files[0])
  }
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
    processFile(event.dataTransfer.files[0])
  }
}

function processFile(file: File) {
  if (!file.type.startsWith('image/')) {
    alert('請選擇圖片檔案')
    return
  }

  uploadFile.value = file
  const reader = new FileReader()
  reader.onload = (e) => {
    uploadPreview.value = e.target?.result as string
  }
  reader.readAsDataURL(file)
}

function clearUpload() {
  uploadFile.value = null
  uploadPreview.value = null
}

// 關閉彈窗
function handleClose() {
  emit('close')
}

// 確認選擇
async function handleConfirm() {
  confirming.value = true

  try {
    if (activeTab.value === 'unsplash' && selectedPhoto.value) {
      // 下載 Unsplash 圖片
      const result = await downloadUnsplashPhoto({
        photoUrl: selectedPhoto.value.regular,
        taskId: props.taskId,
        index: props.pageIndex,
        photoId: selectedPhoto.value.id
      })

      if (result.success && result.image_url) {
        emit('select', { type: 'unsplash', imageUrl: result.image_url })
      } else {
        alert('下載圖片失敗: ' + (result.error || '未知錯誤'))
        return
      }
    } else if (activeTab.value === 'upload' && uploadFile.value) {
      // 上傳自訂圖片
      emit('select', { type: 'upload', imageUrl: uploadPreview.value || undefined })
    } else if (activeTab.value === 'skip') {
      emit('select', { type: 'skip' })
    }
  } catch (e) {
    console.error('處理失敗:', e)
    alert('處理失敗: ' + String(e))
  } finally {
    confirming.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 700px;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color, #eee);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.modal-header h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
}

.header-subtitle {
  margin: 0;
  font-size: 13px;
  color: var(--text-sub, #666);
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: #999;
  line-height: 1;
}

.modal-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-color, #eee);
}

.tab-btn {
  flex: 1;
  padding: 12px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-sub, #666);
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab-btn.active {
  color: var(--primary, #ff2442);
  border-bottom-color: var(--primary, #ff2442);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  min-height: 300px;
}

/* Unsplash 區塊 */
.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.search-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border-color, #eee);
  border-radius: 8px;
  font-size: 14px;
}

.photo-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.photo-item {
  position: relative;
  aspect-ratio: 4/3;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.photo-item:hover {
  border-color: var(--primary, #ff2442);
}

.photo-item.selected {
  border-color: var(--primary, #ff2442);
}

.photo-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-credit {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0,0,0,0.7));
  color: white;
  padding: 20px 8px 8px;
  font-size: 10px;
}

.selected-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: var(--primary, #ff2442);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
}

.no-key-hint, .empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-sub, #666);
}

.link {
  color: var(--primary, #ff2442);
}

/* 上傳區塊 */
.upload-area {
  border: 2px dashed var(--border-color, #ddd);
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-area:hover, .upload-area.dragover {
  border-color: var(--primary, #ff2442);
  background: rgba(255, 36, 66, 0.02);
}

.upload-placeholder {
  color: var(--text-sub, #666);
}

.upload-icon {
  font-size: 48px;
  color: var(--primary, #ff2442);
  margin-bottom: 12px;
}

.preview-container {
  position: relative;
  display: inline-block;
}

.preview-container img {
  max-width: 300px;
  max-height: 200px;
  border-radius: 8px;
}

.remove-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0,0,0,0.6);
  color: white;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
}

/* 跳過區塊 */
.skip-section {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.skip-content {
  text-align: center;
  color: var(--text-sub, #666);
}

.skip-icon {
  font-size: 48px;
  color: #ccc;
  margin-bottom: 16px;
}

.hint {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

/* 底部 */
.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--border-color, #eee);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  border: 1px solid var(--border-color, #eee);
  background: white;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--primary, #ff2442);
  border-color: var(--primary, #ff2442);
  color: white;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
