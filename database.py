import sqlite3
from datetime import datetime
from config import DB_PATH


def get_conn():
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
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT (key) DO UPDATE SET value = excluded.value
    """, ("keywords", json.dumps(keywords, ensure_ascii=False)))
    conn.commit()
    conn.close()


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tenders (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            tender_id        TEXT UNIQUE,
            tender_name      TEXT,
            agency           TEXT,
            tender_case_no   TEXT,
            procurement_type TEXT,
            tender_way       TEXT,
            budget           REAL,
            publish_date     TEXT,
            deadline         TEXT,
            opening_date     TEXT,
            detail_url       TEXT,
            matched_keyword  TEXT,
            fetched_at       TEXT,
            is_read          INTEGER DEFAULT 0,
            is_bid           INTEGER DEFAULT 0
        )
    """)
    # 遷移：為舊資料補欄位
    for col, definition in [("opening_date", "TEXT"), ("is_bid", "INTEGER DEFAULT 0")]:
        try:
            cur.execute(f"ALTER TABLE tenders ADD COLUMN {col} {definition}")
        except Exception:
            pass
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fetch_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
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
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM tenders WHERE publish_date < ?", (cutoff,))
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted


def upsert_tender(t: dict):
    conn = get_conn()
    cur = conn.cursor()
    try:
        vals = (
            t["tender_id"], t.get("tender_name"), t.get("agency"), t.get("tender_case_no"),
            t.get("procurement_type"), t.get("tender_way"), t.get("budget"),
            t.get("publish_date"), t.get("deadline"), t.get("opening_date"),
            t.get("detail_url"), t.get("matched_keyword"), t.get("fetched_at"),
        )
        cur.execute("""
            INSERT INTO tenders (
                tender_id, tender_name, agency, tender_case_no,
                procurement_type, tender_way, budget,
                publish_date, deadline, opening_date, detail_url,
                matched_keyword, fetched_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT (tender_id) DO UPDATE SET
                tender_name      = excluded.tender_name,
                agency           = excluded.agency,
                tender_case_no   = excluded.tender_case_no,
                procurement_type = excluded.procurement_type,
                tender_way       = excluded.tender_way,
                budget           = excluded.budget,
                publish_date     = excluded.publish_date,
                deadline         = excluded.deadline,
                opening_date     = excluded.opening_date,
                detail_url       = excluded.detail_url,
                matched_keyword  = excluded.matched_keyword,
                fetched_at       = excluded.fetched_at
        """, vals)
        conn.commit()
    finally:
        conn.close()


def get_tenders(date_from=None, date_to=None, keyword=None, unread_only=False, active_keywords=None, bid_only=False):
    conn = get_conn()
    cur = conn.cursor()
    sql = "SELECT * FROM tenders WHERE 1=1"
    params = []
    if bid_only:
        sql += " AND is_bid = 1"
    else:
        if date_from:
            sql += " AND publish_date >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND publish_date <= ?"
            params.append(date_to)
        if unread_only:
            sql += " AND is_read = 0"
        if active_keywords:
            sql += f" AND matched_keyword IN ({','.join(['?'] * len(active_keywords))})"
            params += list(active_keywords)
    if keyword:
        sql += " AND (tender_name LIKE ? OR matched_keyword LIKE ? OR agency LIKE ?)"
        params += [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
    sql += " ORDER BY publish_date DESC, fetched_at DESC, id DESC"
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_bid(tender_id: str, bid: bool = True):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE tenders SET is_bid = ? WHERE tender_id = ?", (1 if bid else 0, tender_id))
    conn.commit()
    conn.close()


def mark_read(tender_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE tenders SET is_read = 1 WHERE tender_id = ?", (tender_id,))
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
        "INSERT INTO fetch_log (fetched_at, keyword, count, status) VALUES (?,?,?,?)",
        (datetime.now().isoformat(), keyword, count, status)
    )
    conn.commit()
    conn.close()


def get_fetch_logs(limit=100):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM fetch_log ORDER BY id DESC LIMIT ?", (limit,))
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
