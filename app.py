"""
健檢標案追蹤系統 — Streamlit 介面
執行: streamlit run app.py
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from database import init_db, get_tenders, mark_read, mark_all_read, get_fetch_logs, get_stats
from config import KEYWORDS, PROCUREMENT_TYPES, MIN_BUDGET, MAX_BUDGET

st.set_page_config(
    page_title="健檢標案追蹤",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# ── 樣式 ─────────────────────────────────────────────────
st.markdown("""
<style>
.card { background:#f8f9fa; border-left:4px solid #2196F3; border-radius:6px; padding:12px 16px; margin-bottom:10px; }
.card.unread { border-left-color:#E53935; background:#fff5f5; }
.card-title { font-size:1.05rem; font-weight:700; color:#1a1a2e; margin-bottom:6px; }
.card-meta  { font-size:0.85rem; color:#555; line-height:1.8; }
.badge { display:inline-block; padding:2px 9px; border-radius:12px; font-size:0.75rem; font-weight:600; margin-right:5px; }
.blue  { background:#e3f2fd; color:#1565C0; }
.green { background:#e8f5e9; color:#2E7D32; }
.red   { background:#ffebee; color:#B71C1C; }
.gray  { background:#f5f5f5; color:#424242; }
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

    st.divider()

    # 立即搜尋
    st.subheader("立即搜尋 PCC")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        search_from = st.date_input("起", value=date.today() - timedelta(days=7), label_visibility="visible")
    with col_s2:
        search_to = st.date_input("迄", value=date.today(), label_visibility="visible")

    if st.button("開始搜尋", type="primary", use_container_width=True):
        st.session_state["do_search"] = True
        st.session_state["s_from"] = search_from.strftime("%Y/%m/%d")
        st.session_state["s_to"]   = search_to.strftime("%Y/%m/%d")

    st.divider()
    st.caption("監控關鍵字")
    for kw in KEYWORDS:
        st.caption(f"  • {kw}")
    if PROCUREMENT_TYPES:
        st.caption(f"採購性質: {', '.join(PROCUREMENT_TYPES)}")

# ── 執行搜尋 ─────────────────────────────────────────────
if st.session_state.get("do_search"):
    st.session_state["do_search"] = False
    with st.spinner("正在搜尋政府電子採購網..."):
        try:
            from scraper import run_scraper
            count = run_scraper(
                start_date=st.session_state["s_from"],
                end_date=st.session_state["s_to"],
            )
            st.success(f"搜尋完成！共找到並更新 {count} 筆標案")
            st.rerun()
        except Exception as e:
            st.error(f"搜尋失敗：{e}")

# ── 主畫面 ───────────────────────────────────────────────
st.title("政府採購｜健檢標案追蹤系統")

stats = get_stats()
m1, m2, m3, m4 = st.columns(4)
m1.metric("資料庫總筆數", stats["total"])
m2.metric("未讀", stats["unread"])
m3.metric("關鍵字數", len(KEYWORDS))
m4.metric("最新更新", date.today().strftime("%Y/%m/%d"))

st.divider()

tab_list, tab_table, tab_stats, tab_log = st.tabs(["卡片檢視", "表格 / 匯出", "統計", "搜尋記錄"])

# 取得資料
tenders = get_tenders(
    date_from=date_from.strftime("%Y/%m/%d"),
    date_to=date_to.strftime("%Y/%m/%d"),
    keyword=kw_filter or None,
    unread_only=unread_only,
)


# ── 卡片檢視 ─────────────────────────────────────────────
with tab_list:
    col_a, col_b, _ = st.columns([1, 1, 4])
    with col_a:
        if st.button("全部已讀"):
            mark_all_read(); st.rerun()

    if not tenders:
        st.info("目前沒有資料。請點左側「開始搜尋」。")
    else:
        st.caption(f"共 {len(tenders)} 筆")
        for t in tenders:
            unread = not t["is_read"]
            card_cls = "card unread" if unread else "card"
            budget_str = f"{t['budget']:>12,.0f} 元" if t["budget"] else "未揭露"
            unread_badge = '<span class="badge red">未讀</span>' if unread else ""
            proc_badge   = f'<span class="badge blue">{t["procurement_type"] or "—"}</span>'
            kw_badge     = f'<span class="badge green">{t["matched_keyword"]}</span>'
            url_part = (f' | <a href="{t["detail_url"]}" target="_blank">查看詳情 ↗</a>'
                        if t["detail_url"] else "")

            tender_display = t["tender_name"] or t["tender_case_no"] or "（名稱未載入）"

            st.markdown(f"""
<div class="{card_cls}">
  <div class="card-title">{unread_badge}{proc_badge}{kw_badge} {tender_display}</div>
  <div class="card-meta">
    🏢 {t["agency"] or "—"} &nbsp;&nbsp;
    📋 {t["tender_case_no"] or "—"} &nbsp;&nbsp;
    💰 {budget_str} &nbsp;&nbsp;
    📅 公告：{t["publish_date"] or "—"} &nbsp;&nbsp;
    ⏰ 截止：{t["deadline"] or "—"}{url_part}
  </div>
</div>""", unsafe_allow_html=True)

            if unread:
                if st.button("標為已讀", key=f"r_{t['id']}"):
                    mark_read(t["tender_id"]); st.rerun()


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
