import sqlite3

conn = sqlite3.connect("database/database.db")
cur = conn.cursor()

# ساخت جدول اگر وجود ندارد
cur.execute("""
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER,
    config TEXT,
    is_used INTEGER DEFAULT 0,
    used_by INTEGER,
    used_at TEXT
);
""")

conn.commit()
conn.close()

print("✅ inventory table is ready")

