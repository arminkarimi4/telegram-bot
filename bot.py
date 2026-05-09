import json
import os
from pathlib import Path

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)

TOKEN = "87208760:AAEm9TwoD4c8-ndZLAixw7KMBNaPTdF5Eys"

ADMINS = [400900388, 1483857146]

DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"

def load_users():
    """خواندن لیست کاربران از فایل JSON"""
    if not USERS_FILE.exists():
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_users(users: dict):
    """ذخیره لیست کاربران در فایل JSON"""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    users = load_users()

    if str(user.id) not in users:
        users[str(user.id)] = {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
        save_users(users)

    text = (
        "سلام 🌿\n"
    )

    await context.bot.send_message(
        chat_id=chat_id,
        text=text
    )

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMINS:
        await update.message.reply_text("شما دسترسی مدیریت ندارید ❌")
        return

    keyboard = [
        [InlineKeyboardButton("📊 آمار کاربران", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📂 لیست کاربران", callback_data="admin_userlist")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("🍃 پنل مدیریتی:", reply_markup=reply_markup)

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "admin_stats":
        users = load_users()
        count = len(users)
        text = f"📊 تعداد کل کاربران ثبت‌شده: {count}"
        await query.edit_message_text(text=text)

    elif data == "admin_userlist":
        users = load_users()
        if not users:
            await query.edit_message_text("هنوز کاربری ثبت نشده.")
            return

        lines = []
        for u in users.values():
            line = f"- {u.get('first_name','')} (@{u.get('username')}) | ID: {u['id']}"
            lines.append(line)

        text = "📂 لیست کاربران:\n\n" + "\n".join(lines[:50])
        # فقط ۵۰ تا اولی رو نشون می‌ده که پیام خیلی طولانی نشه
        await query.edit_message_text(text=text)

    # ارسال پیام همگانی (فعلاً بعداً پیاده‌سازی می‌کنیم)
    elif data == "admin_broadcast":
        await query.edit_message_text(
            "قابلیت ارسال پیام همگانی رو بعداً پیاده‌سازی می‌کنیم 🌿."
        )
        
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # هندلر ها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(admin_buttons))

    print("ربات فعال شد...")
    app.run_polling()

if __name__ == "__main__":
    main()
