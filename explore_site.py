"""
探索 PCC 網站結構，找出正確的搜尋 URL 和表單欄位
"""
from playwright.sync_api import sync_playwright
import json

def explore():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        print("前往首頁...")
        page.goto("https://web.pcc.gov.tw/pis/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        # 找所有連結含「標案查詢」
        links = page.locator("a").all()
        tender_links = []
        for l in links:
            try:
                text = l.inner_text().strip()
                href = l.get_attribute("href") or ""
                if "標案" in text or "查詢" in text:
                    tender_links.append({"text": text, "href": href})
            except:
                pass

        print("\n=== 標案相關連結 ===")
        for l in tender_links[:20]:
            print(f"  [{l['text']}] -> {l['href']}")

        # 嘗試點擊「標案查詢」
        print("\n嘗試前往標案查詢頁...")
        try:
            page.goto("https://web.pcc.gov.tw/prkms/tender/common/basic/readTenderBasic",
                      wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(3000)
            print(f"URL: {page.url}")
            print(f"Title: {page.title()}")

            # 找所有 input 和 select
            inputs = page.locator("input, select, textarea").all()
            print("\n=== 表單欄位 ===")
            for inp in inputs:
                try:
                    name = inp.get_attribute("name") or inp.get_attribute("id") or "?"
                    itype = inp.get_attribute("type") or inp.evaluate("el => el.tagName")
                    placeholder = inp.get_attribute("placeholder") or ""
                    print(f"  {itype} name={name} placeholder={placeholder}")
                except:
                    pass

            # 儲存頁面HTML供分析
            html = page.content()
            with open("data/page_structure.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("\n已儲存頁面 HTML 至 data/page_structure.html")

        except Exception as e:
            print(f"失敗: {e}")

        input("\n按 Enter 關閉瀏覽器...")
        browser.close()

if __name__ == "__main__":
    explore()
