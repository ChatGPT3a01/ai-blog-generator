<template>
  <!-- 主题输入组合框 -->
  <div class="composer-container">
    <!-- 输入区域 -->
    <div class="composer-input-wrapper">
      <div class="search-icon-static">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M21 21L16.65 16.65M19 11C19 15.4183 15.4183 19 11 19C6.58172 19 3 15.4183 3 11C3 6.58172 6.58172 3 11 3C15.4183 3 19 6.58172 19 11Z" stroke="#999" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <textarea
        ref="textareaRef"
        :value="modelValue"
        @input="handleInput"
        class="composer-textarea"
        placeholder="輸入你的想望，例如：秋天的風，是思念的呢喃...."
        @keydown.enter.prevent="handleEnter"
        :disabled="loading"
        rows="1"
      ></textarea>
    </div>

    <!-- 已上传图片预览 -->
    <div v-if="uploadedImages.length > 0" class="uploaded-images-preview">
      <div
        v-for="(img, idx) in uploadedImages"
        :key="idx"
        class="uploaded-image-item"
      >
        <img :src="img.preview" :alt="`圖片 ${idx + 1}`" />
        <button class="remove-image-btn" @click="removeImage(idx)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
      <div class="upload-hint">
        這些圖片將用於生成封面和內容參考
      </div>
    </div>

    <!-- 風格選擇區域 -->
    <div class="style-selector-area">
      <!-- 文字風格選擇 -->
      <div class="style-group">
        <label class="style-label">文字風格</label>
        <div class="style-chips">
          <button
            v-for="style in textStyles"
            :key="style.id"
            class="style-chip"
            :class="{ active: selectedTextStyle === style.id }"
            @click="selectedTextStyle = style.id"
            :title="style.description"
          >
            {{ style.icon }} {{ style.name }}
          </button>
        </div>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="composer-toolbar">
      <div class="toolbar-left">
        <label class="tool-btn" :class="{ 'active': uploadedImages.length > 0 }" title="上傳參考圖">
          <input
            type="file"
            accept="image/*"
            multiple
            @change="handleImageUpload"
            :disabled="loading"
            style="display: none;"
          />
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <circle cx="8.5" cy="8.5" r="1.5"></circle>
            <polyline points="21 15 16 10 5 21"></polyline>
          </svg>
          <span v-if="uploadedImages.length > 0" class="badge-count">{{ uploadedImages.length }}</span>
        </label>
      </div>
      <div class="toolbar-right">
        <button
          class="btn btn-primary generate-btn"
          @click="handleGenerate"
          :disabled="!modelValue.trim() || loading"
        >
          <span v-if="loading" class="spinner-sm"></span>
          <span v-else>生成大綱</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'

/**
 * 主题输入组合框组件
 *
 * 功能：
 * - 主题文本输入（自动调整高度）
 * - 参考图片上传（最多5张）
 * - 文字風格選擇
 * - 生成按钮
 */

// 定义上传的图片类型
interface UploadedImage {
  file: File
  preview: string
}

// 文字風格定義
const textStyles = [
  // 基本風格
  { id: 'professional', name: '專業解析', icon: '📊', description: '條理清楚、重邏輯與事實，像深度教學文章' },
  { id: 'teacher', name: '教師引導', icon: '👨‍🏫', description: '一步一步帶讀者，有引導、有鋪陳' },
  { id: 'story', name: '故事敘述', icon: '📖', description: '從情境或事件切入，有轉折，結尾收斂觀點' },
  { id: 'opinion', name: '觀點評論', icon: '💭', description: '有立場、有思辨，不只是整理資料' },
  { id: 'tutorial', name: '實戰教學', icon: '🛠️', description: '步驟化、可照做，像實作教學文章' },
  { id: 'summary', name: '懶人包', icon: '📋', description: '條列重點、好掃讀、易收藏' },
  { id: 'social', name: '社群延伸', icon: '💬', description: '半口語、節奏感強，像與讀者對話' },
  { id: 'brand', name: '品牌觀點', icon: '🎯', description: '有一致價值觀、穩定語氣，建立作者形象' },
  // 作家風格
  { id: 'xuzhimo', name: '徐志摩', icon: '🌹', description: '浪漫抒情、文字唯美細膩，如詩如畫' },
  { id: 'zhangailing', name: '張愛玲', icon: '🌙', description: '精煉老練、冷靜犀利，帶著蒼涼與世故' },
  { id: 'yuguangzhong', name: '余光中', icon: '🎭', description: '優美典雅、意境悠遠，融合古典與現代' },
  { id: 'sanmao', name: '三毛', icon: '🏜️', description: '率真自然、充滿生命力，流浪者的自由' },
  { id: 'linqingxuan', name: '林清玄', icon: '🍃', description: '禪意淡然、哲理深邃，在平凡中見智慧' },
  { id: 'baixianyong', name: '白先勇', icon: '🎎', description: '細膩深沉、情感含蓄，文字優雅精緻' },
  { id: 'longyingtai', name: '龍應台', icon: '🔥', description: '犀利深刻、理性與感性兼具，有力量與溫度' },
  { id: 'liuyong', name: '劉墉', icon: '☀️', description: '溫暖勵志、平易近人，用故事說道理' }
]

