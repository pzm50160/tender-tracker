# 搜尋關鍵字（符合任一即列出）
KEYWORDS = [
    "健康檢查",
    "健檢",
    "體檢",
    "勞工健檢",
    "員工健康",
    "定期健檢",
    "一般健康檢查",
    "職場健檢",
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

# 資料存放路徑
DB_PATH = "data/tenders.db"

# 搜尋網址
PCC_URL = "https://web.pcc.gov.tw/pis/"
PCC_SEARCH_URL = "https://web.pcc.gov.tw/tps/QueryTender/query/searchTenderDateRange"
