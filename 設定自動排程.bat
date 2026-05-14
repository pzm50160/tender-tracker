@echo off
chcp 65001 > nul
title 設定每日自動搜尋
cd /d "%~dp0"

echo ===============================================
echo  設定每日自動搜尋（每天早上 8:00 執行）
echo ===============================================
echo.

REM 找 Python
if exist "%~dp0python-portable\python.exe" (
    set PYTHON=%~dp0python-portable\python.exe
) else (
    set PYTHON=python
)

set SCRIPT=%~dp0自動搜尋.py
set TASKNAME=健檢標案自動搜尋

REM 刪除舊排程（如果存在）
schtasks /delete /tn "%TASKNAME%" /f 2>nul

REM 建立新排程：每天 08:00 執行
schtasks /create /tn "%TASKNAME%" /tr "\"%PYTHON%\" \"%SCRIPT%\"" /sc daily /st 08:00 /f

if errorlevel 1 (
    echo [錯誤] 排程設定失敗
) else (
    echo.
    echo 排程設定完成！
    echo 每天早上 8:00 會自動搜尋最近 7 天的標案。
    echo.
    echo 若要修改時間，請重新執行本腳本。
    echo 若要取消排程，執行：schtasks /delete /tn "%TASKNAME%" /f
)
echo.
pause
