"""
使用正確 URL 格式測試（西元年、isBinding=N）
"""
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "zh-TW,zh;q=0.9",
})
r0 = session.get("https://web.pcc.gov.tw/prkms/tender/common/basic/indexTenderBasic", verify=False, timeout=20)
session.headers["Referer"] = "https://web.pcc.gov.tw/prkms/tender/common/basic/indexTenderBasic"

url = "https://web.pcc.gov.tw/prkms/tender/common/basic/readTenderBasic"

base = {
    "pageSize": "",
    "firstSearch": "true",
    "searchType": "basic",
    "isBinding": "N",
    "isLogIn": "N",
    "level_1": "on",
    "orgName": "", "orgId": "", "tenderId": "",
    "tenderType": "TENDER_DECLARATION",
    "tenderWay": "TENDER_WAY_ALL_DECLARATION",
    "radProctrgCate": "",
    "policyAdvocacy": "",
}

tests = [
    ("isDate 健康檢查 2026/01/01~2026/05/09", {**base,
        "tenderName": "健康檢查", "dateType": "isDate",
        "tenderStartDate": "2026/01/01", "tenderEndDate": "2026/05/09"}),
    ("isDate 健檢 2026/01/01~2026/05/09", {**base,
        "tenderName": "健檢", "dateType": "isDate",
        "tenderStartDate": "2026/01/01", "tenderEndDate": "2026/05/09"}),
    ("isDate 體檢 2026/01/01~2026/05/09", {**base,
        "tenderName": "體檢", "dateType": "isDate",
        "tenderStartDate": "2026/01/01", "tenderEndDate": "2026/05/09"}),
    ("isDate 健康 2025/01/01~2026/05/09 (大範圍)", {**base,
        "tenderName": "健康", "dateType": "isDate",
        "tenderStartDate": "2025/01/01", "tenderEndDate": "2026/05/09"}),
]

def parse_results(html):
    soup = BeautifulSoup(html, "html.parser")
    tb = soup.find("table", class_="tb_01")
    if not tb:
        return 0, [], "無表格"
    rows = tb.find_all("tr")[1:]
    data = []
    for row in rows:
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if not cells:
            continue
        if "無符合" in cells[0] or "查無" in cells[0]:
            return 0, [], cells[0][:30]
        data.append(cells)
    return len(data), data, "OK"

for name, params in tests:
    print(f"\n[{name}]")
    try:
        r = session.get(url, params=params, verify=False, timeout=20)
        n, rows, msg = parse_results(r.text)
        print(f"  結果: {n} 筆 | {msg}")
        if rows:
            for row in rows[:3]:
                print(f"    {[c[:20] for c in row[:8]]}")
            if n > 0:
                with open(f"data/final_{name[:8]}.html", "w", encoding="utf-8") as f:
                    f.write(r.text)
    except Exception as e:
        print(f"  錯誤: {e}")
