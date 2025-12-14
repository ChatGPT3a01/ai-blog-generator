<template>
  <!-- 歷史記錄卡片 -->
  <div class="gallery-card">
    <!-- 封面區域 -->
    <div class="card-cover" @click="$emit('preview', record.id)">
      <img
        v-if="record.thumbnail && record.task_id"
        :src="`/api/images/${record.task_id}/${record.thumbnail}`"
        alt="cover"
        loading="lazy"
        decoding="async"
      />
      <div v-else class="cover-placeholder">
        <span>{{ record.title.charAt(0) }}</span>
      </div>

      <!-- 懸浮操作按鈕 -->
      <div class="card-overlay">
        <button class="overlay-btn" @click.stop="$emit('preview', record.id)">
          預覽
        </button>
        <button class="overlay-btn primary" @click.stop="$emit('edit', record.id)">
          編輯
        </button>
      </div>

      <!-- 狀態標識 -->
      <div class="status-badge" :class="record.status">
        {{ statusText }}
      </div>
    </div>

    <!-- 底部資訊 -->
    <div class="card-footer">
      <div class="card-title" :title="record.title">{{ record.title }}</div>
      <div class="card-meta">
        <span>{{ record.page_count }}P</span>
        <span class="dot">·</span>
        <span>{{ formattedDate }}</span>

        <div class="more-actions-wrapper">
          <button class="more-btn" @click.stop="$emit('delete', record)">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

/**
 * 歷史記錄卡片元件
 *
 * 展示單個歷史記錄的封面、標題、狀態等資訊
 * 支持預覽、編輯、刪除操作
 */

// 定義記錄類型
interface Record {
  id: string
  title: string
  status: 'draft' | 'completed' | 'generating'
  page_count: number
  updated_at: string
  thumbnail?: string
  task_id?: string
}

// 定義 Props
const props = defineProps<{
  record: Record
}>()

// 定義 Emits
defineEmits<{
  (e: 'preview', id: string): void
  (e: 'edit', id: string): void
  (e: 'delete', record: Record): void
}>()

/**
 * 取得狀態文字
 */
const statusText = computed(() => {
  const map: Record<string, string> = {
    draft: '草稿',
    completed: '已完成',
    generating: '生成中'
  }
  return map[props.record.status] || props.record.status
})

/**
 * 格式化日期
 */
const formattedDate = computed(() => {
  const d = new Date(props.record.updated_at)
  return `${d.getMonth() + 1}/${d.getDate()}`
})
</script>

<style scoped>
/* 卡片容器 */
.gallery-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.04);
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1),
              box-shadow 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  will-change: transform;
  contain: layout style paint;
}

.gallery-card:hover {
  transform: translateY(-4px) translateZ(0);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
}

/* 封面區域 */
.card-cover {
  aspect-ratio: 3/4;
  background: #f7f7f7;
  position: relative;
  overflow: hidden;
  cursor: pointer;
}

.card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  will-change: transform;
  backface-visibility: hidden;
}

.gallery-card:hover .card-cover img {
  transform: scale(1.05) translateZ(0);
}

/* 封面佔位符 */
.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  color: #e0e0e0;
  font-weight: 800;
  background: #fafafa;
}

/* 懸浮遮罩層 */
.card-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  opacity: 0;
  transition: opacity 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(2px);
  pointer-events: none;
  will-change: opacity;
}

.gallery-card:hover .card-overlay {
  opacity: 1;
  pointer-events: auto;
}

/* 遮罩層按鈕 */
.overlay-btn {
  padding: 8px 24px;
  border-radius: 100px;
  border: 1px solid rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.2);
  color: white;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s, transform 0.1s;
  will-change: transform;
}

.overlay-btn:hover {
  background: white;
  color: var(--text-main, #1a1a1a);
  transform: translateY(-2px);
}

.overlay-btn.primary {
  background: var(--primary, #ff2442);
  border-color: var(--primary, #ff2442);
}

.overlay-btn.primary:hover {
  background: var(--primary-hover, #e61e3a);
  color: white;
}

/* 狀態標識 */
.status-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  backdrop-filter: blur(4px);
}

.status-badge.completed {
  background: rgba(82, 196, 26, 0.9);
}

.status-badge.draft {
  background: rgba(0, 0, 0, 0.5);
}

.status-badge.generating {
  background: rgba(24, 144, 255, 0.9);
}

/* 底部區域 */
.card-footer {
  padding: 16px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--text-main, #1a1a1a);
}

.card-meta {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: var(--text-sub, #666);
}

.dot {
  margin: 0 6px;
}

/* 更多操作 */
.more-actions-wrapper {
  margin-left: auto;
}

.more-btn {
  background: none;
  border: none;
  color: var(--text-placeholder, #ccc);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.2s, color 0.2s;
}

.more-btn:hover {
  background: #fee;
  color: #ff4d4f;
}
</style>
