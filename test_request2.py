"""
測試不同參數組合
"""
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

url = "https://web.pcc.gov.tw/prkms/tender/common/basic/readTenderBasic"
base_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Referer": "https://web.pcc.gov.tw/prkms/tender/common/basic/indexTenderBasic",
}

# 測試各種參數
test_cases = [
    {
        "name": "測試1: 健康檢查 + 等標期中 + 全部性質",
        "params": {
            "searchType": "basic", "firstSearch": "true",
            "tenderName": "健康檢查", "dateType": "isNow",
            "pageSize": "100",
        }
    },
    {
        "name": "測試2: 健檢 + 等標期中 + 全部性質",
        "params": {
            "searchType": "basic", "firstSearch": "true",
            "tenderName": "健檢", "dateType": "isNow",
            "pageSize": "100",
        }
    },
    {
        "name": "測試3: 健康檢查 + 不限日期",
        "params": {
            "searchType": "basic", "firstSearch": "true",
            "tenderName": "健康檢查",
            "pageSize": "100",
        }
    },
    {
        "name": "測試4: 體檢 + 日期區間 115/04/01~115/05/09",
        "params": {
            "searchType": "basic", "firstSearch": "true",
            "tenderName": "體檢", "dateType": "isDate",
            "queryStartDate": "115/04/01", "queryEndDate": "115/05/09",
            "pageSize": "100",
        }
    },
]

for case in test_cases:
    print(f"\n{case['name']}")
    try:
        resp = requests.get(url, params=case["params"], headers=base_headers,
                           timeout=20, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        tb01 = soup.find("table", class_="tb_01")
        if tb01:
            rows = tb01.find_all("tr")
            data_rows = [r for r in rows[1:] if r.find("td")]
            result_count = len(data_rows)
            if result_count > 0:
                first_cells = [td.get_text(strip=True)[:30] for td in data_rows[0].find_all("td")]
                print(f"  OK 找到 {result_count} 筆! 第一筆: {first_cells[:5]}")
            else:
                msg = rows[1].get_text(strip=True)[:50] if len(rows) > 1 else "空"
                print(f"  MISS 0 筆: {msg}")

        # 找總筆數
        count_el = soup.find(string=lambda t: t and "筆" in t and any(c.isdigit() for c in t))
        if count_el:
            print(f"  筆數說明: {count_el.strip()[:60]}")
    except Exception as e:
        print(f"  錯誤: {e}")
