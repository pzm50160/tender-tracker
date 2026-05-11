from bs4 import BeautifulSoup
import re

with open("data/request_result.html", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

print(f"Title: {soup.title.text if soup.title else 'N/A'}")
print(f"HTML 大小: {len(html)}")

# 找 tb_01 表格（結果表格）
tb01 = soup.find("table", class_="tb_01")
if tb01:
    rows = tb01.find_all("tr")
    print(f"\ntb_01 表格共 {len(rows)} 列")
    for i, row in enumerate(rows):
        cells = row.find_all(["td", "th"])
        texts = [c.get_text(strip=True)[:40] for c in cells]
        print(f"  [{i}] {texts}")
        # 顯示連結
        links = row.find_all("a")
        for l in links:
            print(f"      連結: [{l.get_text(strip=True)}] -> {l.get('href', '')[:100]}")

# 找所有含「筆」「共」的文字
print("\n=== 筆數/總數相關文字 ===")
for tag in soup.find_all(string=re.compile(r'[\d,]+\s*筆|共\s*[\d,]+')):
    print(f"  {tag.strip()[:80]}")

# 找「無符合」或「查無」
no_data = soup.find_all(string=re.compile(r'無符合|查無|no.*data', re.I))
print(f"\n無資料訊息: {no_data[:3]}")

# 找分頁
pager = soup.find(class_=re.compile(r'page|pager|pagination'))
if pager:
    print(f"\n分頁: {pager.get_text(strip=True)[:100]}")
