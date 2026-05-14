@echo off
chcp 65001 > nul
title 健檢標案追蹤系統
cd /d "%~dp0"

echo ===============================================
echo  健檢標案追蹤系統
echo ===============================================
echo.

REM 確保資料資料夾存在
if not exist "data" mkdir data

REM 找 Python
if exist "%~dp0python-portable\python.exe" (
    set PYTHON="%~dp0python-portable\python.exe"
) else (
    set PYTHON=python
)

REM 檢查 streamlit 是否已安裝
%PYTHON% -c "import streamlit" 2>nul
if errorlevel 1 (
    echo [!] 尚未安裝套件，請先執行「安裝套件.bat」
    echo.
    pause
    exit /b 1
)

echo 正在啟動，瀏覽器將自動開啟...
echo 關閉此視窗即可停止系統
echo.

%PYTHON% -m streamlit run app.py --server.headless false --server.port 8501
pause
