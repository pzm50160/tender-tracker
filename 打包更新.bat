@echo off
chcp 65001 > nul
title 打包程式更新
cd /d "%~dp0"

echo 正在打包更新檔...

powershell -Command ^
  "Compress-Archive -Force -Path ^
    '%~dp0app.py', ^
    '%~dp0scraper.py', ^
    '%~dp0database.py', ^
    '%~dp0config.py', ^
    '%~dp0requirements.txt', ^
    '%~dp0啟動系統.bat', ^
    '%~dp0安裝套件.bat', ^
    '%~dp0.streamlit' ^
  -DestinationPath '%~dp0程式更新.zip'"

echo.
echo 完成！已產生「程式更新.zip」
echo 解壓到新電腦後：
echo   1. 第一次執行「安裝套件.bat」
echo   2. 之後每次執行「啟動系統.bat」即可
echo.
pause
