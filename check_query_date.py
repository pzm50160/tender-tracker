with open("data/page_structure.html", encoding="utf-8") as f:
    html = f.read()

# 看 queryStartDate 附近的 HTML
idx = html.find("queryStartDate")
if idx >= 0:
    print("queryStartDate 附近:")
    print(html[max(0,idx-100):idx+200])

# 看 tenderStartDate 完整結構
idx2 = html.find("tenderStartDate")
if idx2 >= 0:
    print("\ntenderStartDate 附近:")
    print(html[idx2-50:idx2+200])

# 找所有 name= 屬性
import re
all_names = re.findall(r'name=["\']([^"\']+)["\']', html)
print(f"\n所有 name 屬性: {sorted(set(all_names))}")
