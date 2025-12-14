# AI 部落格圖文生成器

輸入主題，AI 自動生成精美部落格圖文（4 張配圖），支援一鍵發布到 Blogger。

## 功能特色

- 8 種文字風格：專業、輕鬆、幽默、詩意、故事、教學、新聞、行銷
- 8 種圖片風格：扁平插畫、3D 卡通、水彩、寫實、日系動漫、極簡、復古、科技
- 支援上傳參考圖片
- 整合 ImgBB 圖床
- 一鍵發布到 Google Blogger

## 教學簡報

完整教學請參考 `docs/` 資料夾中的簡報：

1. **Part 1** - 專案介紹與功能概覽
2. **Part 2** - 環境安裝與設定
3. **Part 3** - 功能使用說明
4. **Part 4** - 進階設定與部署

開啟 `docs/index.html` 即可瀏覽教學。

## 快速開始

### 1. 安裝 Python 套件

```bash
pip install -r requirements.txt
```

### 2. 啟動服務

**Windows：**
```bash
start.bat
```
或雙擊 `start.bat`

**Mac/Linux：**
```bash
chmod +x start.sh
./start.sh
```

或手動啟動：
```bash
python -m backend.app
```

### 3. 開始使用

1. 開啟瀏覽器，前往 http://localhost:8099
2. 點擊右上角「設定」→ 填入 API Key
3. 回首頁輸入主題 → 選擇風格 → 生成圖文

## API Key 取得方式

| 服務 | 用途 | 取得連結 |
|------|------|----------|
| OpenAI | 文字生成 + 圖片生成 | https://platform.openai.com/api-keys |
| Google Gemini | 文字生成（免費額度多） | https://aistudio.google.com/apikey |
| ImgBB | 圖床上傳（選用） | https://api.imgbb.com/ |

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
│   └── dist/         # 建置輸出
├── docs/             # 教學簡報
├── start.bat         # Windows 啟動腳本
├── start.sh          # Linux/Mac 啟動腳本
└── requirements.txt  # Python 依賴
```

## 作者資訊

- **作者**：阿亮老師
- **Facebook**：https://www.facebook.com/iddmail
- **YouTube**：https://www.youtube.com/@Liang-yt02
- **3A科技實驗室**：https://www.facebook.com/groups/2754139931432955

## 授權

MIT License
