import sqlite3
from config import DATABASE_PATH

conn = sqlite3.connect(DATABASE_PATH)
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE inventory ADD COLUMN used_by INTEGER;")
    cur.execute("ALTER TABLE inventory ADD COLUMN used_at TIMESTAMP;")
    conn.commit()
    print("ستون‌های جدید با موفقیت اضافه شدند! ✅")
except sqlite3.OperationalError as e:
    print("خطا:", e)

conn.close()