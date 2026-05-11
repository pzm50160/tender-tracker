"""
政府電子採購網 健檢標案爬蟲
GET /prkms/tender/common/basic/readTenderBasic
"""

import re
import time
import requests
import urllib3
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta

from config import PROCUREMENT_TYPES, MIN_BUDGET, MAX_BUDGET
from database import upsert_tender, log_fetch, init_db, get_keywords

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://web.pcc.gov.tw"
SEARCH_URL = f"{BASE_URL}/prkms/tender/common/basic/readTenderBasic"
INDEX_URL  = f"{BASE_URL}/prkms/tender/common/basic/indexTenderBasic"

# 採購性質代碼
PROC_TYPE_VALUES = {
    "工程類": "RAD_PROCTRG_CATE_1",
    "財物類": "RAD_PROCTRG_CATE_2",
    "勞務類": "RAD_PROCTRG_CATE_3",
}

# ROC → 西元年
def roc_to_western(roc_date: str) -> str:
    """115/05/08 → 2026/05/08"""
    if not roc_date:
        return ""
    parts = roc_date.split("/")
    if len(parts) == 3:
        try:
            year = int(parts[0]) + 1911
            return f"{year}/{parts[1]}/{parts[2]}"
        except ValueError:
            pass
    return roc_date


def parse_budget(text: str) -> float | None:
    if not text:
        return None
    text = text.replace(",", "").strip()
    m = re.search(r"[\d.]+", text)
    return float(m.group()) if m else None


def is_budget_ok(budget: float | None) -> bool:
    if budget is None:
        return True
    if MIN_BUDGET is not None and budget < MIN_BUDGET:
        return False
    if MAX_BUDGET is not None and budget > MAX_BUDGET:
        return False
    return True


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    })
    # 取得 Cookie
    session.get(INDEX_URL, verify=False, timeout=20)
    session.headers["Referer"] = INDEX_URL
    return session


def build_params(keyword: str, start_date: str, end_date: str,
                 page_param: str = "", procurement_type: str = "",
                 search_field: str = "tenderName") -> dict:
    """建立搜尋 GET 參數，search_field: tenderName | orgName"""
    params = {
        "pageSize": "100",
        "firstSearch": "true",
        "searchType": "basic",
        "isBinding": "N",
        "isLogIn": "N",
        "level_1": "on",
        "orgName":  keyword if search_field == "orgName" else "",
        "orgId": "", "tenderId": "",
        "tenderType": "TENDER_DECLARATION",
        "tenderWay": "TENDER_WAY_ALL_DECLARATION",
        "tenderName": keyword if search_field == "tenderName" else "",
        "dateType": "isDate",
        "tenderStartDate": start_date,
        "tenderEndDate": end_date,
        "radProctrgCate": PROC_TYPE_VALUES.get(procurement_type, ""),
        "policyAdvocacy": "",
    }
    if page_param:
        key, val = page_param.split("=")
        params[key] = val
    return params


def parse_tender_name(cell_html: str) -> str:
    """從 JavaScript pageCode2Img("名稱") 提取標案名稱"""
    m = re.search(r'pageCode2Img\("([^"]+)"\)', cell_html)
    return m.group(1) if m else ""


def parse_page(html: str, keyword: str, fetched_at: str) -> tuple[list[dict], str | None]:
    """
    解析搜尋結果頁
    回傳 (標案清單, 下一頁參數 or None)
    """
    soup = BeautifulSoup(html, "html.parser")
    tb = soup.find("table", class_="tb_01")
    if not tb:
        return [], None

    results = []
    rows = tb.find_all("tr")[1:]  # 跳過表頭

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 8:
            continue

        first_text = cells[0].get_text(strip=True)
        if "無符合" in first_text or "查無" in first_text or not first_text.isdigit():
            continue

        # 標案案號
        tender_id = cells[2].get_text("\n", strip=True).split("\n")[0].strip()

        # 標案名稱（從 JS 提取）
        tender_name = parse_tender_name(str(cells[2]))

        # 詳情 URL
        link_tag = cells[2].find("a", href=True)
        detail_url = (BASE_URL + link_tag["href"]) if link_tag else ""

        # 機關名稱
        agency = cells[1].get_text(strip=True)

        # 招標次數 (col 3)
        bid_round = cells[3].get_text(strip=True)

        # 招標方式
        tender_way = cells[4].get_text(strip=True)

        # 採購性質
        procurement_type = cells[5].get_text(strip=True)

        # 採購性質篩選
        if PROCUREMENT_TYPES and procurement_type and procurement_type not in PROCUREMENT_TYPES:
            continue

        # 公告日期 (ROC format)
        publish_date_roc = cells[6].get_text(strip=True)
        publish_date = roc_to_western(publish_date_roc)

        # 截止投標 (ROC)
        deadline_roc = cells[7].get_text(strip=True) if len(cells) > 7 else ""
        deadline = roc_to_western(deadline_roc)

        # 預算金額
        budget_text = cells[8].get_text(strip=True) if len(cells) > 8 else ""
        budget = parse_budget(budget_text)

        if not is_budget_ok(budget):
            continue

        # 開標時間（只取含 / 的日期格式，避免抓到「檢視」按鈕文字）
        opening_date_roc = cells[9].get_text(strip=True) if len(cells) > 9 else ""
        if opening_date_roc and "/" not in opening_date_roc:
            opening_date_roc = ""
        opening_date = roc_to_western(opening_date_roc) if opening_date_roc else ""

        # 唯一鍵：機關+案號+招標次數
        uid = f"{agency}_{tender_id}_{bid_round}"[:120]

        results.append({
            "tender_id": uid,
            "tender_name": tender_name,
            "agency": agency,
            "tender_case_no": tender_id,
            "procurement_type": procurement_type,
            "tender_way": tender_way,
            "budget": budget,
            "publish_date": publish_date,
            "deadline": deadline,
            "opening_date": opening_date,
            "detail_url": detail_url,
            "matched_keyword": keyword,
            "fetched_at": fetched_at,
        })

    # 找下一頁連結
    next_page_param = None
    page_div = soup.find(class_=lambda x: x and "page" in x.lower())
    if page_div:
        next_link = page_div.find("a", string=re.compile(r"下一頁|Next|›|»"))
        if next_link and next_link.get("href"):
            href = next_link["href"]
            # 提取 d-XXXX-p=N 分頁參數
            m = re.search(r"(d-\d+-p=\d+)", href)
            if m:
                next_page_param = m.group(1)
                # 設 firstSearch=false 換頁
                next_page_param = next_page_param

    return results, next_page_param


