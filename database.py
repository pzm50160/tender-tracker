import os
from datetime import datetime


def _get_db_url():
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    try:
        import streamlit as st
        return st.secrets.get("DATABASE_URL", "")
    except Exception:
        return ""


DATABASE_URL = _get_db_url()
_PG = bool(DATABASE_URL)
PH = "%s" if _PG else "?"


def get_conn():
    if _PG:
        import psycopg2
        import psycopg2.extras
        return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    import sqlite3
    from config import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    pk = "SERIAL" if _PG else "INTEGER"
    ai = "" if _PG else " AUTOINCREMENT"
    num = "NUMERIC" if _PG else "REAL"
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS tenders (
            id               {pk} PRIMARY KEY{ai},
            tender_id        TEXT UNIQUE,
            tender_name      TEXT,
            agency           TEXT,
            tender_case_no   TEXT,
            procurement_type TEXT,
            tender_way       TEXT,
            budget           {num},
            publish_date     TEXT,
            deadline         TEXT,
            detail_url       TEXT,
            matched_keyword  TEXT,
            fetched_at       TEXT,
            is_read          INTEGER DEFAULT 0
        )
    """)
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS fetch_log (
            id         {pk} PRIMARY KEY{ai},
            fetched_at TEXT,
            keyword    TEXT,
            count      INTEGER,
            status     TEXT
        )
    """)
    conn.commit()
    conn.close()


def upsert_tender(t: dict):
    conn = get_conn()
    cur = conn.cursor()
    try:
        vals = (
            t["tender_id"], t.get("tender_name"), t.get("agency"), t.get("tender_case_no"),
            t.get("procurement_type"), t.get("tender_way"), t.get("budget"),
            t.get("publish_date"), t.get("deadline"), t.get("detail_url"),
            t.get("matched_keyword"), t.get("fetched_at"),
        )
        ph12 = ",".join([PH] * 12)
        cur.execute(f"""
            INSERT INTO tenders (
                tender_id, tender_name, agency, tender_case_no,
                procurement_type, tender_way, budget,
                publish_date, deadline, detail_url,
                matched_keyword, fetched_at
            ) VALUES ({ph12})
            ON CONFLICT (tender_id) DO UPDATE SET
                tender_name      = EXCLUDED.tender_name,
                agency           = EXCLUDED.agency,
                tender_case_no   = EXCLUDED.tender_case_no,
                procurement_type = EXCLUDED.procurement_type,
                tender_way       = EXCLUDED.tender_way,
                budget           = EXCLUDED.budget,
                publish_date     = EXCLUDED.publish_date,
                deadline         = EXCLUDED.deadline,
                detail_url       = EXCLUDED.detail_url,
                matched_keyword  = EXCLUDED.matched_keyword,
                fetched_at       = EXCLUDED.fetched_at
        """, vals)
        conn.commit()
    finally:
        conn.close()


def get_tenders(date_from=None, date_to=None, keyword=None, unread_only=False):
    conn = get_conn()
    cur = conn.cursor()
    sql = "SELECT * FROM tenders WHERE 1=1"
    params = []
    if date_from:
        sql += f" AND publish_date >= {PH}"
        params.append(date_from)
    if date_to:
        sql += f" AND publish_date <= {PH}"
        params.append(date_to)
    if keyword:
        sql += f" AND (tender_name LIKE {PH} OR matched_keyword LIKE {PH} OR agency LIKE {PH})"
        params += [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
    if unread_only:
        sql += " AND is_read = 0"
    sql += " ORDER BY publish_date DESC, fetched_at DESC"
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_read(tender_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"UPDATE tenders SET is_read = 1 WHERE tender_id = {PH}", (tender_id,))
    conn.commit()
    conn.close()


def mark_all_read():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE tenders SET is_read = 1 WHERE is_read = 0")
    conn.commit()
    conn.close()


def log_fetch(keyword: str, count: int, status: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        f"INSERT INTO fetch_log (fetched_at, keyword, count, status) VALUES ({PH},{PH},{PH},{PH})",
        (datetime.now().isoformat(), keyword, count, status)
    )
    conn.commit()
    conn.close()


def get_fetch_logs(limit=100):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM fetch_log ORDER BY id DESC LIMIT {PH}", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS cnt FROM tenders")
    total = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) AS cnt FROM tenders WHERE is_read=0")
    unread = cur.fetchone()["cnt"]
    conn.close()
    return {"total": total, "unread": unread}
