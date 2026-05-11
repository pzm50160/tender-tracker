@echo off
chcp 65001 > nul
title 打包程式更新
cd /d "%~dp0"

echo 正在打包更新檔...

REM 用 PowerShell 壓縮（Windows 內建，不需額外工具）
powershell -Command ^
  "Compress-Archive -Force -Path ^
    '%~dp0app.py', ^
    '%~dp0scraper.py', ^
    '%~dp0database.py', ^
    '%~dp0config.py', ^
    '%~dp0啟動系統.bat', ^
    '%~dp0requirements.txt' ^
  -DestinationPath '%~dp0程式更新.zip'"

echo.
echo 完成！已產生「程式更新.zip」
echo 將此 zip 複製到新電腦，解壓覆蓋同名檔案即可。
echo.
pause
