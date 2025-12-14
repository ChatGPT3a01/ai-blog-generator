@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   AI 部落格圖文生成器 - 啟動中...
echo ========================================
echo.

:: 檢查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 請先安裝 Python 3.11+
    pause
    exit /b 1
)

:: 安裝相依套件（如果需要）
if not exist ".venv" (
    echo [1/2] 首次執行，安裝相依套件...
    pip install -r requirements.txt -q
)

:: 啟動服務
echo [2/2] 啟動服務...
echo.
echo 請在瀏覽器開啟: http://localhost:8099
echo 首次使用請到「設定」頁面填入 API Key
echo.
echo 按 Ctrl+C 可停止服務
echo ========================================
echo.

python -m backend.app
