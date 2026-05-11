from bs4 import BeautifulSoup
import re

with open("data/page_structure.html", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
form = soup.find("form", id="basicTenderSearchForm")
if not form:
    print("找不到表單!")
else:
    print("=== 所有表單欄位 ===")
    for inp in form.find_all(["input", "select", "textarea"]):
        name = inp.get("name", "")
        itype = inp.get("type", inp.name)
        value = inp.get("value", "")
        placeholder = inp.get("placeholder", "")
        checked = "checked" if inp.get("checked") else ""
        selected_el = inp.get("selected")
        print(f"  {itype:10} name={name!r:35} value={value!r:30} {placeholder} {checked}")

    # 找 queryStartDate / queryEndDate
    print("\n=== 搜尋 queryStartDate ===")
    matches = html.find("queryStartDate")
    print(f"  queryStartDate 位置: {matches}")
    print(f"\n  tenderStartDate 相關 HTML:")
    idx = html.find("tenderStartDate")
    if idx > 0:
        print(html[max(0,idx-200):idx+300])
