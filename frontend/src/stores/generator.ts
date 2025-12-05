import { defineStore } from 'pinia'
import type { Page } from '../api'

export interface GeneratedImage {
  index: number
  url: string
  status: 'generating' | 'done' | 'error' | 'retrying'
  error?: string
  retryable?: boolean
}

export interface GeneratorState {
  // 當前階段
  stage: 'input' | 'outline' | 'generating' | 'result'

  // 使用者輸入
  topic: string

  // 大綱資料
  outline: {
    raw: string
    pages: Page[]
  }

  // 生成進度
  progress: {
    current: number
    total: number
    status: 'idle' | 'generating' | 'done' | 'error'
  }

  // 生成結果
  images: GeneratedImage[]

  // 任務ID
  taskId: string | null

  // 歷史記錄ID
  recordId: string | null

  // 使用者上傳的圖片（用於圖片生成參考）
  userImages: File[]
}

const STORAGE_KEY = 'generator-state'

// 從 localStorage 載入狀態
function loadState(): Partial<GeneratorState> {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (e) {
    console.error('載入狀態失敗:', e)
  }
  return {}
}

// 儲存狀態到 localStorage
function saveState(state: GeneratorState) {
  try {
    // 只儲存關鍵資料，不儲存 userImages（檔案物件無法序列化）
    const toSave = {
      stage: state.stage,
      topic: state.topic,
      outline: state.outline,
      progress: state.progress,
      images: state.images,
      taskId: state.taskId,
      recordId: state.recordId
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave))
  } catch (e) {
    console.error('儲存狀態失敗:', e)
  }
}

export const useGeneratorStore = defineStore('generator', {
  state: (): GeneratorState => {
    const saved = loadState()
    return {
      stage: saved.stage || 'input',
      topic: saved.topic || '',
      outline: saved.outline || {
        raw: '',
        pages: []
      },
      progress: saved.progress || {
        current: 0,
        total: 0,
        status: 'idle'
      },
      images: saved.images || [],
      taskId: saved.taskId || null,
      recordId: saved.recordId || null,
      userImages: []  // 不從 localStorage 恢復
    }
  },

  actions: {
    // 設定主題
    setTopic(topic: string) {
      this.topic = topic
    },

    // 設定大綱
    setOutline(raw: string, pages: Page[]) {
      this.outline.raw = raw
      this.outline.pages = pages
      this.stage = 'outline'
    },

    // 更新頁面
    updatePage(index: number, content: string) {
      const page = this.outline.pages.find(p => p.index === index)
      if (page) {
        page.content = content
        // 同步更新 raw 文字
        this.syncRawFromPages()
      }
    },

    // 根據 pages 重新生成 raw 文字
    syncRawFromPages() {
      this.outline.raw = this.outline.pages
        .map(page => page.content)
        .join('\n\n<page>\n\n')
    },

    // 刪除頁面
    deletePage(index: number) {
      this.outline.pages = this.outline.pages.filter(p => p.index !== index)
      // 重新索引
      this.outline.pages.forEach((page, idx) => {
        page.index = idx
      })
      // 同步更新 raw 文字
      this.syncRawFromPages()
    },

    // 新增頁面
    addPage(type: 'cover' | 'content' | 'summary', content: string = '') {
      const newPage: Page = {
        index: this.outline.pages.length,
        type,
        content
      }
      this.outline.pages.push(newPage)
      // 同步更新 raw 文字
      this.syncRawFromPages()
    },

    // 插入頁面
    insertPage(afterIndex: number, type: 'cover' | 'content' | 'summary', content: string = '') {
      const newPage: Page = {
        index: afterIndex + 1,
        type,
        content
      }
      this.outline.pages.splice(afterIndex + 1, 0, newPage)
      // 重新索引
      this.outline.pages.forEach((page, idx) => {
        page.index = idx
      })
      // 同步更新 raw 文字
      this.syncRawFromPages()
    },

    // 移動頁面（拖曳排序）
    movePage(fromIndex: number, toIndex: number) {
      const pages = [...this.outline.pages]
      const [movedPage] = pages.splice(fromIndex, 1)
      pages.splice(toIndex, 0, movedPage)

      // 重新索引
      pages.forEach((page, idx) => {
        page.index = idx
      })

      this.outline.pages = pages
      // 同步更新 raw 文字
      this.syncRawFromPages()
    },

    // 開始生成
    startGeneration() {
      this.stage = 'generating'
      this.progress.current = 0
      this.progress.total = this.outline.pages.length
      this.progress.status = 'generating'
      this.images = this.outline.pages.map(page => ({
        index: page.index,
        url: '',
        status: 'generating'
      }))
    },

    // 更新進度
    updateProgress(index: number, status: 'generating' | 'done' | 'error', url?: string, error?: string) {
      const image = this.images.find(img => img.index === index)
      if (image) {
        image.status = status
        if (url) image.url = url
        if (error) image.error = error
      }
      if (status === 'done') {
        this.progress.current++
      }
    },

    updateImage(index: number, newUrl: string) {
      const image = this.images.find(img => img.index === index)
      if (image) {
        const timestamp = Date.now()
        image.url = `${newUrl}?t=${timestamp}`
        image.status = 'done'
        delete image.error
      }
    },

    // 完成生成
    finishGeneration(taskId: string) {
      this.taskId = taskId
      this.stage = 'result'
      this.progress.status = 'done'
    },

    // 設定單個圖片為重試中狀態
    setImageRetrying(index: number) {
      const image = this.images.find(img => img.index === index)
      if (image) {
        image.status = 'retrying'
      }
    },

    // 取得失敗的圖片清單
    getFailedImages() {
      return this.images.filter(img => img.status === 'error')
    },

    // 取得失敗圖片對應的頁面
    getFailedPages() {
      const failedIndices = this.images
        .filter(img => img.status === 'error')
        .map(img => img.index)
      return this.outline.pages.filter(page => failedIndices.includes(page.index))
    },

    // 檢查是否有失敗的圖片
    hasFailedImages() {
      return this.images.some(img => img.status === 'error')
    },

    // 重置
    reset() {
      this.stage = 'input'
      this.topic = ''
      this.outline = {
        raw: '',
        pages: []
      }
      this.progress = {
        current: 0,
        total: 0,
        status: 'idle'
      }
      this.images = []
      this.taskId = null
      this.recordId = null
      this.userImages = []
      // 清除 localStorage
      localStorage.removeItem(STORAGE_KEY)
    },

    // 儲存當前狀態
    saveToStorage() {
      saveState(this)
    }
  }
})

// 監聽狀態變化並自動儲存（使用 watch）
import { watch } from 'vue'

export function setupAutoSave() {
  const store = useGeneratorStore()

  // 監聽關鍵欄位變化並自動儲存
  watch(
    () => ({
      stage: store.stage,
      topic: store.topic,
      outline: store.outline,
      progress: store.progress,
      images: store.images,
      taskId: store.taskId,
      recordId: store.recordId
    }),
    () => {
      store.saveToStorage()
    },
    { deep: true }
  )
}
