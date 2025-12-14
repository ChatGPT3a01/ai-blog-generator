# AI 圖文生成器 - 部落格文章一鍵生成

基於 [RedInk](https://github.com/HisMax/RedInk) 改造的部落格圖文生成工具，使用 AI 自動生成部落格文章大綱、內文和配圖。

---

## 功能特色

- **一鍵生成**：輸入主題，AI 自動生成完整部落格文章
- **智慧摘要**：AI 生成文章結構，支援自訂編輯
- **自動配圖**：為每個段落生成 16:9 橫式配圖
- **多格式輸出**：支援 Markdown 和 HTML 格式匯出
- **多種 AI 服務**：支援 Gemini、OpenAI 等多種 API
- **歷史記錄**：自動儲存生成的文章，方便管理

---

## 系統需求

- Python 3.11+
- Node.js 18+
- pnpm（前端套件管理）
- uv（Python 套件管理，推薦）或 pip

---

## 安裝步驟

### 步驟 1：下載專案

```bash
git clone https://github.com/ChatGPT3a01/ai-blog-generator.git
cd ai-blog-generator
```

### 步驟 2：設定 API 金鑰

複製設定範例檔案：

```bash
cp text_providers.yaml.example text_providers.yaml
cp image_providers.yaml.example image_providers.yaml
```

編輯 `text_providers.yaml`，設定文字生成 API：

```yaml
# 目前啟用的服務供應商
active_provider: gemini

providers:
  # Google Gemini（推薦，免費額度較多）
  gemini:
    type: google_gemini
    api_key: 你的_GEMINI_API_KEY
    model: gemini-2.5-flash

  # 或使用 OpenAI
  openai:
    type: openai_compatible
    api_key: 你的_OPENAI_API_KEY
    base_url: https://api.openai.com/v1
    model: gpt-4o
```

編輯 `image_providers.yaml`，設定圖片生成 API：

```yaml
# 目前啟用的服務供應商
active_provider: gemini

providers:
  # Google Gemini 圖片生成
  gemini:
    type: google_genai
    api_key: 你的_GEMINI_API_KEY
    model: gemini-2.0-flash-exp-image-generation
    default_aspect_ratio: "16:9"
    high_concurrency: false
```

### 步驟 3：安裝後端相依套件

使用 uv（推薦）：

```bash
uv sync
```

或使用 pip：

```bash
pip install -r requirements.txt
```

### 步驟 4：安裝前端相依套件

```bash
cd frontend
pnpm install
cd ..
```

---

## 啟動服務

### 方式一：Docker 部署（最簡單，推薦）

只需一行指令：

```bash
docker-compose up -d
```

打開瀏覽器 http://localhost:12398 即可使用。

> **注意**：首次執行會自動建構映像，需要等待幾分鐘。

**停止服務：**

```bash
docker-compose down
```

**手動建構（可選）：**

```bash
# 建構映像
docker build -t ai-blog-generator .

# 執行容器
docker run -d -p 12398:12398 \
  -v ./history:/app/history \
  -v ./output:/app/output \
  ai-blog-generator
```

### 方式二：正式環境模式

適合沒有安裝 Docker 的使用者。

**步驟 1：建構前端**

```bash
cd frontend
pnpm build
cd ..
```

**步驟 2：啟動服務**

```bash
uv run python -m backend.app
```

打開瀏覽器 http://localhost:12398 即可使用。

### 方式三：開發模式（前後端分離）

適合需要修改程式碼的開發者。

**啟動後端：**

```bash
uv run python -m backend.app
```

後端會在 http://localhost:12398 啟動

**啟動前端：**（開啟新的終端機視窗）

```bash
cd frontend
pnpm dev
```

前端會在 http://localhost:5173 啟動

---

## 使用教學

### 基本使用流程

1. **輸入主題**
   - 在首頁輸入想要撰寫的部落格主題
   - 例如：「如何在家製作美味的義式濃縮咖啡」

2. **生成大綱**
   - 點擊「生成大綱」按鈕
   - AI 會自動生成 4-8 個段落的文章結構
   - 包含：封面、前言、內容段落、結論

3. **編輯大綱**（可選）
   - 可以修改每個段落的內容描述
   - 調整段落順序
   - 新增或刪除段落

4. **生成配圖**
   - 點擊「生成圖片」按鈕
   - AI 會為每個段落生成 16:9 橫式配圖
   - 可以單獨重新生成不滿意的圖片

5. **匯出文章**
   - 支援 Markdown 格式（適合 Medium、Notion 等）
   - 支援 HTML 格式（可直接貼上部落格後台）
   - 一鍵下載所有圖片

### 進階功能

- **上傳參考圖片**：上傳品牌圖片，AI 會參考其風格
- **系統設定**：在設定頁面管理 API 設定
- **歷史記錄**：查看和重新編輯之前生成的文章

---

## API 設定說明

### 文字生成 API（text_providers.yaml）

| 供應商 | 類型 | 推薦模型 | 說明 |
|--------|------|----------|------|
| Google Gemini | google_gemini | gemini-2.5-flash | 免費額度多，推薦 |
| OpenAI | openai_compatible | gpt-4o | 品質好，需付費 |
| 第三方 API | openai_compatible | 依供應商 | 如 OneAPI 等 |

### 圖片生成 API（image_providers.yaml）

| 供應商 | 類型 | 推薦模型 | 說明 |
|--------|------|----------|------|
| Google Gemini | google_genai | gemini-2.0-flash-exp-image-generation | 免費額度多 |
| OpenAI DALL-E | openai_compatible | dall-e-3 | 品質好，需付費 |
| 第三方 API | image_api | 依供應商 | 支援 OpenAI 相容格式 |

### 取得 API Key

#### Google Gemini API Key

1. 前往 [Google AI Studio](https://aistudio.google.com/)
2. 登入 Google 帳號
3. 點擊「Get API Key」
4. 建立新的 API Key 或使用現有的

#### OpenAI API Key

1. 前往 [OpenAI Platform](https://platform.openai.com/)
2. 登入或註冊帳號
3. 前往 API Keys 頁面
4. 點擊「Create new secret key」

---

## 專案結構

```
專案_打造部落格圖文生成器/
├── backend/                 # 後端 (Flask)
│   ├── app.py              # 主應用程式
│   ├── config.py           # 設定管理
│   ├── generators/         # AI 生成器
│   │   ├── google_genai.py # Gemini API
│   │   ├── openai_compatible.py # OpenAI API
│   │   └── image_api.py    # 圖片 API
│   ├── prompts/            # AI 提示詞
│   │   ├── outline_prompt.txt  # 大綱生成
│   │   └── image_prompt.txt    # 圖片生成
│   ├── routes/             # API 路由
│   │   ├── outline_routes.py   # 大綱 API
│   │   ├── image_routes.py     # 圖片 API
│   │   ├── export_routes.py    # 匯出 API
│   │   └── history_routes.py   # 歷史 API
│   └── services/           # 業務邏輯
│       ├── outline.py      # 大綱服務
│       ├── image.py        # 圖片服務
│       └── export.py       # 匯出服務
├── frontend/               # 前端 (Vue 3)
│   ├── src/
│   │   ├── views/          # 頁面元件
│   │   ├── components/     # 通用元件
│   │   └── stores/         # 狀態管理
│   └── package.json
├── history/                # 歷史記錄存放
├── text_providers.yaml     # 文字 API 設定
├── image_providers.yaml    # 圖片 API 設定
└── docker-compose.yml      # Docker 設定
```

---

## API 端點

### 大綱生成

```
POST /api/outline/generate
Content-Type: application/json

{
  "topic": "文章主題",
  "images": []  // 可選，base64 參考圖片
}
```

### 圖片生成

```
POST /api/images/generate
Content-Type: application/json

{
  "pages": [...],  // 大綱頁面
  "task_id": "xxx",
  "user_topic": "文章主題"
}
```

### 匯出 Markdown

```
POST /api/export/markdown
Content-Type: application/json

{
  "task_id": "xxx",
  "pages": [...],
  "include_images": true
}
```

### 匯出 HTML

```
POST /api/export/html
Content-Type: application/json

{
  "task_id": "xxx",
  "pages": [...],
  "include_images": true,
  "include_style": true
}
```

---

## 常見問題

### Q: 圖片生成失敗怎麼辦？

1. 檢查 API Key 是否正確
2. 確認 API 額度是否足夠
3. 嘗試關閉高並行模式（high_concurrency: false）
4. 查看後端 log 取得詳細錯誤訊息

### Q: 如何更換 AI 服務供應商？

在 Web 介面的「系統設定」頁面可以直接切換，或編輯設定檔中的 `active_provider`。

### Q: 可以自訂圖片比例嗎？

可以，在 `image_providers.yaml` 中修改 `default_aspect_ratio`，支援的比例取決於 AI 服務供應商。

### Q: 歷史記錄存在哪裡？

存放在專案根目錄的 `history/` 資料夾中，每個任務一個子資料夾。

---

## 授權說明

本專案基於 [RedInk](https://github.com/HisMax/RedInk) 修改，遵循 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 授權。

- 可自由用於個人、學習、研究用途
- 禁止商業用途（除非獲得原作者授權）
- 修改後需以相同授權分享

---

## 如何用 AI 建立類似專案

如果你想用 AI（如 GitHub Copilot、Claude、ChatGPT）從零開始建立類似的專案，可以參考以下提示詞：

### 提示詞範例

```
請幫我建立一個「AI 部落格圖文生成器」專案，需求如下：

【功能需求】
1. 使用者輸入部落格主題，AI 自動生成文章大綱（包含封面、前言、內容段落、結論）
2. 根據大綱為每個段落生成 16:9 橫式配圖
3. 支援編輯大綱內容、調整段落順序、新增/刪除段落
4. 可單獨重新生成不滿意的圖片
5. 支援匯出 Markdown 和 HTML 格式
6. 自動儲存歷史記錄

【技術架構】
- 後端：Python Flask REST API
- 前端：Vue 3 + Vite + Pinia 狀態管理
- AI 服務：支援 Google Gemini 和 OpenAI API（可切換）
- 設定檔：使用 YAML 格式管理多個 AI 服務商

【API 設計】
- POST /api/outline/generate - 生成大綱
- POST /api/images/generate - 生成圖片（SSE 串流回傳進度）
- POST /api/export/markdown - 匯出 Markdown
- POST /api/export/html - 匯出 HTML
- GET/POST /api/history - 歷史記錄管理

【其他需求】
- 圖片生成採用「封面優先」策略，先生成封面再並發生成其他頁面
- 使用封面圖作為風格參考，確保整篇文章圖片風格一致
- 支援 Docker 部署
- 提供設定檔範例（.example 檔案）
```

---

## 致謝

- [RedInk](https://github.com/HisMax/RedInk) - 原始專案
- [Google Gemini](https://ai.google.dev/) - AI 服務
- [OpenAI](https://openai.com/) - AI 服務
