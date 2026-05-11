"""
用 Playwright 攔截網路請求，找出真正的搜尋 API
"""
from playwright.sync_api import sync_playwright

def capture():
    requests_log = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        # 攔截所有網路請求
        def on_request(req):
            if "prkms" in req.url or "tps" in req.url or "pcc.gov" in req.url:
                requests_log.append({
                    "method": req.method,
                    "url": req.url,
                    "post_data": req.post_data if req.method == "POST" else None,
                })
                print(f"  REQ {req.method} {req.url[:100]}")

        def on_response(resp):
            if "readTenderBasic" in resp.url or "searchTender" in resp.url:
                print(f"  RESP {resp.status} {resp.url[:100]}")

        page.on("request", on_request)
        page.on("response", on_response)

        print("前往搜尋頁...")
        page.goto("https://web.pcc.gov.tw/prkms/tender/common/basic/indexTenderBasic",
                  wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)

        # 用 JS 填入標案名稱
        page.evaluate("""() => {
            document.querySelector('input[name="tenderName"]').value = '健康檢查';
        }""")
        print("已填入健康檢查")

        # 點擊查詢按鈕（a[onclick=basicTenderSearch()]）
        print("點擊查詢按鈕...")
        search_link = page.locator("a[onclick*='basicTenderSearch']").first
        print(f"  找到按鈕: {search_link.count()} 個")

        # 監聽頁面導航
        with page.expect_navigation(wait_until="domcontentloaded", timeout=15000):
            search_link.click()

        page.wait_for_timeout(4000)
        print(f"\n結果頁 URL: {page.url}")

        # 儲存結果 HTML
        html = page.content()
        with open("data/playwright_result.html", "w", encoding="utf-8") as f:
            f.write(html)

        # 分析結果
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        tb = soup.find("table", class_="tb_01")
        if tb:
            rows = tb.find_all("tr")
            print(f"tb_01 表格: {len(rows)} 列")
            for row in rows[:6]:
                cells = [td.get_text(strip=True)[:25] for td in row.find_all(["td","th"])]
                print(f"  {cells}")
        else:
            print("找不到 tb_01 表格")
            print("所有表格:")
            for t in soup.find_all("table"):
                rows = t.find_all("tr")
                print(f"  class={t.get('class')} rows={len(rows)}")

        print(f"\n=== 攔截到的請求 ===")
        for req in requests_log:
            print(f"  {req['method']} {req['url'][:100]}")
            if req['post_data']:
                print(f"    POST data: {req['post_data'][:200]}")

        input("\n按 Enter 關閉...")
        browser.close()

if __name__ == "__main__":
    capture()