// 選中的文字風格
const selectedTextStyle = ref('professional')

// 定义 Props
const props = defineProps<{
  modelValue: string
  loading: boolean
}>()

// 定义 Emits
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'generate', textStyle: string): void
  (e: 'imagesChange', images: File[]): void
}>()

/**
 * 處理生成按鈕點擊
 */
function handleGenerate() {
  emit('generate', selectedTextStyle.value)
}

// 输入框引用
const textareaRef = ref<HTMLTextAreaElement | null>(null)

// 已上传的图片
const uploadedImages = ref<UploadedImage[]>([])

/**
 * 处理输入变化
 */
function handleInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  emit('update:modelValue', target.value)
  adjustHeight()
}

/**
 * 处理回车键
 */
function handleEnter(e: KeyboardEvent) {
  if (e.shiftKey) return // 允许 Shift+Enter 换行
  emit('generate')
}

/**
 * 自动调整输入框高度
 */
function adjustHeight() {
  const el = textareaRef.value
  if (!el) return

  el.style.height = 'auto'
  const newHeight = Math.max(64, Math.min(el.scrollHeight, 200))
  el.style.height = newHeight + 'px'
}

/**
 * 处理图片上传
 */
function handleImageUpload(event: Event) {
  const target = event.target as HTMLInputElement
  if (!target.files) return

  const files = Array.from(target.files)
  files.forEach((file) => {
    // 限制最多 5 张图片
    if (uploadedImages.value.length >= 5) {
      return
    }
    // 创建预览 URL
    const preview = URL.createObjectURL(file)
    uploadedImages.value.push({ file, preview })
  })

  // 通知父组件
  emitImagesChange()

  // 清空 input，允许重复选择同一文件
  target.value = ''
}

/**
 * 移除图片
 */
function removeImage(index: number) {
  const img = uploadedImages.value[index]
  // 释放预览 URL
  URL.revokeObjectURL(img.preview)
  uploadedImages.value.splice(index, 1)

  // 通知父组件
  emitImagesChange()
}

/**
 * 通知父组件图片变化
 */
function emitImagesChange() {
  const files = uploadedImages.value.map(img => img.file)
  emit('imagesChange', files)
}

/**
 * 清理所有预览 URL
 */
function clearPreviews() {
  uploadedImages.value.forEach(img => URL.revokeObjectURL(img.preview))
  uploadedImages.value = []
}

// 组件卸载时清理
onUnmounted(() => {
  clearPreviews()
})

// 暴露方法给父组件
defineExpose({
  clearPreviews
})
</script>

<style scoped>
/* 组合框容器 */
.composer-container {
  background: white;
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.06);
}

/* 输入区域 */
.composer-input-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.search-icon-static {
  flex-shrink: 0;
  padding-top: 8px;
  color: #999;
}

.composer-textarea {
  flex: 1;
  border: none;
  outline: none;
  font-size: 16px;
  line-height: 1.6;
  resize: none;
  min-height: 44px;
  max-height: 200px;
  padding: 8px 0;
  font-family: inherit;
  color: var(--text-main, #1a1a1a);
}

.composer-textarea::placeholder {
  color: #999;
}

.composer-textarea:disabled {
  background: transparent;
  color: #999;
}

/* 已上传图片预览 */
.uploaded-images-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 12px;
  align-items: center;
}

.uploaded-image-item {
  position: relative;
  width: 60px;
  height: 60px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.uploaded-image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-image-btn {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  opacity: 0;
  transition: opacity 0.2s;
}

.uploaded-image-item:hover .remove-image-btn {
  opacity: 1;
}

.remove-image-btn:hover {
  background: var(--primary, #ff2442);
}

.upload-hint {
  flex: 1;
  font-size: 12px;
  color: var(--text-sub, #666);
  text-align: right;
}

/* 工具栏 */
.composer-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.toolbar-left {
  display: flex;
  gap: 8px;
}

.tool-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #f5f5f5;
  border: none;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
}

.tool-btn:hover {
  background: #eee;
  color: var(--primary, #ff2442);
}

.tool-btn.active {
  background: rgba(255, 36, 66, 0.1);
  color: var(--primary, #ff2442);
}

.badge-count {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  background: var(--primary, #ff2442);
  color: white;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

/* 生成按钮 */
.generate-btn {
  padding: 10px 24px;
  font-size: 15px;
  border-radius: 100px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.generate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 加载动画 */
.spinner-sm {
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 風格選擇區域 */
.style-selector-area {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.style-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.style-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-sub, #666);
}

.style-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.style-chip {
  padding: 6px 12px;
  border-radius: 20px;
  border: 1px solid #e0e0e0;
  background: #fafafa;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text-main, #333);
}

.style-chip:hover {
  border-color: var(--primary, #ff2442);
  background: #fff;
}

.style-chip.active {
  border-color: var(--primary, #ff2442);
  background: rgba(255, 36, 66, 0.1);
  color: var(--primary, #ff2442);
  font-weight: 500;
}
</style>
