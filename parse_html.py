import re

with open('data/page_structure.html', encoding='utf-8') as f:
    html = f.read()

# 找送出按鈕
btns = re.findall(r'<(?:button|a)[^>]*>[^<]*(?:查詢|搜尋|送出)[^<]*</(?:button|a)>', html)
print("=== 查詢按鈕 ===")
for b in btns[:10]:
    print(b[:200])

# 找 radProctrgCate 的選項值
cates = re.findall(r'name="radProctrgCate"[^>]*value="([^"]+)"', html)
print("\n=== radProctrgCate 值 ===", cates)

# 找 dateType 選項
dtypes = re.findall(r'name="dateType"[^>]*value="([^"]+)"', html)
print("=== dateType 值 ===", dtypes)

# 找所有 select option
ttype = re.findall(r'<option[^>]*value="([^"]*)"[^>]*>([^<]+)</option>', html)
print("\n=== select options ===")
for v, t in ttype[:20]:
    print(f"  value={v!r} text={t.strip()!r}")

# 找分頁
page_info = re.findall(r'pageIndex|currentPage|totalPage|totalCount', html)
print("\n=== 分頁關鍵字 ===", set(page_info))

# 找結果表格
result_table = re.findall(r'class="[^"]*result[^"]*"', html)
print("\n=== result class ===", result_table[:10])
