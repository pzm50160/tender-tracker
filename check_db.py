from database import get_tenders, get_stats
stats = get_stats()
print(f"資料庫統計: total={stats['total']}, unread={stats['unread']}")
tenders = get_tenders()
print(f"\n前 5 筆標案:")
for t in tenders[:5]:
    name = t["tender_name"] or "(無名稱)"
    print(f"  [{t['matched_keyword']}] {name}")
    print(f"   機關: {t['agency']}")
    print(f"   案號: {t['tender_case_no']} | 採購: {t['procurement_type']}")
    print(f"   預算: {t['budget']} | 公告: {t['publish_date']} | 截止: {t['deadline']}")
    print()
