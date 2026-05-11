"""
使用正確的欄位名稱測試
"""
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "zh-TW,zh;q=0.9",
})
session.get("https://web.pcc.gov.tw/prkms/tender/common/basic/indexTenderBasic", verify=False, timeout=20)
session.headers["Referer"] = "https://web.pcc.gov.tw/prkms/tender/common/basic/indexTenderBasic"

url = "https://web.pcc.gov.tw/prkms/tender/common/basic/readTenderBasic"

tests = [
    ("isNow + 健康檢查", {
        "searchType": "basic", "firstSearch": "true", "isLogIn": "N",
        "tenderType": "TENDER_DECLARATION",
        "tenderWay": "TENDER_WAY_ALL_DECLARATION",
        "tenderName": "健康檢查", "dateType": "isNow",
        "radProctrgCate": "", "pageSize": "100",
    }),
    ("isDate + tenderStartDate + 健康檢查", {
        "searchType": "basic", "firstSearch": "true", "isLogIn": "N",
        "tenderType": "TENDER_DECLARATION",
        "tenderWay": "TENDER_WAY_ALL_DECLARATION",
        "tenderName": "健康檢查", "dateType": "isDate",
        "tenderStartDate": "115/01/01", "tenderEndDate": "115/05/09",
        "radProctrgCate": "", "pageSize": "100",
    }),
    ("isDate + startDate + 健康檢查", {
        "searchType": "basic", "firstSearch": "true", "isLogIn": "N",
        "tenderType": "TENDER_DECLARATION",
        "tenderWay": "TENDER_WAY_ALL_DECLARATION",
        "tenderName": "健康檢查", "dateType": "isDate",
        "startDate": "115/01/01", "endDate": "115/05/09",
        "radProctrgCate": "", "pageSize": "100",
    }),
    ("isNow + 健檢 (無關鍵字過濾)", {
        "searchType": "basic", "firstSearch": "true", "isLogIn": "N",
        "tenderType": "TENDER_DECLARATION",
        "tenderWay": "TENDER_WAY_ALL_DECLARATION",
        "tenderName": "健檢", "dateType": "isNow",
        "radProctrgCate": "", "pageSize": "100",
    }),
    ("isNow + 無關鍵字 (看總數)", {
        "searchType": "basic", "firstSearch": "true", "isLogIn": "N",
        "tenderType": "TENDER_DECLARATION",
        "tenderWay": "TENDER_WAY_ALL_DECLARATION",
        "tenderName": "", "dateType": "isNow",
        "radProctrgCate": "", "pageSize": "10",
    }),
]

def count_results(html):
    soup = BeautifulSoup(html, "html.parser")
    tb = soup.find("table", class_="tb_01")
    if not tb:
        return -1, "無表格"
    rows = tb.find_all("tr")
    data = [r for r in rows[1:] if r.find("td")]
    if not data:
        return 0, "空"
    first = data[0].get_text(strip=True)[:60]
    if "無符合" in first or "查無" in first:
        return 0, first

    # 找筆數說明
    page_div = soup.find(class_=lambda x: x and "page" in x)
    count_info = page_div.get_text(strip=True)[:60] if page_div else ""
    return len(data), f"{first[:30]} | 分頁:{count_info}"

for name, params in tests:
    print(f"\n[{name}]")
    r = session.get(url, params=params, verify=False, timeout=20)
    n, msg = count_results(r.text)
    print(f"  結果: {n} 筆")
    print(f"  訊息: {msg}")