def search_by_field(session: requests.Session, keyword: str,
                    start_date: str, end_date: str,
                    search_field: str = "tenderName") -> list[dict]:
    """搜尋單一欄位的所有頁，回傳標案清單"""
    all_results = []
    fetched_at = datetime.now().isoformat()
    page_param = ""
    page_num = 1
    first_search = True

    while True:
        params = build_params(keyword, start_date, end_date, page_param,
                              search_field=search_field)
        if not first_search:
            params["firstSearch"] = "false"

        try:
            resp = session.get(SEARCH_URL, params=params, verify=False, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            print(f"    [錯誤] {e}")
            break

        page_results, next_param = parse_page(resp.text, keyword, fetched_at)
        all_results.extend(page_results)
        print(f"    [{search_field}] 第{page_num}頁: {len(page_results)} 筆")

        if not next_param or not page_results:
            break

        page_param = next_param
        first_search = False
        page_num += 1
        time.sleep(1)

        if page_num > 30:
            break

    return all_results


def fetch_detail(session: requests.Session, url: str) -> dict:
    """從詳情頁抓截止時間(含時:分)和開標時間"""
    if not url:
        return {}
    try:
        resp = session.get(url, verify=False, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"    [詳情頁錯誤] {e}")
        return {}

    soup = BeautifulSoup(resp.text, "html.parser")
    result = {}
    for tr in soup.find_all("tr"):
        tds = tr.find_all(["th", "td"])
        for i, td in enumerate(tds):
            label = td.get_text(strip=True)
            if i + 1 >= len(tds):
                continue
            val = tds[i + 1].get_text(strip=True)
            if not val or "/" not in val:
                continue
            if "截止投標" in label:
                result["deadline"] = roc_to_western(val)
            elif "開標時間" in label:
                result["opening_date"] = roc_to_western(val)
    return result


def search_keyword(session: requests.Session, keyword: str,
                   start_date: str, end_date: str) -> list[dict]:
    """搜尋標案名稱 + 機關名稱，合併去重後回傳；再逐筆抓詳情頁取精確時間"""
    seen = {}
    for field in ("tenderName", "orgName"):
        results = search_by_field(session, keyword, start_date, end_date, field)
        for r in results:
            if r["tender_id"] not in seen:
                seen[r["tender_id"]] = r
        time.sleep(0.5)

    all_results = list(seen.values())
    print(f"  → 抓取 {len(all_results)} 筆詳情頁取精確時間...")
    for r in all_results:
        detail = fetch_detail(session, r.get("detail_url", ""))
        if detail:
            r.update(detail)
        time.sleep(0.4)

    return all_results


def run_scraper(start_date: str = None, end_date: str = None) -> int:
    """
    執行爬蟲
    start_date, end_date: "YYYY/MM/DD" 西元年，預設近 7 天
    回傳總抓取筆數
    """
    init_db()

    today = date.today()
    if not start_date:
        start_date = (today - timedelta(days=7)).strftime("%Y/%m/%d")
    if not end_date:
        end_date = today.strftime("%Y/%m/%d")

    KEYWORDS = get_keywords()

    print(f"\n{'='*55}")
    print(f"搜尋日期: {start_date} ~ {end_date}")
    print(f"關鍵字: {KEYWORDS}")
    print(f"採購性質: {PROCUREMENT_TYPES or '全部'}")
    print(f"{'='*55}\n")

    session = make_session()
    total = 0

    for keyword in KEYWORDS:
        print(f"[搜尋] 「{keyword}」")
        try:
            results = search_keyword(session, keyword, start_date, end_date)
            for r in results:
                upsert_tender(r)
            total += len(results)
            log_fetch(keyword, len(results), "success")
            print(f"  → 共 {len(results)} 筆\n")
        except Exception as e:
            print(f"  → 失敗: {e}\n")
            log_fetch(keyword, 0, f"error: {str(e)[:100]}")
        time.sleep(0.5)

    print(f"完成！共 {total} 筆標案已入庫。")
    return total


if __name__ == "__main__":
    run_scraper()
