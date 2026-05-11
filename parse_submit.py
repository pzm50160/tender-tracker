import re

with open("data/page_structure.html", encoding="utf-8") as f:
    html = f.read()

# 找完整的 goTender 函式
go_tender = re.search(r'function goTender\(\)\{.*?\}', html, re.DOTALL)
if go_tender:
    print("=== goTender ===")
    print(go_tender.group()[:500])

# 找 form 中的 button 和 input[type=submit]
form_match = re.search(r'<form[^>]*id="basicTenderSearchForm"[^>]*>(.*?)</form>', html, re.DOTALL)
if form_match:
    form_html = form_match.group(1)
    # 找 button
    buttons = re.findall(r'<(?:button|input)[^>]*(?:type="submit"|onclick)[^>]*>', form_html)
    print("\n=== Form 中的按鈕 ===")
    for b in buttons:
        print(b[:200])
    # 找所有 a 標籤
    anchors = re.findall(r'<a[^>]*onclick[^>]*>.*?</a>', form_html, re.DOTALL)
    print("\n=== Form 中的 a[onclick] ===")
    for a in anchors[:5]:
        print(a[:200])

# 找 commonInit 或 search 相關函式
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
for s in scripts:
    if 'submit' in s.lower() or 'search' in s.lower() or 'basicTenderSearchForm' in s:
        print("\n=== 含 submit/search 的 script ===")
        # 找含關鍵字的行
        for line in s.split('\n'):
            if any(kw in line for kw in ['submit', 'Search', 'Form', 'basicTender', 'query']):
                print(f"  {line.strip()}")
