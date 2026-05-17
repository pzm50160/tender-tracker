"""
自動排程搜尋腳本
由 Windows 工作排程器每天執行，抓取最近 7 天的標案
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta
from scraper import run_scraper

today = date.today()
start = (today - timedelta(days=7)).strftime("%Y/%m/%d")
end   = today.strftime("%Y/%m/%d")

print(f"自動搜尋：{start} ~ {end}")
count = run_scraper(start_date=start, end_date=end)
print(f"完成，共 {count} 筆")
