<template>
  <div class="container">
    <div class="page-header">
      <h1 class="page-title">系統設定</h1>
      <p class="page-subtitle">設定文字生成和圖片生成的 API 服務</p>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>載入設定中...</p>
    </div>

    <div v-else class="settings-container">
      <!-- 文字生成設定 -->
      <div class="card">
        <div class="section-header">
          <div>
            <h2 class="section-title">文字生成設定</h2>
            <p class="section-desc">用於生成部落格圖文大綱</p>
          </div>
          <button class="btn btn-small" @click="openAddTextModal">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            新增
          </button>
        </div>

        <!-- 供應商清單表格 -->
        <ProviderTable
          :providers="textConfig.providers"
          :activeProvider="textConfig.active_provider"
          @activate="activateTextProvider"
          @edit="openEditTextModal"
          @delete="deleteTextProvider"
          @test="testTextProviderInList"
        />
      </div>

      <!-- 圖片生成設定 -->
      <div class="card">
        <div class="section-header">
          <div>
            <h2 class="section-title">圖片生成設定</h2>
            <p class="section-desc">用於生成部落格配圖</p>
          </div>
          <button class="btn btn-small" @click="openAddImageModal">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            新增
          </button>
        </div>

        <!-- 供應商清單表格 -->
        <ProviderTable
          :providers="imageConfig.providers"
          :activeProvider="imageConfig.active_provider"
          @activate="activateImageProvider"
          @edit="openEditImageModal"
          @delete="deleteImageProvider"
          @test="testImageProviderInList"
        />
      </div>

      <!-- 圖床設定 -->
      <div class="card">
        <div class="section-header">
          <div>
            <h2 class="section-title">圖床設定 (ImgBB)</h2>
            <p class="section-desc">用於上傳圖片到圖床，取得公開 URL 以便發布到 Blogger</p>
          </div>
        </div>

        <div class="imgbb-config">
          <div class="form-group">
            <label class="form-label">ImgBB API Key</label>
            <div style="display: flex; gap: 12px;">
              <input
                type="password"
                v-model="imgbbApiKey"
                placeholder="請輸入 ImgBB API Key"
                class="form-input"
                style="flex: 1;"
              />
              <button
                class="btn btn-primary"
                @click="saveImgBBConfig"
                :disabled="savingImgBB"
              >
                {{ savingImgBB ? '儲存中...' : '儲存' }}
              </button>
            </div>
            <p class="form-hint">
              <a href="https://api.imgbb.com/" target="_blank" style="color: var(--primary);">
                點此前往 ImgBB 取得免費 API Key
              </a>
            </p>
          </div>

          <div v-if="hasImgBBKey" class="status-success">
            已設定 API Key
          </div>
        </div>
      </div>

      <!-- Unsplash 備用圖庫設定 -->
      <div class="card">
        <div class="section-header">
          <div>
            <h2 class="section-title">Unsplash 備用圖庫</h2>
            <p class="section-desc">當 AI 圖片生成失敗時，可從 Unsplash 圖庫選擇替代圖片</p>
          </div>
        </div>

        <div class="unsplash-config">
          <div class="form-group">
            <label class="form-label">Unsplash Access Key</label>
            <div style="display: flex; gap: 12px;">
              <input
                type="password"
                v-model="unsplashApiKey"
                placeholder="請輸入 Unsplash Access Key"
                class="form-input"
                style="flex: 1;"
              />
              <button
                class="btn btn-primary"
                @click="saveUnsplashConfig"
                :disabled="savingUnsplash"
              >
                {{ savingUnsplash ? '儲存中...' : '儲存' }}
              </button>
            </div>
          </div>

          <!-- 教學說明 -->
          <div class="api-guide">
            <h4>如何取得 Unsplash Access Key？</h4>
            <ol>
              <li>前往 <a href="https://unsplash.com/developers" target="_blank">Unsplash Developers</a> 網站</li>
              <li>註冊或登入 Unsplash 帳號</li>
              <li>點擊「Your apps」→「New Application」</li>
              <li>填寫應用程式名稱和說明（可隨意填寫）</li>
              <li>勾選同意條款，建立應用程式</li>
              <li>複製「Access Key」（不是 Secret Key）</li>
              <li>將 Access Key 貼到上方輸入框並儲存</li>
            </ol>
            <p class="note">Unsplash API 免費版每月可搜尋 50 次，足夠一般使用。</p>
          </div>

          <div v-if="hasUnsplashKey" class="status-success">
            已設定 Access Key
          </div>
        </div>
      </div>
    </div>

    <!-- 文字供應商彈窗 -->
    <ProviderModal
      :visible="showTextModal"
      :isEditing="!!editingTextProvider"
      :formData="textForm"
      :testing="testingText"
      :typeOptions="textTypeOptions"
      providerCategory="text"
      @close="closeTextModal"
      @save="saveTextProvider"
      @test="testTextConnection"
      @update:formData="updateTextForm"
    />

    <!-- 圖片供應商彈窗 -->
    <ImageProviderModal
      :visible="showImageModal"
      :isEditing="!!editingImageProvider"
      :formData="imageForm"
      :testing="testingImage"
      :typeOptions="imageTypeOptions"
      @close="closeImageModal"
      @save="saveImageProvider"
      @test="testImageConnection"
      @update:formData="updateImageForm"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import ProviderTable from '../components/settings/ProviderTable.vue'
