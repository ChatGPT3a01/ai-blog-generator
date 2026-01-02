# AI 部落格圖文生成器

輸入主題，AI 自動生成精美部落格圖文（4 張配圖），支援一鍵發布到 Blogger。

## 功能特色

- 8 種文字風格：專業、輕鬆、幽默、詩意、故事、教學、新聞、行銷
- 8 種圖片風格：扁平插畫、3D 卡通、水彩、寫實、日系動漫、極簡、復古、科技
- 支援上傳參考圖片
- **Unsplash 備用圖庫**：AI 圖片生成失敗時，可從免費圖庫選擇替代圖片
- 整合 ImgBB 圖床
- 一鍵發布到 Google Blogger
- 滑鼠粒子特效

---

## 快速開始（學生教學）

### 步驟 1：下載專案

**方法 A：使用 Git（推薦）**
```bash
git clone https://github.com/ChatGPT3a01/AI-Blog-Generator.git
cd AI-Blog-Generator
```

**方法 B：直接下載 ZIP**
1. 點擊本頁面綠色「Code」按鈕
2. 選擇「Download ZIP」
3. 解壓縮到任意資料夾

### 步驟 2：安裝 Python 套件

確保已安裝 Python 3.8 以上版本，然後執行：

```bash
pip install -r requirements.txt
```

### 步驟 3：啟動服務

**Windows：**
```bash
python -m backend.app
```
或雙擊 `start.bat`

**Mac/Linux：**
```bash
python -m backend.app
```
或執行 `./start.sh`

### 步驟 4：開啟網頁

啟動成功後，開啟瀏覽器前往：
```
http://localhost:8099
```

---

## API Key 設定教學

首次使用需要設定 API Key。點擊左側「系統設定」進入設定頁面。

### 文字生成 API（必填，擇一）

#### 選項 1：Google Gemini（推薦，免費額度多）

1. 前往 https://aistudio.google.com/apikey
2. 登入 Google 帳號
3. 點擊「Create API Key」
4. 複製 API Key
5. 回到系統設定 → 文字生成 → 新增
   - 類型：選擇「Google Gemini」
   - 名稱：隨意（如「我的Gemini」）
   - API Key：貼上剛才複製的 Key
   - 模型：選擇 `gemini-2.0-flash`（推薦）
6. 點擊「測試連線」確認成功
7. 儲存後點擊「啟用」

#### 選項 2：OpenAI

1. 前往 https://platform.openai.com/api-keys
2. 登入 OpenAI 帳號
3. 點擊「Create new secret key」
4. 複製 API Key
5. 回到系統設定 → 文字生成 → 新增
   - 類型：選擇「OpenAI」
   - 名稱：隨意
   - API Key：貼上 Key
   - 模型：選擇 `gpt-4o`（推薦）或 `gpt-4-turbo`
6. 測試連線 → 儲存 → 啟用

### 圖片生成 API（必填）

#### OpenAI DALL-E（推薦）

使用與文字相同的 OpenAI API Key：
1. 系統設定 → 圖片生成 → 新增
2. 類型：選擇「OpenAI DALL-E」
3. API Key：貼上 OpenAI Key
4. 模型：選擇 `dall-e-3`
5. 測試連線 → 儲存 → 啟用

### Unsplash 備用圖庫（選填）

當 AI 圖片生成失敗時，可使用 Unsplash 免費圖庫作為替代：

**申請步驟：**

| 步驟 | 網址 | 操作 |
|:---:|------|------|
| 1 | https://unsplash.com/developers | 點擊「Your apps」 |
| 2 | https://unsplash.com/oauth/applications | 點擊「New Application」 |
| 3 | 彈出視窗 | 勾選 4 個 API 使用條款 |
| 4 | 彈出視窗 | 點擊「Accept terms」 |
| 5 | 表單頁面 | 填寫應用名稱 & 說明 |
| 6 | 表單頁面 | 點擊「Create application」 |
| 7 | Gmail | 確認郵件驗證（如需要） |
| 8 | 應用詳情頁面 | 複製「Access Key」 |

**設定方式：**
- 回到系統設定 → Unsplash 備用圖庫 → 貼上 Access Key → 儲存

