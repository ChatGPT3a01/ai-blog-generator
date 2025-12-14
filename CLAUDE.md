# CLAUDE.md

## 語言設定
所有回應請使用繁體中文。

## 作者資訊
- **作者名稱**: 阿亮老師
- **Facebook**: https://www.facebook.com/iddmail?locale=zh_TW
- **YouTube**: https://www.youtube.com/@Liang-yt02
- **3A科技實驗室 (FB社團)**: https://www.facebook.com/groups/2754139931432955?locale=zh_TW

## 專案概述
AI 部落格圖文生成器 - 輸入主題自動生成 4 張部落格配圖。

## 常用指令

```bash
# 安裝
pip install -r requirements.txt

# 啟動（port 8099）
python -m backend.app
```

## 架構

```
backend/
├── app.py              # Flask 進入點
├── config.py           # 設定管理
├── routes/             # API 路由
├── services/           # 業務邏輯
├── generators/         # AI 生成器
└── prompts/            # 提示詞模板

frontend/
└── src/
    ├── views/          # 頁面
    ├── components/     # 元件
    └── stores/         # 狀態管理
```

## 設定檔
- `text_providers.yaml` - 文字生成 API
- `image_providers.yaml` - 圖片生成 API
