import re

with open("data/results.html", encoding="utf-8") as f:
    html = f.read()

print(f"HTML 大小: {len(html)} bytes")

# 找所有 table 的 class
tables = re.findall(r'<table[^>]*class="([^"]*)"[^>]*>', html)
print("\ntable classes:", tables[:10])

# 找標案名稱（通常含有連結）
tender_links = re.findall(r'<a[^>]*href="([^"]*tenderCase[^"]*|[^"]*tender[^"]*)"[^>]*>([^<]+)</a>', html)
print(f"\n標案相關連結 ({len(tender_links)} 筆):")
for href, text in tender_links[:10]:
    print(f"  [{text.strip()}] -> {href}")

# 找所有連結文字含有「健」的
health_links = re.findall(r'<a[^>]*>([^<]*健[^<]*)</a>', html)
print(f"\n含「健」的連結:")
for l in health_links[:10]:
    print(f"  {l.strip()}")

# 找分頁
pager = re.findall(r'class="[^"]*pag[^"]*"[^>]*>.*?</[^>]+>', html, re.DOTALL)
for p in pager[:3]:
    print("\n分頁元素:", p[:200])

# 找總筆數
total = re.findall(r'(?:共|總數|筆數)[^\d]*(\d+)[^\d]*筆', html)
print(f"\n總筆數: {total}")

# 找所有 td 中含有「健康」或「體檢」的文字
health_tds = re.findall(r'<td[^>]*>[^<]*(?:健康|體檢|健檢)[^<]*</td>', html)
print(f"\n含健康/體檢/健檢的 td: {len(health_tds)} 個")
for td in health_tds[:5]:
    print(f"  {td.strip()[:100]}")
