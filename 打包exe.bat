@echo off
chcp 65001 > nul
title 打包 launcher.exe
cd /d "%~dp0"

echo ===============================================
echo  打包桌面程式（launcher.exe）
echo ===============================================
echo.

REM 找 Python
if exist "%~dp0python-portable\python.exe" (
    set PYTHON="%~dp0python-portable\python.exe"
) else (
    set PYTHON=python
)

echo 安裝打包工具...
%PYTHON% -m pip install pyinstaller pystray pillow --quiet

echo.
echo 開始打包...
%PYTHON% -m PyInstaller --noconfirm --onefile --windowed ^
    --name "健檢標案追蹤系統" ^
    --icon NONE ^
    launcher.py

echo.
if exist "dist\健檢標案追蹤系統.exe" (
    copy /Y "dist\健檢標案追蹤系統.exe" "健檢標案追蹤系統.exe"
    echo ===============================================
    echo  完成！已產生「健檢標案追蹤系統.exe」
    echo  將以下檔案複製到目標電腦同一個資料夾：
    echo    - 健檢標案追蹤系統.exe
    echo    - app.py / database.py / config.py / scraper.py
    echo    - .streamlit\
    echo    - python-portable\  （含所有套件）
    echo ===============================================
) else (
    echo [錯誤] 打包失敗，請查看上方訊息
)
echo.
pause
