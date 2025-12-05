<template>
  <!-- 圖片供應商編輯/新增彈窗 -->
  <div v-if="visible" class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>{{ isEditing ? '編輯供應商' : '新增供應商' }}</h3>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <div class="modal-body">
        <!-- 供應商名稱（僅新增時顯示） -->
        <div class="form-group" v-if="!isEditing">
          <label>供應商名稱</label>
          <input
            type="text"
            class="form-input"
            :value="formData.name"
            @input="updateField('name', ($event.target as HTMLInputElement).value)"
            placeholder="例如: google_genai"
          />
          <span class="form-hint">唯一識別，用於區分不同供應商</span>
        </div>

        <!-- 類型選擇 -->
        <div class="form-group">
          <label>類型</label>
          <select
            class="form-select"
            :value="formData.type"
            @change="updateField('type', ($event.target as HTMLSelectElement).value)"
          >
            <option v-for="opt in typeOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>

        <!-- API Key -->
        <div class="form-group">
          <label>API Key</label>
          <input
            type="text"
            class="form-input"
            :value="formData.api_key"
            @input="updateField('api_key', ($event.target as HTMLInputElement).value)"
            :placeholder="isEditing && formData._has_api_key ? formData.api_key_masked : '輸入 API Key'"
          />
          <span class="form-hint" v-if="isEditing && formData._has_api_key">
            已設定 API Key，留空表示不修改
          </span>
        </div>

        <!-- Base URL -->
        <div class="form-group" v-if="showBaseUrl">
          <label>Base URL</label>
          <input
            type="text"
            class="form-input"
            :value="formData.base_url"
            @input="updateField('base_url', ($event.target as HTMLInputElement).value)"
            placeholder="例如: https://generativelanguage.googleapis.com"
          />
          <span class="form-hint" v-if="previewUrl">
            預覽: {{ previewUrl }}
          </span>
        </div>

        <!-- 模型 -->
        <div class="form-group">
          <label>模型</label>
          <input
            type="text"
            class="form-input"
            :value="formData.model"
            @input="updateField('model', ($event.target as HTMLInputElement).value)"
            :placeholder="modelPlaceholder"
          />
        </div>

        <!-- 端點路徑（僅 OpenAI 相容介面） -->
        <div class="form-group" v-if="showEndpointType">
          <label>API 端點路徑</label>
          <input
            type="text"
            class="form-input"
            :value="formData.endpoint_type"
            @input="updateField('endpoint_type', ($event.target as HTMLInputElement).value)"
            placeholder="例如: /v1/images/generations 或 /v1/chat/completions"
          />
          <span class="form-hint">
            常用端點：/v1/images/generations（標準圖片生成）、/v1/chat/completions（即夢等返回連結的 API）
          </span>
        </div>

        <!-- 高並行模式 -->
        <div class="form-group">
          <label class="toggle-label">
            <span>高並行模式</span>
            <div
              class="toggle-switch"
              :class="{ active: formData.high_concurrency }"
              @click="updateField('high_concurrency', !formData.high_concurrency)"
            >
              <div class="toggle-slider"></div>
            </div>
          </label>
          <span class="form-hint">
            啟用後將並行生成圖片，速度更快但對 API 品質要求較高。GCP 300$ 試用帳號不建議啟用。
          </span>
        </div>

        <!-- 短 Prompt 模式 -->
        <div class="form-group">
          <label class="toggle-label">
            <span>短 Prompt 模式</span>
            <div
              class="toggle-switch"
              :class="{ active: formData.short_prompt }"
              @click="updateField('short_prompt', !formData.short_prompt)"
            >
              <div class="toggle-slider"></div>
            </div>
          </label>
          <span class="form-hint">
            啟用後使用精簡版提示詞，適合有字元限制的 API（如即夢 1600 字元限制）。
          </span>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn" @click="$emit('close')">取消</button>
        <button
          class="btn btn-secondary"
          @click="$emit('test')"
          :disabled="testing || (!formData.api_key && !isEditing)"
        >
          <span v-if="testing" class="spinner-small"></span>
          {{ testing ? '測試中...' : '測試連線' }}
        </button>
        <button class="btn btn-primary" @click="$emit('save')">
          {{ isEditing ? '儲存' : '新增' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

/**
 * 圖片供應商編輯/新增彈窗元件
 *
 * 功能：
 * - 新增供應商
 * - 編輯現有供應商
 * - 測試連線
 * - 支援高並行模式和短 Prompt 模式開關
 */

// 定义表单数据类型
interface FormData {
  name: string
  type: string
  api_key: string
  api_key_masked?: string
  _has_api_key?: boolean
  base_url: string
  model: string
  endpoint_type?: string
  high_concurrency?: boolean
  short_prompt?: boolean
}

// 定义类型选项
interface TypeOption {
  value: string
  label: string
}

// 定义 Props
const props = defineProps<{
  visible: boolean
  isEditing: boolean
  formData: FormData
  testing: boolean
  typeOptions: TypeOption[]
}>()

// 定义 Emits
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save'): void
  (e: 'test'): void
  (e: 'update:formData', data: FormData): void
}>()

// 更新表单字段
function updateField(field: keyof FormData, value: string | boolean) {
  emit('update:formData', {
    ...props.formData,
    [field]: value
  })
}

// 是否显示 Base URL
const showBaseUrl = computed(() => {
  return ['image_api', 'google_genai'].includes(props.formData.type)
})

// 是否显示端点类型
const showEndpointType = computed(() => {
  return props.formData.type === 'image_api'
})

// 模型占位符
const modelPlaceholder = computed(() => {
  switch (props.formData.type) {
    case 'google_genai':
      return '例如: imagen-3.0-generate-002'
    case 'image_api':
      return '例如: flux-pro'
    default:
      return '例如: gpt-4o'
  }
})

// 预览 URL
const previewUrl = computed(() => {
  if (!props.formData.base_url) return ''

  const baseUrl = props.formData.base_url.replace(/\/$/, '').replace(/\/v1$/, '')
  const endpointType = props.formData.endpoint_type || '/v1/images/generations'

  switch (props.formData.type) {
    case 'image_api':
      if (endpointType.includes('chat')) {
        return `${baseUrl}/v1/chat/completions`
      }
      return `${baseUrl}/v1/images/generations`
    case 'google_genai':
      return `${baseUrl}/v1beta/models/${props.formData.model || '{model}'}:generateImages`
    default:
      return ''
  }
})
</script>

<style scoped>
/* 模态框遮罩 */
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

/* 模态框内容 */
.modal-content {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

/* 头部 */
.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color, #eee);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
  padding: 0;
  line-height: 1;
}

.close-btn:hover {
  color: #333;
}

/* 主体 */
.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

/* 表单组 */
.form-group {
  margin-bottom: 20px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-main, #1a1a1a);
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color, #eee);
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary, #ff2442);
  box-shadow: 0 0 0 3px rgba(255, 36, 66, 0.1);
}

.form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color, #eee);
  border-radius: 8px;
  font-size: 14px;
  background: white;
  cursor: pointer;
}

.form-hint {
  display: block;
  font-size: 12px;
  color: var(--text-sub, #666);
  margin-top: 6px;
}

/* Toggle 开关样式 */
.toggle-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}

.toggle-switch {
  width: 44px;
  height: 24px;
  background: #d1d5db;
  border-radius: 12px;
  position: relative;
  transition: background 0.2s;
  flex-shrink: 0;
}

.toggle-switch.active {
  background: var(--primary, #ff2442);
}

.toggle-slider {
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.toggle-switch.active .toggle-slider {
  transform: translateX(20px);
}

/* 底部 */
.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--border-color, #eee);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 按钮样式 */
.btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid var(--border-color, #eee);
  background: white;
  color: var(--text-main, #1a1a1a);
  transition: all 0.2s;
}

.btn:hover {
  background: #f5f5f5;
}

.btn-primary {
  background: var(--primary, #ff2442);
  border-color: var(--primary, #ff2442);
  color: white;
}

.btn-primary:hover {
  background: var(--primary-hover, #e61e3a);
}

.btn-secondary {
  background: #f0f0f0;
  border-color: #ddd;
  color: #333;
}

.btn-secondary:hover {
  background: #e5e5e5;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 加载动画 */
.spinner-small {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 6px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
