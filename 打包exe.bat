@echo off
chcp 65001 > nul
title 打包 launcher.exe（全自包，無需安裝 Python）
cd /d "%~dp0"

echo ===============================================
echo  打包桌面程式（含 Python + 所有套件）
echo  對方電腦不需另裝任何東西
echo ===============================================
echo.

REM 找 Python
if exist "%~dp0python-portable\python.exe" (
    set PYTHON="%~dp0python-portable\python.exe"
) else (
    set PYTHON=python
)

echo 關閉執行中的舊版程式...
taskkill /F /IM "健檢標案追蹤系統.exe" /T >nul 2>&1
timeout /t 2 /nobreak >nul

echo 安裝打包工具...
%PYTHON% -m pip install pyinstaller pystray pillow --quiet

echo.
echo 開始打包（首次約需 3~10 分鐘，請耐心等候）...
%PYTHON% -m PyInstaller --noconfirm --onedir --windowed ^
    --name "健檢標案追蹤系統" ^
    --collect-all streamlit ^
    --collect-all altair ^
    --collect-all pandas ^
    --collect-all numpy ^
    --collect-all pydeck ^
    --collect-all requests ^
    --collect-all bs4 ^
    --collect-all PIL ^
    --collect-all pystray ^
    --copy-metadata streamlit ^
    --copy-metadata pandas ^
    launcher.py

if errorlevel 1 (
    echo.
    echo [錯誤] 打包失敗，請查看上方訊息
    pause
    exit /b 1
)

REM 把 .py 應用程式檔案複製到 dist 資料夾旁
set DIST=dist\健檢標案追蹤系統
echo.
echo 複製應用程式檔案...
copy /Y app.py      "%DIST%\"
copy /Y database.py "%DIST%\"
copy /Y scraper.py  "%DIST%\"
copy /Y config.py   "%DIST%\"
copy /Y 自動搜尋.py  "%DIST%\"
copy /Y 安裝套件.bat "%DIST%\"

if not exist "%DIST%\.streamlit" mkdir "%DIST%\.streamlit"
copy /Y .streamlit\config.toml "%DIST%\.streamlit\"

if not exist "%DIST%\data" mkdir "%DIST%\data"

REM 寫入目前 git commit SHA 作為版本標記（供 app 內建更新比對用）
for /f %%i in ('git rev-parse HEAD 2^>nul') do set GIT_SHA=%%i
if defined GIT_SHA (
    echo %GIT_SHA%> "%DIST%\.version"
    echo 版本標記已寫入：%GIT_SHA:~0,7%
) else (
    echo 警告：找不到 git，略過版本標記
)

echo.
echo ===============================================
echo  完成！發佈資料夾：dist\健檢標案追蹤系統\
echo.
echo  傳給對方的方式：
echo    將整個「健檢標案追蹤系統」資料夾壓縮成 ZIP
echo    對方解壓縮後，直接雙擊「健檢標案追蹤系統.exe」
echo    不需安裝 Python 或任何套件！
echo ===============================================
echo.
pause
