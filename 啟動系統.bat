@echo off
chcp 65001 > nul
title 健檢標案追蹤系統
echo ===============================================
echo  健檢標案追蹤系統
echo ===============================================
echo.
echo 正在啟動網頁介面...
echo 請用瀏覽器開啟: http://localhost:8501
echo.
echo 按 Ctrl+C 可關閉系統
echo.
REM 優先使用攜帶式 Python，否則用系統 Python
if exist "%~dp0python-portable\python.exe" (
    "%~dp0python-portable\python.exe" -m streamlit run "%~dp0app.py" --server.headless true
) else (
    python -m streamlit run app.py --server.headless true
)
pause
