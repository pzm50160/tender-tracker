"""
健檢標案追蹤系統 — Streamlit 介面
執行: streamlit run app.py
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from database import init_db, get_tenders, mark_read, mark_all_read, mark_bid, get_fetch_logs, get_stats, get_keywords, save_keywords
from config import PROCUREMENT_TYPES, MIN_BUDGET, MAX_BUDGET

st.set_page_config(
    page_title="健檢標案追蹤",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

CARDS_PER_PAGE = 20

if "cache_buster" not in st.session_state:
    st.session_state["cache_buster"] = 0
if "page" not in st.session_state:
    st.session_state["page"] = 0

@st.cache_data(show_spinner=False)
def fetch_tenders(cb, date_from, date_to, keyword, unread_only, active_keywords_tuple, bid_only):
    return get_tenders(
        date_from=date_from, date_to=date_to, keyword=keyword,
        unread_only=unread_only,
        active_keywords=list(active_keywords_tuple) if active_keywords_tuple else None,
        bid_only=bid_only,
    )

def invalidate_cache():
    st.session_state["cache_buster"] += 1

# ── 樣式 ─────────────────────────────────────────────────
st.markdown("""
<style>
.card { background:#f8f9fa; border-left:4px solid #2196F3; border-radius:6px; padding:12px 16px; margin-bottom:10px; }
.card.unread { border-left-color:#E53935; background:#fff5f5; }
.card.bid   { border-left-color:#7B1FA2; background:#f3e5f5; }
.card.bid.unread { border-left-color:#7B1FA2; background:#ede7f6; }
.card-title { font-size:1.05rem; font-weight:700; color:#1a1a2e; margin-bottom:6px; }
.card-meta  { font-size:0.85rem; color:#555; line-height:1.8; }
.badge { display:inline-block; padding:2px 9px; border-radius:12px; font-size:0.75rem; font-weight:600; margin-right:5px; }
.blue  { background:#e3f2fd; color:#1565C0; }
.green { background:#e8f5e9; color:#2E7D32; }
.red   { background:#ffebee; color:#B71C1C; }
.gray   { background:#f5f5f5; color:#424242; }
.purple { background:#ede7f6; color:#4527A0; }
</style>
""", unsafe_allow_html=True)

# ── 側邊欄 ───────────────────────────────────────────────
with st.sidebar:
    st.title("🏥 健檢標案追蹤")
    st.divider()

    # 篩選
    st.subheader("篩選")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        date_from = st.date_input("從", value=date.today() - timedelta(days=30), label_visibility="visible")
    with col_d2:
        date_to = st.date_input("至", value=date.today(), label_visibility="visible")
    kw_filter = st.text_input("關鍵字", placeholder="機關名稱 / 標案名稱")
    unread_only = st.toggle("只看未讀", value=False)
    bid_only    = st.toggle("顯示所有已投標", value=False)

    st.divider()

    # 立即搜尋
    st.subheader("立即搜尋 PCC")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        search_from = st.date_input("起", value=date.today() - timedelta(days=7), label_visibility="visible")
    with col_s2:
        search_to = st.date_input("迄", value=date.today(), label_visibility="visible")

    ALL_PROC_TYPES = ["工程類", "財物類", "勞務類"]
    selected_types = st.multiselect(
        "採購性質",
        options=ALL_PROC_TYPES,
        default=ALL_PROC_TYPES,
        help="不選等同全部"
    )

    if st.button("開始搜尋", type="primary", use_container_width=True):
        st.session_state["do_search"] = True
        st.session_state["s_from"] = search_from.strftime("%Y/%m/%d")
        st.session_state["s_to"]   = search_to.strftime("%Y/%m/%d")
        st.session_state["s_types"] = selected_types if selected_types != ALL_PROC_TYPES else []

    st.divider()
    st.subheader("監控關鍵字")
    keywords = get_keywords()
    for kw in keywords:
        col_kw, col_del = st.columns([4, 1])
        col_kw.caption(f"• {kw}")
        if col_del.button("✕", key=f"del_{kw}"):
            keywords.remove(kw)
            save_keywords(keywords)
            st.rerun()
    new_kw = st.text_input("新增關鍵字", placeholder="輸入後按 Enter", label_visibility="collapsed")
    if new_kw and new_kw not in keywords:
        keywords.append(new_kw)
        save_keywords(keywords)
        st.rerun()

# ── 執行搜尋 ─────────────────────────────────────────────
if st.session_state.get("do_search"):
    st.session_state["do_search"] = False
    with st.spinner("正在搜尋政府電子採購網..."):
        try:
            import importlib, traceback
            import scraper as _scraper_mod
            importlib.reload(_scraper_mod)
            run_scraper = _scraper_mod.run_scraper
            count = run_scraper(
                start_date=st.session_state["s_from"],
                end_date=st.session_state["s_to"],
                procurement_types=st.session_state.get("s_types") or None,
            )
            invalidate_cache()
            if count > 0:
                st.success(f"搜尋完成！共找到並更新 {count} 筆標案")
            else:
                st.warning("搜尋完成，但沒有符合條件的標案（可嘗試擴大日期範圍或新增關鍵字）")
            st.rerun()
        except Exception as e:
            st.error(f"搜尋失敗：{e}")
            st.code(traceback.format_exc())

# ── 主畫面 ───────────────────────────────────────────────
st.title("政府採購｜健檢標案追蹤系統")

# 篩選條件變動時重置頁碼
_filter_key = (date_from, date_to, kw_filter, unread_only, bid_only, tuple(keywords))
if st.session_state.get("last_filter_key") != _filter_key:
    st.session_state["last_filter_key"] = _filter_key
    st.session_state["page"] = 0

# 取得資料
tenders = fetch_tenders(
    cb=st.session_state["cache_buster"],
    date_from=date_from.strftime("%Y/%m/%d"),
    date_to=date_to.strftime("%Y/%m/%d"),
    keyword=kw_filter or None,
    unread_only=unread_only,
    active_keywords_tuple=tuple(keywords),
    bid_only=bid_only,
)

unread_count = sum(1 for t in tenders if not t["is_read"])
m1, m2, m3, m4 = st.columns(4)
m1.metric("標案筆數", len(tenders))
m2.metric("未讀", unread_count)
m3.metric("關鍵字數", len(keywords))
logs = get_fetch_logs(1)
last_update = logs[0]["fetched_at"][:10] if logs else "尚無記錄"
m4.metric("最新更新", last_update)

st.divider()

tab_list, tab_table, tab_stats, tab_log = st.tabs(["卡片檢視", "表格 / 匯出", "統計", "搜尋記錄"])


# ── 卡片檢視 ─────────────────────────────────────────────
with tab_list:
    col_a, col_b, _ = st.columns([1, 1, 4])
    with col_a:
        if st.button("全部已讀"):
            mark_all_read(); invalidate_cache(); st.rerun()

    if not tenders:
        st.info("目前沒有資料。請點左側「開始搜尋」。")
    else:
        total_pages = max(1, (len(tenders) + CARDS_PER_PAGE - 1) // CARDS_PER_PAGE)
        page = min(st.session_state["page"], total_pages - 1)
        st.session_state["page"] = page
        page_tenders = tenders[page * CARDS_PER_PAGE:(page + 1) * CARDS_PER_PAGE]

        # 分頁控制列
        pg_cols = st.columns([1, 1, 3, 1, 1])
        if pg_cols[0].button("⏮", disabled=(page == 0)):
            st.session_state["page"] = 0; st.rerun()
        if pg_cols[1].button("◀", disabled=(page == 0)):
            st.session_state["page"] -= 1; st.rerun()
        pg_cols[2].markdown(f"<div style='text-align:center;padding-top:6px'>第 {page+1} / {total_pages} 頁　共 {len(tenders)} 筆</div>", unsafe_allow_html=True)
        if pg_cols[3].button("▶", disabled=(page >= total_pages - 1)):
            st.session_state["page"] += 1; st.rerun()
        if pg_cols[4].button("⏭", disabled=(page >= total_pages - 1)):
            st.session_state["page"] = total_pages - 1; st.rerun()

        st.divider()
        for t in page_tenders:
            unread = not t["is_read"]
            is_bid_flag = bool(t.get("is_bid"))
            if is_bid_flag and unread:
                card_cls = "card bid unread"
            elif is_bid_flag:
                card_cls = "card bid"
            elif unread:
                card_cls = "card unread"
            else:
                card_cls = "card"
            budget_str = f"{t['budget']:>12,.0f} 元" if t["budget"] else "未揭露"
            unread_badge = '<span class="badge red">未讀</span>' if unread else ""
            bid_badge    = '<span class="badge purple">已投標</span>' if is_bid_flag else ""
            proc_badge   = f'<span class="badge blue">{t["procurement_type"] or "—"}</span>'
            kw_badge     = f'<span class="badge green">{t["matched_keyword"]}</span>'
            url_part = (f' | <a href="{t["detail_url"]}" target="_blank">查看詳情 ↗</a>'
                        if t["detail_url"] else "")

            tender_display = t["tender_name"] or t["tender_case_no"] or "（名稱未載入）"

            st.markdown(f"""
<div class="{card_cls}">
  <div class="card-title">{unread_badge}{bid_badge}{proc_badge}{kw_badge} {tender_display}</div>
  <div class="card-meta">
    🏢 {t["agency"] or "—"} &nbsp;&nbsp;
    📋 {t["tender_case_no"] or "—"} &nbsp;&nbsp;
    💰 {budget_str} &nbsp;&nbsp;
    📅 公告：{t["publish_date"] or "—"} &nbsp;&nbsp;
    ⏰ 截止：{t["deadline"] or "—"}{url_part}
  </div>
</div>""", unsafe_allow_html=True)

            btn_cols = st.columns([1, 1, 6])
            if unread:
                if btn_cols[0].button("標為已讀", key=f"r_{t['id']}"):
                    mark_read(t["tender_id"]); invalidate_cache(); st.rerun()
            if is_bid_flag:
                if btn_cols[1].button("取消已投標", key=f"ub_{t['id']}"):
                    mark_bid(t["tender_id"], False); invalidate_cache(); st.rerun()
            else:
                if btn_cols[1].button("標為已投標", key=f"b_{t['id']}"):
                    mark_bid(t["tender_id"], True); invalidate_cache(); st.rerun()


# ── 表格 / 匯出 ──────────────────────────────────────────
with tab_table:
    if not tenders:
        st.info("無資料")
    else:
        df = pd.DataFrame(tenders)
        show = ["tender_name", "agency", "tender_case_no",
                "procurement_type", "budget", "publish_date", "deadline",
                "matched_keyword", "is_read"]
        df_show = df[[c for c in show if c in df.columns]].rename(columns={
            "tender_name":      "標案名稱",
            "agency":           "機關",
            "tender_case_no":   "案號",
            "procurement_type": "採購性質",
            "budget":           "預算(元)",
            "publish_date":     "公告日",
            "deadline":         "截止投標",
            "matched_keyword":  "關鍵字",
            "is_read":          "已讀",
        })
        st.dataframe(df_show, use_container_width=True, height=500)

        csv = df_show.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("下載 CSV", csv, "健檢標案.csv", "text/csv")


# ── 統計 ─────────────────────────────────────────────────
with tab_stats:
    if tenders:
        df = pd.DataFrame(tenders)
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("依關鍵字")
            kc = df["matched_keyword"].value_counts().reset_index()
            kc.columns = ["關鍵字", "筆數"]
            st.bar_chart(kc.set_index("關鍵字"))
        with c2:
            st.subheader("依採購性質")
            pc = df["procurement_type"].value_counts().reset_index()
            pc.columns = ["採購性質", "筆數"]
            st.bar_chart(pc.set_index("採購性質"))

        df["budget"] = pd.to_numeric(df["budget"], errors="coerce")
        bd = df[df["budget"].notna()].nlargest(15, "budget")[["tender_name", "budget"]]
        if not bd.empty:
            st.subheader("前 15 高預算標案")
            st.bar_chart(bd.set_index("tender_name"))
    else:
        st.info("無資料")


# ── 搜尋記錄 ─────────────────────────────────────────────
with tab_log:
    logs = get_fetch_logs(100)
    if logs:
        st.dataframe(
            pd.DataFrame(logs)[["fetched_at", "keyword", "count", "status"]],
            use_container_width=True
        )
    else:
        st.info("尚無記錄")
