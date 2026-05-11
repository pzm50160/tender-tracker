"""
直接用 GET 請求搜尋 PCC，不需要瀏覽器
"""
import requests
from bs4 import BeautifulSoup

params = {
    "searchType": "basic",
    "firstSearch": "true",
    "tenderType": "TENDER_DECLARATION",
    "tenderName": "健康檢查",
    "dateType": "isNow",
    "radProctrgCate": "RAD_PROCTRG_CATE_3",  # 勞務類
    "pageSize": "100",
    "pageIndex": "1",
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9",
    "Referer": "https://web.pcc.gov.tw/prkms/tender/common/basic/indexTenderBasic",
}

url = "https://web.pcc.gov.tw/prkms/tender/common/basic/readTenderBasic"
print(f"請求 URL: {url}")
print(f"參數: {params}\n")

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
resp = requests.get(url, params=params, headers=headers, timeout=30, verify=False)
print(f"狀態碼: {resp.status_code}")
print(f"最終 URL: {resp.url}")
print(f"內容大小: {len(resp.content)} bytes")

# 解析
soup = BeautifulSoup(resp.text, "html.parser")
print(f"\nTitle: {soup.title.text if soup.title else 'N/A'}")

# 找結果表格
tables = soup.find_all("table")
print(f"Table 數量: {len(tables)}")
for t in tables:
    cls = t.get("class", [])
    rows = t.find_all("tr")
    print(f"  table class={cls} rows={len(rows)}")
    if len(rows) > 2:
        # 顯示前幾列
        for row in rows[:4]:
            cells = row.find_all(["td", "th"])
            texts = [c.get_text(strip=True)[:20] for c in cells]
            if texts:
                print(f"    {texts}")

# 找總筆數
for el in soup.find_all(string=True):
    if "筆" in el and any(c.isdigit() for c in el):
        print(f"\n含「筆」文字: {el.strip()[:80]}")

# 儲存
with open("data/request_result.html", "w", encoding="utf-8") as f:
    f.write(resp.text)
print("\n已儲存 data/request_result.html")
