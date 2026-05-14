# 搜尋關鍵字（符合任一即列出）
KEYWORDS = [
    "健康檢查",
    "健檢",
    "體檢",
    "委託檢驗",
    "病理",
    "細胞",
    "重金屬",
    "臺北榮民總醫院桃園分院",
    "金門縣採購招標所",
    "衛生福利部臺南教養院",
    "委託代檢",
    "衛生福利部嘉南療養院",
    "衛生福利部胸腔病院",
    "臺南市政府衛生局",
]

# 採購性質篩選（可複選）
# "工程類", "財物類", "勞務類", "全部"
PROCUREMENT_TYPES = ["勞務類", "財物類"]

# 預算金額下限（元），None 表示不限
MIN_BUDGET = None

# 預算金額上限（元），None 表示不限
MAX_BUDGET = None

# 地區篩選（空白表示全台灣）
REGIONS = []

# 資料存放路徑（絕對路徑，確保無論從哪個目錄啟動都找到同一個檔案）
import os as _os
DB_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "data", "tenders.db")

# 搜尋網址
PCC_URL = "https://web.pcc.gov.tw/pis/"
PCC_SEARCH_URL = "https://web.pcc.gov.tw/tps/QueryTender/query/searchTenderDateRange"
