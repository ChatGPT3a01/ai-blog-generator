<template>
  <div v-if="visible" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <h3>發布到 Blogger</h3>

      <!-- Step 1: Get Access Token -->
      <div v-if="step === 1" class="step-content">
        <div style="background: #f8f9fa; border-radius: 12px; padding: 16px; margin-bottom: 16px;">
          <p style="font-weight: 600; margin-bottom: 12px; color: #333;">📋 取得授權步驟：</p>
          <ol style="margin: 0; padding-left: 20px; font-size: 14px; color: #555; line-height: 1.8;">
            <li>點擊下方「開啟 OAuth Playground」按鈕</li>
            <li>在左側 <strong>Step 1</strong> 的「Input your own scopes」輸入框中貼上：<br/>
              <code style="background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-size: 12px; user-select: all;">https://www.googleapis.com/auth/blogger</code><br/>
              <span style="color: #d63384;">⚠️ 貼上後按 Enter 鍵確認！</span>
            </li>
            <li>確認下方出現已添加的 scope 後，點擊藍色「Authorize APIs」按鈕</li>
            <li>選擇您的 Google 帳號並允許授權</li>
            <li>回到頁面後，在 <strong>Step 2</strong> 點擊「Exchange authorization code for tokens」</li>
            <li>複製 <strong>Access token</strong> 欄位的內容（以 ya29. 開頭）</li>
            <li>貼到下方輸入框</li>
          </ol>
        </div>

        <a
          :href="oauthUrl"
          target="_blank"
          class="btn btn-primary"
          style="display: inline-block; text-decoration: none; margin-bottom: 16px;"
        >
          開啟 OAuth Playground
        </a>

        <p style="margin-bottom: 8px; font-size: 14px; font-weight: 500;">貼上 Access Token：</p>
        <textarea
          v-model="accessToken"
          placeholder="ya29.xxxx..."
          style="width: 100%; height: 80px; padding: 8px; border: 1px solid var(--border-color); border-radius: 8px; resize: none; font-family: monospace; font-size: 12px;"
        ></textarea>

        <div style="margin-top: 16px; display: flex; gap: 12px; justify-content: flex-end;">
          <button class="btn" @click="$emit('close')">取消</button>
          <button class="btn btn-primary" @click="fetchBlogs" :disabled="!accessToken || loading">
            {{ loading ? '載入中...' : '下一步' }}
          </button>
        </div>
      </div>

      <!-- Step 2: Select Blog -->
      <div v-if="step === 2" class="step-content">
        <p style="margin-bottom: 16px; color: var(--text-sub);">選擇要發布的部落格：</p>

        <div v-if="blogs.length === 0" style="color: var(--text-secondary);">
          找不到部落格，請確認您的 Google 帳號有建立 Blogger 部落格。
        </div>

        <div v-else style="display: flex; flex-direction: column; gap: 8px;">
          <label
            v-for="blog in blogs"
            :key="blog.id"
            style="display: flex; align-items: center; gap: 8px; padding: 12px; border: 1px solid var(--border-color); border-radius: 8px; cursor: pointer;"
            :style="{ borderColor: selectedBlogId === blog.id ? 'var(--primary)' : '' }"
          >
            <input type="radio" :value="blog.id" v-model="selectedBlogId" />
            <div>
              <div style="font-weight: 500;">{{ blog.name }}</div>
              <div style="font-size: 12px; color: var(--text-secondary);">{{ blog.url }}</div>
            </div>
          </label>
        </div>

        <div style="margin-top: 16px;">
          <label style="display: flex; align-items: center; gap: 8px;">
            <input type="checkbox" v-model="isDraft" />
            <span>儲存為草稿（不直接發布）</span>
          </label>
        </div>

        <div style="margin-top: 16px; display: flex; gap: 12px; justify-content: flex-end;">
          <button class="btn" @click="step = 1">上一步</button>
          <button class="btn btn-primary" @click="publish" :disabled="!selectedBlogId || publishing">
            {{ publishing ? '發布中...' : (isDraft ? '儲存草稿' : '發布文章') }}
          </button>
        </div>
      </div>

      <!-- Step 3: Success -->
      <div v-if="step === 3" class="step-content">
        <div style="text-align: center; padding: 20px 0;">
          <div style="font-size: 48px; margin-bottom: 16px;">✅</div>
          <h4 style="margin-bottom: 8px;">{{ isDraft ? '草稿已儲存！' : '發布成功！' }}</h4>
          <p style="color: var(--text-sub); margin-bottom: 16px;">
            {{ isDraft ? '文章已儲存為草稿，您可以到 Blogger 編輯後再發布。' : '文章已成功發布到您的部落格。' }}
          </p>
          <a
            v-if="postUrl"
            :href="postUrl"
            target="_blank"
            class="btn btn-primary"
            style="display: inline-block; text-decoration: none;"
          >
            查看文章
          </a>
        </div>

        <div style="margin-top: 16px; display: flex; justify-content: center;">
          <button class="btn" @click="$emit('close')">關閉</button>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="error" style="margin-top: 16px; padding: 12px; background: #fee; border-radius: 8px; color: #c00;">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { getBloggerBlogs, publishToBlogger } from '../api'

const props = defineProps<{
  visible: boolean
  title: string
  outline: string
  images: string[]
}>()

const emit = defineEmits(['close'])

const step = ref(1)
const accessToken = ref('')
const blogs = ref<{ id: string; name: string; url: string }[]>([])
const selectedBlogId = ref('')
const isDraft = ref(false)
const loading = ref(false)
const publishing = ref(false)
const error = ref('')
const postUrl = ref('')

// Google OAuth URL (使用 OAuth Playground 簡化流程)
const oauthUrl = computed(() => {
  return 'https://developers.google.com/oauthplayground/#step1&scopes=https%3A//www.googleapis.com/auth/blogger&url=https%3A//&content_type=application/json&http_method=GET&useDefaultOauthCred=checked&oauthEndpointSelect=Google&oauthAuthEndpointValue=https%3A//accounts.google.com/o/oauth2/v2/auth&oauthTokenEndpointValue=https%3A//oauth2.googleapis.com/token&includeCredentials=unchecked&accessTokenType=bearer&autoRefreshToken=unchecked&accessType=offline&forceApr498498ovalPrompt=checked&response_type=code'
})

const fetchBlogs = async () => {
  if (!accessToken.value) return

  loading.value = true
  error.value = ''

  try {
    const result = await getBloggerBlogs(accessToken.value)
    if (result.success && result.blogs) {
      blogs.value = result.blogs
      if (blogs.value.length > 0) {
        selectedBlogId.value = blogs.value[0].id
      }
      step.value = 2
    } else {
      error.value = result.error || '取得部落格清單失敗'
    }
  } catch (e: any) {
    error.value = e.message || '取得部落格清單失敗'
  } finally {
    loading.value = false
  }
}

const publish = async () => {
  if (!selectedBlogId.value) return

  publishing.value = true
  error.value = ''

  try {
    const result = await publishToBlogger({
      accessToken: accessToken.value,
      blogId: selectedBlogId.value,
      title: props.title,
      outline: props.outline,
      images: props.images,
      isDraft: isDraft.value
    })

    if (result.success) {
      postUrl.value = result.post_url || ''
      step.value = 3
    } else {
      error.value = result.error || '發布失敗'
    }
  } catch (e: any) {
    error.value = e.message || '發布失敗'
  } finally {
    publishing.value = false
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
}

.modal-content {
  background: white;
  padding: 24px;
  border-radius: 16px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-content h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
}
</style>
