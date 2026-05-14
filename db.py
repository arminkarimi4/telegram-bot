import os
import sqlite3
from config import DATABASE_PATH

# ساخت پوشه دیتابیس
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# =========================================
# اتصال دیتابیس
# =========================================
def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# =========================================
# ساخت جداول
# =========================================
def init_db():

    conn = get_connection()
    cur = conn.cursor()

    # کاربران
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        coins INTEGER DEFAULT 0,
        invites INTEGER DEFAULT 0,
        invited_by INTEGER,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_blocked INTEGER DEFAULT 0
    )
    """)

    # رفرال‌ها
    cur.execute("""
    CREATE TABLE IF NOT EXISTS referrals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inviter_id INTEGER,
        invited_id INTEGER UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # پلن‌ها
    cur.execute("""
    CREATE TABLE IF NOT EXISTS plans(
        id INTEGER PRIMARY KEY,
        name TEXT,
        price INTEGER,
        traffic TEXT
    )
    """)

    # انبار کانفیگ
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER,
        config TEXT,
        is_used INTEGER DEFAULT 0,
        used_by INTEGER,
        used_at TIMESTAMP
    )
    """)

    # ثبت دریافت پلن
    cur.execute("""
    CREATE TABLE IF NOT EXISTS claims(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plan_id INTEGER,
        config_id INTEGER,
        claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # لاگ‌ها
    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ثبت پلن‌ها
    plans = [
        (1, "15MB", 1, "15MB"),
        (2, "50MB", 3, "50MB"),
        (3, "80MB", 5, "80MB"),
        (4, "200MB", 10, "200MB"),
    ]

    for plan in plans:
        cur.execute("""
        INSERT OR IGNORE INTO plans(id, name, price, traffic)
        VALUES (?, ?, ?, ?)
        """, plan)

    conn.commit()
    conn.close()
