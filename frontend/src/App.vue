<template>
  <div id="app">
    <!-- 側邊欄 Sidebar -->
    <aside class="layout-sidebar">
      <div class="logo-area">
        <img src="/logo.png" alt="3A科技實驗室" class="logo-icon" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />
        <span class="logo-text">亮言AI</span>
      </div>

      <nav class="nav-menu">
        <RouterLink to="/" class="nav-item" active-class="active">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
          創作中心
        </RouterLink>
        <RouterLink to="/history" class="nav-item" active-class="active">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
          歷史記錄
        </RouterLink>
        <RouterLink to="/settings" class="nav-item" active-class="active">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M12 1v6m0 6v6m-6-6h6m6 0h-6"></path><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
          系統設定
        </RouterLink>
      </nav>
      
      <!-- 音樂播放器 -->
      <div class="music-player-section">
        <div class="music-header">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
          <span>背景音樂</span>
        </div>
        <div class="music-presets">
          <button
            v-for="(preset, idx) in musicPresets"
            :key="idx"
            class="preset-btn"
            :class="{ active: currentMusicIndex === idx }"
            @click="selectMusic(idx)"
          >
            {{ idx + 1 }}
          </button>
        </div>
        <div class="music-custom">
          <input
            v-model="customMusicUrl"
            type="text"
            placeholder="貼入 YouTube 連結..."
            @keyup.enter="playCustomMusic"
          />
          <button @click="playCustomMusic" class="play-btn" title="播放">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
          </button>
        </div>
        <div class="music-player">
          <iframe
            v-if="currentMusicEmbed"
            :src="currentMusicEmbed"
            width="100%"
            height="60"
            frameborder="0"
            allow="autoplay; encrypted-media"
            allowfullscreen
          ></iframe>
        </div>
      </div>

      <div style="margin-top: auto; padding-top: 20px; border-top: 1px solid var(--border-color);">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
          <img src="/logo.png" alt="3A科技實驗室" style="width: 36px; height: 36px; border-radius: 50%; object-fit: cover;" />
          <div>
            <div style="font-size: 14px; font-weight: 600;">阿亮老師</div>
            <div style="font-size: 12px; color: var(--text-sub);">亮言AI 生成器</div>
          </div>
        </div>
        <div style="display: flex; gap: 10px; padding-left: 4px; flex-wrap: wrap;">
          <a href="https://www.facebook.com/iddmail?locale=zh_TW" target="_blank" rel="noopener noreferrer" style="color: #1877F2; display: flex; align-items: center; gap: 4px; font-size: 12px; text-decoration: none;" title="Facebook">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
            FB
          </a>
          <a href="https://www.youtube.com/@Liang-yt02" target="_blank" rel="noopener noreferrer" style="color: #FF0000; display: flex; align-items: center; gap: 4px; font-size: 12px; text-decoration: none;" title="YouTube">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
            YT
          </a>
          <a href="https://www.facebook.com/groups/2754139931432955?locale=zh_TW" target="_blank" rel="noopener noreferrer" style="color: #1877F2; display: flex; align-items: center; gap: 4px; font-size: 12px; text-decoration: none;" title="3A科技實驗室">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
            3A
          </a>
        </div>
      </div>
    </aside>

    <!-- 主內容區 -->
    <main class="layout-main">
      <RouterView v-slot="{ Component, route }">
        <component :is="Component" />

        <!-- 全局頁腳版權資訊（首頁除外） -->
        <footer v-if="route.path !== '/'" class="global-footer">
          <div class="footer-content">
            <div class="footer-text">
              © 2026 AI 圖文生成器 - 部落格文章一鍵生成
            </div>
            <div class="footer-license">
              阿亮老師
            </div>
          </div>
        </footer>
      </RouterView>
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterView, RouterLink } from 'vue-router'
import { onMounted, ref, computed } from 'vue'
import { setupAutoSave } from './stores/generator'

// 預設音樂清單
const musicPresets = [
  'https://youtu.be/xA95Wd---5g?list=RDxA95Wd---5g',
  'https://youtu.be/WQl1C3xBhKo?list=RDWQl1C3xBhKo',
  'https://youtu.be/Ib2osVLmjSU?list=RDIb2osVLmjSU',
  'https://youtu.be/nx9MB6lQ6tw?list=RDnx9MB6lQ6tw',
  'https://youtu.be/Vwr_l5bUgUA?list=RDVwr_l5bUgUA'
]

const currentMusicIndex = ref(-1)
const customMusicUrl = ref('')
const currentMusicUrl = ref('')

// 將 YouTube URL 轉換為嵌入格式
function getYouTubeEmbedUrl(url: string): string {
  if (!url) return ''

  // 提取 video ID
  let videoId = ''

  // 處理 youtu.be 格式
  const shortMatch = url.match(/youtu\.be\/([^?&]+)/)
  if (shortMatch) {
    videoId = shortMatch[1]
  }

  // 處理 youtube.com/watch?v= 格式
  const longMatch = url.match(/[?&]v=([^&]+)/)
  if (longMatch) {
    videoId = longMatch[1]
  }

  if (!videoId) return ''

  // 使用 youtube-nocookie.com 並加入更多參數嘗試繞過限制
  return `https://www.youtube-nocookie.com/embed/${videoId}?autoplay=1&loop=1&playlist=${videoId}&modestbranding=1&rel=0`
}

const currentMusicEmbed = computed(() => getYouTubeEmbedUrl(currentMusicUrl.value))

function selectMusic(index: number) {
  currentMusicIndex.value = index
  currentMusicUrl.value = musicPresets[index]
}

function playCustomMusic() {
  if (customMusicUrl.value.trim()) {
    currentMusicIndex.value = -1
    currentMusicUrl.value = customMusicUrl.value.trim()
  }
}

// 啟用自動保存到 localStorage
onMounted(() => {
  setupAutoSave()
})
</script>
