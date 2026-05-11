@echo off
chcp 65001 > nul
title 安裝套件（只需執行一次）
echo ===============================================
echo  正在安裝必要套件（只需執行一次）
echo ===============================================
echo.

cd /d "%~dp0"

if not exist "python-portable\python.exe" (
    echo [錯誤] 找不到攜帶式 Python！
    echo 請先將 WinPython Dot 解壓到 python-portable 資料夾
    echo 路徑應為: %~dp0python-portable\python.exe
    pause
    exit /b 1
)

echo 找到攜帶式 Python，開始安裝套件...
echo.
python-portable\python.exe -m pip install --no-warn-script-location ^
    requests>=2.31.0 ^
    beautifulsoup4>=4.12.0 ^
    "streamlit>=1.35.0" ^
    "pandas>=2.0.0" ^
    urllib3>=2.0.0

echo.
echo ===============================================
echo  安裝完成！請執行「啟動系統.bat」
echo ===============================================
pause
