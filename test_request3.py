"""
用 Session 保持 Cookie，更接近真實瀏覽器行為
"""
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
})

# Step 1: 先造訪首頁取得 Cookie
print("Step 1: 取得 Session Cookie...")
r = session.get("https://web.pcc.gov.tw/prkms/tender/common/basic/indexTenderBasic",
                 verify=False, timeout=20)
print(f"  狀態: {r.status_code}, Cookie: {dict(session.cookies)}")

# Step 2: 搜尋
url = "https://web.pcc.gov.tw/prkms/tender/common/basic/readTenderBasic"
session.headers["Referer"] = "https://web.pcc.gov.tw/prkms/tender/common/basic/indexTenderBasic"

tests = [
    ("健康檢查, isNow", {"searchType":"basic","firstSearch":"true","tenderName":"健康檢查","dateType":"isNow","pageSize":"100"}),
    ("健康檢查, 日期 115/03/01~115/05/09", {"searchType":"basic","firstSearch":"true","tenderName":"健康檢查","dateType":"isDate","queryStartDate":"115/03/01","queryEndDate":"115/05/09","pageSize":"100"}),
    ("體檢, 日期 115/01/01~115/05/09", {"searchType":"basic","firstSearch":"true","tenderName":"體檢","dateType":"isDate","queryStartDate":"115/01/01","queryEndDate":"115/05/09","pageSize":"100"}),
    ("健檢, 日期 114/01/01~115/05/09 (超過一年)", {"searchType":"basic","firstSearch":"true","tenderName":"健檢","dateType":"isDate","queryStartDate":"114/01/01","queryEndDate":"115/05/09","pageSize":"100"}),
]

def count_results(html):
    soup = BeautifulSoup(html, "html.parser")
    tb = soup.find("table", class_="tb_01")
    if not tb:
        return 0, "無表格"
    rows = tb.find_all("tr")[1:]
    data = [r for r in rows if r.find("td")]
    if not data:
        return 0, "空"
    first_text = data[0].get_text(strip=True)[:40]
    if "無符合" in first_text or "查無" in first_text:
        return 0, first_text
    return len(data), first_text

for name, params in tests:
    print(f"\nTest: {name}")
    try:
        r = session.get(url, params=params, verify=False, timeout=20)
        n, msg = count_results(r.text)
        print(f"  結果: {n} 筆  |  {msg}")
        if n > 0:
            # 顯示更多資料
            soup = BeautifulSoup(r.text, "html.parser")
            tb = soup.find("table", class_="tb_01")
            for row in tb.find_all("tr")[1:4]:
                cells = [td.get_text(strip=True)[:25] for td in row.find_all("td")]
                print(f"    {cells}")
            with open(f"data/result_{name[:8]}.html", "w", encoding="utf-8") as f:
                f.write(r.text)
    except Exception as e:
        print(f"  錯誤: {e}")
