"""
嘗試 POST 方式，以及不同的參數組合
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

# 先取得首頁 cookie
r0 = session.get("https://web.pcc.gov.tw/prkms/tender/common/basic/indexTenderBasic", verify=False, timeout=20)
print(f"首頁狀態: {r0.status_code}")
print(f"Cookie: {dict(session.cookies)}")

session.headers["Referer"] = "https://web.pcc.gov.tw/prkms/tender/common/basic/indexTenderBasic"
session.headers["Content-Type"] = "application/x-www-form-urlencoded"

url = "https://web.pcc.gov.tw/prkms/tender/common/basic/readTenderBasic"

# POST 方式
base_data = {
    "pageSize": "50",
    "firstSearch": "true",
    "searchType": "basic",
    "isBinding": "",
    "isLogIn": "N",
    "level_1": "on",
    "orgName": "",
    "orgId": "",
    "tenderId": "",
    "tenderType": "TENDER_DECLARATION",
    "tenderWay": "TENDER_WAY_ALL_DECLARATION",
    "radProctrgCate": "",
    "policyAdvocacy": "",
}

tests = [
    ("POST isNow 健康檢查", {**base_data, "tenderName": "健康檢查", "dateType": "isNow"}),
    ("POST isDate 健康檢查 115/01/01~115/05/09", {**base_data, "tenderName": "健康檢查", "dateType": "isDate", "tenderStartDate": "115/01/01", "tenderEndDate": "115/05/09"}),
    ("POST isNow 無關鍵字", {**base_data, "tenderName": "", "dateType": "isNow"}),
    ("GET isNow 健康檢查 (對照組)", None),
]

def count_results(html):
    soup = BeautifulSoup(html, "html.parser")
    tb = soup.find("table", class_="tb_01")
    if not tb:
        # 找任何含有標案資料的表格
        for t in soup.find_all("table"):
            rows = t.find_all("tr")
            if len(rows) > 3:
                return len(rows)-1, f"未知表格 class={t.get('class')} {rows[1].get_text(strip=True)[:30]}"
        return -1, "無tb_01表格"
    rows = tb.find_all("tr")
    data = [r for r in rows[1:] if r.find("td")]
    if not data:
        return 0, "空"
    first = data[0].get_text(strip=True)[:60]
    if "無符合" in first or "查無" in first:
        return 0, first
    return len(data), first[:30]

for name, data in tests:
    print(f"\n[{name}]")
    if data is None:
        # GET 對照
        params = {**base_data, "tenderName": "健康檢查", "dateType": "isNow"}
        r = session.get(url, params=params, verify=False, timeout=20)
    else:
        r = session.post(url, data=data, verify=False, timeout=20)
    print(f"  狀態: {r.status_code} | URL: {r.url[:80]}")
    n, msg = count_results(r.text)
    print(f"  結果: {n} 筆 | {msg}")
    if n > 0 and n != -1:
        print("  儲存結果HTML...")
        with open(f"data/post_{name[:10]}.html", "w", encoding="utf-8") as f:
            f.write(r.text)
