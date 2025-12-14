# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 語言設定

所有回應請使用繁體中文。

## 專案概述

AI 圖文生成器 - 以 GitHub Copilot 建置的部落格圖文生成工具，使用 AI 自動生成部落格文章大綱、內文和配圖。

## 常用指令

### 後端 (Flask + Python)

```bash
# 安裝相依套件
pip install -r requirements.txt

# 啟動後端開發伺服器 (port 12398)
python -m backend.app

# 執行測試
pytest tests/
```

### 前端 (Vue 3 + Vite)

```bash
cd frontend

# 安裝相依套件
pnpm install

# 啟動開發伺服器 (port 5173)
pnpm dev

# 建構正式版本
pnpm build
```

### Docker 部署

```bash
docker run -d -p 12398:12398 \
  -v ./history:/app/history \
  -v ./output:/app/output \
  your-image-name:latest
```

## 架構說明

### 後端架構

- **進入點**: `backend/app.py` - Flask 應用程式，自動偵測是否有前端建構產物決定運作模式
- **設定管理**: `backend/config.py` - 載入 YAML 設定檔，提供服務商配置
- **API 路由**: `backend/routes/` - RESTful API 端點
  - `outline_routes.py` - 大綱生成 `/api/outline/generate`
  - `image_routes.py` - 圖片生成 `/api/images/generate`（SSE 串流）
  - `export_routes.py` - 匯出 Markdown/HTML
  - `history_routes.py` - 歷史記錄管理
- **業務邏輯**: `backend/services/` - 核心服務
  - `outline.py` - 呼叫文字 AI 生成大綱，解析 `<page>` 標籤
  - `image.py` - 圖片生成服務，支援並發生成、封面優先、自動重試
- **AI 生成器**: `backend/generators/` - 工廠模式實作
  - `google_genai.py` - Google Gemini API
  - `openai_compatible.py` - OpenAI 相容 API
  - `image_api.py` - 通用圖片 API
- **提示詞模板**: `backend/prompts/` - AI 提示詞文字檔

### 前端架構

- **狀態管理**: `frontend/src/stores/generator.ts` - Pinia store，管理生成流程狀態
- **頁面流程**: Home → Outline → Generate → Result
- **API 層**: `frontend/src/api/index.ts` - Axios 封裝

### 設定檔

- `text_providers.yaml` - 文字生成 API 設定（Gemini、OpenAI）
- `image_providers.yaml` - 圖片生成 API 設定
- 設定檔支援多服務商，透過 `active_provider` 切換

### 資料流

1. 使用者輸入主題 → OutlineService 呼叫文字 AI 生成大綱
2. 大綱解析為 pages 陣列（cover/intro/content/summary 類型）
3. ImageService 先生成封面，再並發生成其他頁面（使用封面作為風格參考）
4. 圖片存入 `history/{task_id}/` 目錄，同時生成縮圖
5. 支援單張重新生成和批次重試

## 重要檔案位置

| 用途 | 路徑 |
|------|------|
| 大綱生成提示詞 | `backend/prompts/outline_prompt.txt` |
| 圖片生成提示詞 | `backend/prompts/image_prompt.txt` |
| 歷史記錄目錄 | `history/` |
| 前端狀態管理 | `frontend/src/stores/generator.ts` |
| API 路由定義 | `backend/routes/__init__.py` |
