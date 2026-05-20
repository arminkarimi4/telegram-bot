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

# fix_bot.py
file_path = 'bot.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# جایگزین کردن عبارت‌های اشتباه با فضای خالی
new_content = content.replace(', filters=filters.ChatType.PRIVATE', '')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("فایل با موفقیت اصلاح شد!")
