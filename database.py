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


def _ph():
    return "%s" if _get_db_url() else "?"


def get_conn():
    db_url = _get_db_url()
    if db_url:
        import psycopg2
        import psycopg2.extras
        return psycopg2.connect(db_url, cursor_factory=psycopg2.extras.RealDictCursor)
    import sqlite3
    from config import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_keywords():
    import json
    from config import KEYWORDS as DEFAULT_KEYWORDS
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT value FROM settings WHERE key = 'keywords'")
        row = cur.fetchone()
        if row:
            return json.loads(row["value"])
    except Exception:
        pass
    finally:
        conn.close()
    return DEFAULT_KEYWORDS


def save_keywords(keywords: list):
    import json
    ph = _ph()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"""
        INSERT INTO settings (key, value) VALUES ({ph}, {ph})
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """, ("keywords", json.dumps(keywords, ensure_ascii=False)))
    conn.commit()
    conn.close()


def init_db():
    pg = bool(_get_db_url())
    conn = get_conn()
    cur = conn.cursor()
    pk = "SERIAL" if pg else "INTEGER"
    ai = "" if pg else " AUTOINCREMENT"
    num = "NUMERIC" if pg else "REAL"
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)
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
            opening_date     TEXT,
            detail_url       TEXT,
            matched_keyword  TEXT,
            fetched_at       TEXT,
            is_read          INTEGER DEFAULT 0
        )
    """)
    # 遷移：為舊資料表補欄位
    if pg:
        try:
            cur.execute("ALTER TABLE tenders ADD COLUMN IF NOT EXISTS opening_date TEXT")
        except Exception:
            conn.rollback()
    else:
        try:
            cur.execute("ALTER TABLE tenders ADD COLUMN opening_date TEXT")
        except Exception:
            pass
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


def delete_old_tenders(months: int = 3):
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(days=months * 30)).strftime("%Y/%m/%d")
    ph = _ph()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM tenders WHERE publish_date < {ph}", (cutoff,))
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted


def upsert_tender(t: dict):
    ph = _ph()
    conn = get_conn()
    cur = conn.cursor()
    try:
        vals = (
            t["tender_id"], t.get("tender_name"), t.get("agency"), t.get("tender_case_no"),
            t.get("procurement_type"), t.get("tender_way"), t.get("budget"),
            t.get("publish_date"), t.get("deadline"), t.get("opening_date"),
            t.get("detail_url"), t.get("matched_keyword"), t.get("fetched_at"),
        )
        ph13 = ",".join([ph] * 13)
        cur.execute(f"""
            INSERT INTO tenders (
                tender_id, tender_name, agency, tender_case_no,
                procurement_type, tender_way, budget,
                publish_date, deadline, opening_date, detail_url,
                matched_keyword, fetched_at
            ) VALUES ({ph13})
            ON CONFLICT (tender_id) DO UPDATE SET
                tender_name      = EXCLUDED.tender_name,
                agency           = EXCLUDED.agency,
                tender_case_no   = EXCLUDED.tender_case_no,
                procurement_type = EXCLUDED.procurement_type,
                tender_way       = EXCLUDED.tender_way,
                budget           = EXCLUDED.budget,
                publish_date     = EXCLUDED.publish_date,
                deadline         = EXCLUDED.deadline,
                opening_date     = EXCLUDED.opening_date,
                detail_url       = EXCLUDED.detail_url,
                matched_keyword  = EXCLUDED.matched_keyword,
                fetched_at       = EXCLUDED.fetched_at
        """, vals)
        conn.commit()
    finally:
        conn.close()


def get_tenders(date_from=None, date_to=None, keyword=None, unread_only=False, active_keywords=None):
    ph = _ph()
    conn = get_conn()
    cur = conn.cursor()
    sql = "SELECT * FROM tenders WHERE 1=1"
    params = []
    if date_from:
        sql += f" AND publish_date >= {ph}"
        params.append(date_from)
    if date_to:
        sql += f" AND publish_date <= {ph}"
        params.append(date_to)
    if keyword:
        sql += f" AND (tender_name LIKE {ph} OR matched_keyword LIKE {ph} OR agency LIKE {ph})"
        params += [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
    if unread_only:
        sql += " AND is_read = 0"
    if active_keywords:
        placeholders = ",".join([ph] * len(active_keywords))
        sql += f" AND matched_keyword IN ({placeholders})"
        params += list(active_keywords)
    sql += " ORDER BY publish_date DESC, fetched_at DESC"
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_read(tender_id: str):
    ph = _ph()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"UPDATE tenders SET is_read = 1 WHERE tender_id = {ph}", (tender_id,))
    conn.commit()
    conn.close()


def mark_all_read():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE tenders SET is_read = 1 WHERE is_read = 0")
    conn.commit()
    conn.close()


def log_fetch(keyword: str, count: int, status: str):
    ph = _ph()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        f"INSERT INTO fetch_log (fetched_at, keyword, count, status) VALUES ({ph},{ph},{ph},{ph})",
        (datetime.now().isoformat(), keyword, count, status)
    )
    conn.commit()
    conn.close()


def get_fetch_logs(limit=100):
    ph = _ph()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM fetch_log ORDER BY id DESC LIMIT {ph}", (limit,))
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
