#!/bin/bash

echo ""
echo "========================================"
echo "  AI 部落格圖文生成器 - 啟動中..."
echo "========================================"
echo ""

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "[錯誤] 請先安裝 Python 3.11+"
    exit 1
fi

# 安裝相依套件（如果需要）
if [ ! -d ".venv" ]; then
    echo "[1/2] 首次執行，安裝相依套件..."
    pip install -r requirements.txt -q
fi

# 啟動服務
echo "[2/2] 啟動服務..."
echo ""
echo "請在瀏覽器開啟: http://localhost:8099"
echo "首次使用請到「設定」頁面填入 API Key"
echo ""
echo "按 Ctrl+C 可停止服務"
echo "========================================"
echo ""

python3 -m backend.app
