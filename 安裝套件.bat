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
        echo 請先安裝 Python 3.10 以上版本：
        echo   https://www.python.org/downloads/
        echo 安裝時請勾選「Add Python to PATH」
        pause
        exit /b 1
    )
    set PYTHON=python
    echo 使用系統 Python
)

echo.
echo 安裝套件中（首次約需 2~5 分鐘）...
%PYTHON% -m pip install --upgrade pip --quiet
%PYTHON% -m pip install -r requirements.txt --quiet

echo.
echo ===============================================
echo  安裝完成！
echo  請雙擊「健檢標案追蹤系統.exe」開啟程式
echo ===============================================
pause
