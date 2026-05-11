"""
探索 PCC 搜尋結果頁結構（用 JavaScript 填表）
"""
from playwright.sync_api import sync_playwright
import re

def explore_results():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        print("前往搜尋頁...")
        page.goto("https://web.pcc.gov.tw/prkms/tender/common/basic/readTenderBasic",
                  wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)

        # 用 JavaScript 填入表單
        page.evaluate("""() => {
            // 標案名稱
            document.querySelector('input[name="tenderName"]').value = '健康檢查';

            // dateType = isNow（等標期中，已是預設）
            // 已預設，不需更改

            // 採購性質 = 勞務類 RAD_PROCTRG_CATE_3
            const radios = document.querySelectorAll('input[name="radProctrgCate"]');
            for (const r of radios) {
                if (r.value === 'RAD_PROCTRG_CATE_3') {
                    r.checked = true;
                    break;
                }
            }

            // 每頁 100 筆
            const ps = document.querySelector('select[name="pageSize"]');
            if (ps) ps.value = '100';
        }""")
        print("已填入搜尋條件（健康檢查、勞務類、等標期中）")
        page.wait_for_timeout(500)

        # 點擊查詢（呼叫 goTender 函式）
        print("送出查詢...")
        page.evaluate("goTender()")
        page.wait_for_timeout(6000)

        print(f"結果頁 URL: {page.url}")
        print(f"Title: {page.title()}")

        # 儲存結果 HTML
        html = page.content()
        with open("data/results.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("已儲存 data/results.html")

        # 分析表格結構
        rows = page.locator("table tbody tr").all()
        print(f"\n找到 {len(rows)} 個表格列")
        for i, row in enumerate(rows[:5]):
            tds = row.locator("td").all()
            texts = []
            for td in tds:
                t = td.inner_text().strip().replace("\n", " ")[:30]
                texts.append(t)
            print(f"  row[{i}]: {texts}")

        # 找分頁資訊
        pager = page.locator("[class*='pager'], [class*='page'], .pagination").first
        if pager.count():
            print(f"\n分頁: {pager.inner_text()[:100]}")

        # 找總筆數
        total_els = page.locator("*:has-text('筆'), *:has-text('總數')").all()
        for el in total_els[:5]:
            t = el.inner_text().strip()[:60]
            if any(c.isdigit() for c in t):
                print(f"總筆數資訊: {t}")

        input("\n按 Enter 關閉瀏覽器...")
        browser.close()

if __name__ == "__main__":
    explore_results()