### ImgBB 圖床（選填，發布到 Blogger 需要）

1. 前往 https://api.imgbb.com/
2. 註冊/登入
3. 複製 API Key
4. 回到系統設定 → 圖床設定 → 貼上 → 儲存

### Blogger 授權（選填，發布文章需要）

要發布文章到 Google Blogger，需要取得 OAuth Access Token：

**步驟 1：開啟 OAuth Playground**
- 前往 https://developers.google.com/oauthplayground/

**步驟 2：啟用自訂憑證**
- 點擊頁面**右上角齒輪圖示** ⚙️
- 勾選 `Use your own OAuth credentials`

**步驟 3：輸入授權範圍**
- 在左側 Step 1 的「Input your own scopes」輸入框貼上：
  ```
  https://www.googleapis.com/auth/blogger
  ```
- **按 Enter 確認**（很重要！）
- 確認下方出現已添加的 scope

**步驟 4：授權**
- 點擊藍色「Authorize APIs」按鈕
- 選擇您的 Google 帳號
- 允許授權

**步驟 5：取得 Token**
- 回到頁面後，在 Step 2 點擊「Exchange authorization code for tokens」
- 複製「Access token」欄位的內容（以 `ya29.` 開頭）

**步驟 6：設定**
- 回到系統設定 → Blogger 設定 → 貼上 Access Token → 儲存

> ⚠️ 注意：Access Token 有效期約 1 小時，過期後需重新取得

---

## 使用流程

1. **首頁**：輸入主題（如「咖啡沖泡教學」）
2. **選擇風格**：選擇文字風格和圖片風格
3. **生成大綱**：AI 會生成 4 個區塊的文字內容
4. **編輯大綱**：可手動修改文字
5. **生成圖片**：AI 為每個區塊生成配圖
6. **查看結果**：預覽完整圖文
7. **發布**：一鍵發布到 Blogger（需設定 ImgBB）

---

## 常見問題

### Q: 圖片生成失敗怎麼辦？
A: 點擊失敗圖片下方的「替代圖片」按鈕，可以：
- 從 Unsplash 搜尋免費圖片
- 上傳自己的圖片
- 跳過此張圖片

### Q: 出現「API Key 無效」錯誤？
A: 請確認：
1. API Key 複製完整，沒有多餘空格
2. API Key 帳號有足夠額度
3. 選擇的模型與 API Key 相符

### Q: 網頁打不開？
A: 確認：
1. 終端機顯示「Running on http://localhost:8099」
2. 沒有其他程式佔用 8099 埠
3. 防火牆沒有阻擋

### Q: 如何停止服務？
A: 在終端機按 `Ctrl + C`

---

## 教學簡報

完整教學請參考 `docs/` 資料夾中的簡報：

1. **Part 1** - 專案介紹與功能概覽
2. **Part 2** - 環境安裝與設定
3. **Part 3** - 功能使用說明
4. **Part 4** - 進階設定與部署

開啟 `docs/index.html` 即可瀏覽教學。

---

## 專案結構

```
AI-Blog-Generator/
├── backend/           # Python 後端
│   ├── app.py        # Flask 進入點
│   ├── routes/       # API 路由
│   ├── services/     # 業務邏輯
│   └── prompts/      # AI 提示詞模板
├── frontend/         # Vue 3 前端
│   ├── src/          # 原始碼
│   └── dist/         # 建置輸出（已包含）
├── docs/             # 教學簡報
├── start.bat         # Windows 啟動腳本
├── start.sh          # Linux/Mac 啟動腳本
└── requirements.txt  # Python 依賴
```

---

## 進階：重新建置前端（開發者）

如需修改前端程式碼，請使用 Node.js 20 LTS：

```bash
cd frontend
npm install
npm run build:normal
```

> 注意：Node.js 24 有相容性問題，請使用 Node.js 20

---

## 作者資訊

- **作者**：阿亮老師
- **Facebook**：https://www.facebook.com/iddmail
- **YouTube**：https://www.youtube.com/@Liang-yt02
- **3A科技實驗室**：https://www.facebook.com/groups/2754139931432955

---

## 授權

MIT License
