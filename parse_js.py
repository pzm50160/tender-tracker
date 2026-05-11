import re

with open("data/page_structure.html", encoding="utf-8") as f:
    html = f.read()

# 找 goTender 函式
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
for s in scripts:
    if 'goTender' in s or 'submit' in s.lower():
        print("=== Script 含 goTender/submit ===")
        print(s[:2000])
        print()

# 找 form 詳細資訊
forms = re.findall(r'<form[^>]*>.*?</form>', html, re.DOTALL)
for f in forms[:3]:
    print("=== FORM ===")
    print(f[:500])
    print()
