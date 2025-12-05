<template>
  <!-- 供應商清單表格 -->
  <div class="provider-table">
    <div class="table-header">
      <div class="col-status">狀態</div>
      <div class="col-name">名稱</div>
      <div class="col-model">模型</div>
      <div class="col-apikey">API Key</div>
      <div class="col-actions">操作</div>
    </div>
    <div
      v-for="(provider, name) in providers"
      :key="name"
      class="table-row"
      :class="{ active: activeProvider === name }"
    >
      <div class="col-status">
        <button
          class="btn-activate"
          :class="{ active: activeProvider === name }"
          @click="$emit('activate', name)"
          :disabled="activeProvider === name"
        >
          {{ activeProvider === name ? '已啟用' : '啟用' }}
        </button>
      </div>
      <div class="col-name">
        <span class="provider-name">{{ name }}</span>
      </div>
      <div class="col-model">
        <span class="model-name">{{ provider.model }}</span>
      </div>
      <div class="col-apikey">
        <span class="apikey-masked" :class="{ empty: !provider.api_key_masked }">
          {{ provider.api_key_masked || '未設定' }}
        </span>
      </div>
      <div class="col-actions">
        <button class="btn-icon" @click="$emit('test', name, provider)" title="測試連線">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
          </svg>
        </button>
        <button class="btn-icon" @click="$emit('edit', name, provider)" title="編輯">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
          </svg>
        </button>
        <button
          class="btn-icon danger"
          @click="$emit('delete', name)"
          v-if="canDelete"
          title="刪除"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

/**
 * 供應商清單表格元件
 *
 * 功能：
 * - 展示供應商清單
 * - 啟用/編輯/刪除/測試操作
 */

// 定義供應商類型
interface Provider {
  type: string
  model: string
  base_url?: string
  api_key?: string
  api_key_masked?: string
}

// 定義 Props
const props = defineProps<{
  providers: Record<string, Provider>
  activeProvider: string
}>()

// 定義 Emits
defineEmits<{
  (e: 'activate', name: string): void
  (e: 'edit', name: string, provider: Provider): void
  (e: 'delete', name: string): void
  (e: 'test', name: string, provider: Provider): void
}>()

// 是否可以刪除（至少保留一個）
const canDelete = computed(() => Object.keys(props.providers).length > 1)
</script>

<style scoped>
/* 表格容器 */
.provider-table {
  border: 1px solid var(--border-color, #eee);
  border-radius: 8px;
  overflow: hidden;
}

/* 表頭 */
.table-header {
  display: grid;
  grid-template-columns: 80px 1fr 1fr 1.5fr 120px;
  gap: 12px;
  padding: 12px 16px;
  background: #f9fafb;
  border-bottom: 1px solid var(--border-color, #eee);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-sub, #666);
  text-transform: uppercase;
}

/* 表格列 */
.table-row {
  display: grid;
  grid-template-columns: 80px 1fr 1fr 1.5fr 120px;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-color, #eee);
  align-items: center;
  transition: background-color 0.2s;
}

.table-row:last-child {
  border-bottom: none;
}

.table-row:hover {
  background: #f9fafb;
}

.table-row.active {
  background: rgba(255, 36, 66, 0.02);
}

/* 啟用按鈕 */
.btn-activate {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid var(--border-color, #eee);
  background: white;
  color: var(--text-sub, #666);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-activate:hover:not(:disabled) {
  border-color: var(--primary, #ff2442);
  color: var(--primary, #ff2442);
}

.btn-activate.active {
  background: rgba(34, 197, 94, 0.1);
  border-color: #22c55e;
  color: #22c55e;
  cursor: default;
}

/* 供應商名稱 */
.provider-name {
  font-weight: 600;
  color: var(--text-main, #1a1a1a);
}

/* 模型名稱 */
.model-name {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  color: var(--text-sub, #666);
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
}

/* API Key 顯示 */
.apikey-masked {
  font-size: 12px;
  font-family: 'Monaco', 'Menlo', monospace;
  color: #6b7280;
  word-break: break-all;
}

.apikey-masked.empty {
  color: #f59e0b;
}

/* 操作列 */
.col-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* 圖標按鈕 */
.btn-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 1px solid var(--border-color, #eee);
  background: white;
  color: var(--text-sub, #666);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-icon:hover {
  border-color: var(--primary, #ff2442);
  color: var(--primary, #ff2442);
  background: rgba(255, 36, 66, 0.05);
}

.btn-icon.danger:hover {
  border-color: #ef4444;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.05);
}

/* 響應式 */
@media (max-width: 768px) {
  .table-header,
  .table-row {
    grid-template-columns: 70px 1fr 100px;
  }

  .col-model,
  .col-apikey {
    display: none;
  }
}
</style>
