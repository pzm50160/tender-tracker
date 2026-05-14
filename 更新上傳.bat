@echo off
chcp 65001 > nul
title 上傳程式更新到 GitHub
cd /d "%~dp0"

echo ===============================================
echo  上傳程式更新到 GitHub
echo ===============================================
echo.

REM 顯示目前有哪些變更
echo 【目前變更的檔案】
git status --short
echo.

REM 如果沒有任何變更，就結束
git diff --quiet HEAD 2>nul
git status --porcelain > "%TEMP%\git_status.txt" 2>nul
for %%i in ("%TEMP%\git_status.txt") do if %%~zi==0 (
    echo 沒有任何變更，無需上傳。
    echo.
    pause
    exit /b 0
)

REM 輸入版本說明（可直接按 Enter 略過，用時間戳記）
set /p MSG=請輸入更新說明（直接按 Enter 使用時間戳記）：

if "%MSG%"=="" (
    for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set D=%%c%%b%%a
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do set T=%%a%%b
    set MSG=更新 %D%-%T%
)

echo.
echo 正在上傳：%MSG%
echo.

git add -A
git commit -m "%MSG%"

if errorlevel 1 (
    echo [錯誤] commit 失敗
    pause
    exit /b 1
)

git push origin main

if errorlevel 1 (
    echo.
    echo [錯誤] 上傳失敗，請確認網路連線與 GitHub 權限
) else (
    echo.
    echo 上傳完成！對方電腦開啟程式後點「立即更新」即可取得最新版。
)

echo.
pause
