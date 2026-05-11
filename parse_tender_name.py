from bs4 import BeautifulSoup

with open("data/final_isDate 健.html", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
tb = soup.find("table", class_="tb_01")
rows = tb.find_all("tr")[1:3]

for row in rows:
    cells = row.find_all("td")
    print("\n=== 第2欄原始 HTML ===")
    if len(cells) > 2:
        print(cells[2])
    print("\n=== 第3欄原始 HTML ===")
    if len(cells) > 3:
        print(cells[3])
