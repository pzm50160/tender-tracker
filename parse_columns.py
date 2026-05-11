from bs4 import BeautifulSoup

with open("data/final_isDate 健.html", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
tb = soup.find("table", class_="tb_01")

# 標題列
header_row = tb.find("tr")
ths = header_row.find_all(["th", "td"])
print("=== 欄位標題 ===")
for i, th in enumerate(ths):
    print(f"  [{i}] {th.get_text(strip=True)}")

# 資料列
print("\n=== 前 3 筆資料 ===")
data_rows = tb.find_all("tr")[1:]
for row in data_rows[:3]:
    cells = row.find_all("td")
    print(f"\n資料列 ({len(cells)} 欄):")
    for i, td in enumerate(cells):
        text = td.get_text(strip=True)
        links = td.find_all("a")
        link_info = [(l.get_text(strip=True), l.get("href","")) for l in links]
        print(f"  [{i}] text={text!r} links={link_info}")
