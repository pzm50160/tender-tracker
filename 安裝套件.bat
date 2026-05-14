@echo off
chcp 65001 > nul
title 安裝套件（只需執行一次）
cd /d "%~dp0"

echo ===============================================
echo  安裝必要套件（只需執行一次）
echo ===============================================
echo.

REM 找 Python
if exist "%~dp0python-portable\python.exe" (
    set PYTHON="%~dp0python-portable\python.exe"
    echo 使用攜帶式 Python
) else (
    python --version 2>nul
    if errorlevel 1 (
        echo [錯誤] 找不到 Python！
        echo 請安裝 Python 3.10 以上版本，或將 WinPython 解壓到 python-portable 資料夾
        pause
        exit /b 1
    )
    set PYTHON=python
    echo 使用系統 Python
)

echo.
echo 安裝套件中...
%PYTHON% -m pip install --upgrade pip --quiet
%PYTHON% -m pip install -r requirements.txt --quiet
%PYTHON% -m pip install pywebview pystray pillow --quiet

echo.
echo ===============================================
echo  安裝完成！
echo  - 執行「健檢標案追蹤系統.exe」開啟桌面程式
echo  - 或執行「啟動系統.bat」使用瀏覽器版本
echo ===============================================
pause