import ProviderModal from '../components/settings/ProviderModal.vue'
import ImageProviderModal from '../components/settings/ImageProviderModal.vue'
import {
  useProviderForm,
  textTypeOptions,
  imageTypeOptions
} from '../composables/useProviderForm'
import { getUploadConfig, updateUploadConfig, getUnsplashConfig, updateUnsplashConfig } from '../api'

/**
 * 系統設定頁面
 *
 * 功能：
 * - 管理文字生成供應商設定
 * - 管理圖片生成供應商設定
 * - 測試 API 連線
 * - 管理 ImgBB 圖床設定
 */

// ImgBB 配置狀態
const imgbbApiKey = ref('')
const hasImgBBKey = ref(false)
const savingImgBB = ref(false)

// Unsplash 配置狀態
const unsplashApiKey = ref('')
const hasUnsplashKey = ref(false)
const savingUnsplash = ref(false)

// 載入 ImgBB 配置
async function loadImgBBConfig() {
  try {
    const result = await getUploadConfig()
    hasImgBBKey.value = result.has_imgbb_key || false
  } catch (e) {
    console.error('載入 ImgBB 配置失敗:', e)
  }
}

// 儲存 ImgBB 配置
async function saveImgBBConfig() {
  if (!imgbbApiKey.value.trim()) {
    alert('請輸入 API Key')
    return
  }

  savingImgBB.value = true
  try {
    const result = await updateUploadConfig(imgbbApiKey.value.trim())
    if (result.success) {
      hasImgBBKey.value = true
      imgbbApiKey.value = ''
      alert('ImgBB API Key 已儲存')
    } else {
      alert('儲存失敗: ' + (result.error || '未知錯誤'))
    }
  } catch (e: any) {
    alert('儲存失敗: ' + e.message)
  } finally {
    savingImgBB.value = false
  }
}

// 載入 Unsplash 配置
async function loadUnsplashConfig() {
  try {
    const result = await getUnsplashConfig()
    hasUnsplashKey.value = result.has_api_key || false
  } catch (e) {
    console.error('載入 Unsplash 配置失敗:', e)
  }
}

// 儲存 Unsplash 配置
async function saveUnsplashConfig() {
  if (!unsplashApiKey.value.trim()) {
    alert('請輸入 Access Key')
    return
  }

  savingUnsplash.value = true
  try {
    const result = await updateUnsplashConfig(unsplashApiKey.value.trim())
    if (result.success) {
      hasUnsplashKey.value = true
      unsplashApiKey.value = ''
      alert('Unsplash Access Key 已儲存')
    } else {
      alert('儲存失敗: ' + (result.error || '未知錯誤'))
    }
  } catch (e: any) {
    alert('儲存失敗: ' + e.message)
  } finally {
    savingUnsplash.value = false
  }
}

// 使用 composable 管理表單狀態和邏輯
const {
  // 狀態
  loading,
  testingText,
  testingImage,

  // 設定資料
  textConfig,
  imageConfig,

  // 文字供應商彈窗
  showTextModal,
  editingTextProvider,
  textForm,

  // 圖片供應商彈窗
  showImageModal,
  editingImageProvider,
  imageForm,

  // 方法
  loadConfig,

  // 文字供應商方法
  activateTextProvider,
  openAddTextModal,
  openEditTextModal,
  closeTextModal,
  saveTextProvider,
  deleteTextProvider,
  testTextConnection,
  testTextProviderInList,
  updateTextForm,

  // 圖片供應商方法
  activateImageProvider,
  openAddImageModal,
  openEditImageModal,
  closeImageModal,
  saveImageProvider,
  deleteImageProvider,
  testImageConnection,
  testImageProviderInList,
  updateImageForm
} = useProviderForm()

onMounted(() => {
  loadConfig()
  loadImgBBConfig()
  loadUnsplashConfig()
})
</script>

<style scoped>
.settings-container {
  max-width: 900px;
  margin: 0 auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
  color: #1a1a1a;
}

.section-desc {
  font-size: 14px;
  color: #666;
  margin: 0;
}

/* 按鈕樣式 */
.btn-small {
  padding: 6px 12px;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

/* 載入狀態 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #666;
}

/* ImgBB 配置區 */
.imgbb-config {
  padding-top: 8px;
}

.form-group {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.form-input {
  padding: 10px 14px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary);
}

.form-hint {
  font-size: 12px;
  color: #888;
  margin-top: 8px;
}

.status-success {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #dcfce7;
  color: #16a34a;
  border-radius: 6px;
  font-size: 13px;
}

/* Unsplash 配置區 */
.unsplash-config {
  padding-top: 8px;
}

/* API 教學說明 */
.api-guide {
  margin-top: 16px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 3px solid var(--primary);
}

.api-guide h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.api-guide ol {
  margin: 0;
  padding-left: 20px;
  font-size: 13px;
  color: #555;
  line-height: 1.8;
}

.api-guide li {
  margin-bottom: 4px;
}

.api-guide a {
  color: var(--primary);
  text-decoration: none;
}

.api-guide a:hover {
  text-decoration: underline;
}

.api-guide .note {
  margin: 12px 0 0 0;
  font-size: 12px;
  color: #888;
  font-style: italic;
}
</style>
