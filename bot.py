import json
import os
from pathlib import Path
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    _update
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

TOKEN = "87208760:AAEm9TwoD4c8-ndZLAixw7KMBNaPTdF5Eys"

ADMINS = [400900388, 1483857146]

DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"
BLOCKED_FILE = DATA_DIR / "blocked.json"

admin_state = {}

def load_json(file_path, default):
    if not file_path.exists():
        return default

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_users():
    return load_json(USERS_FILE, {})


def save_users(users):
    save_json(USERS_FILE, users)


def load_blocked():
    return load_json(BLOCKED_FILE, [])


def save_blocked(blocked):
    save_json(BLOCKED_FILE, blocked)


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

def register_user(user):
    users = load_users()
    user_id = str(user.id)

    if user_id not in users:
        users[user_id] = {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "joined_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        users[user_id]["username"] = user.username
        users[user_id]["first_name"] = user.first_name
        users[user_id]["last_name"] = user.last_name

    save_users(users) 

    if str(user.id) not in users:
        users[str(user.id)] = {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
        save_users(users)

    text = (
        "سلام\n"
    )

def register_user(user):
    users = load_users()
    users[user.id] = {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }
    save_users(users)  # فقط وظیفه ذخیره کاربر را دارد

# تابع شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)  # ثبت کاربر جدید

    chat_id = update.effective_chat.id
    text = "سلام خوش اومدی!"

    await context.bot.send_message(chat_id=chat_id,
                                   text=text,
                                   reply_markup=user_panel_keyboard(user.id)
)
    

def user_panel_keyboard(user_id):
    keyboard = [
        [KeyboardButton("پنل کاربری")],
        [KeyboardButton("راهنما")]
    ]

    if user_id in ADMINS:
        keyboard.append([KeyboardButton("پنل مدیریت")])

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def user_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == " پنل کاربری":
        await update.message.reply_text("به پنل کاربری خوش آمدید")

    elif text == "ℹ راهنما":
        await update.message.reply_text("برای استفاده از ربات از دکمه‌ها استفاده کنید.")

    elif text == " پنل مدیریت":
        user_id = update.effective_user.id

        if user_id not in ADMINS:
            await update.message.reply_text("❌ شما مدیر نیستید")
            return

        await update.message.reply_text("به پنل مدیریت خوش آمدید ")

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    await query.answer()

    if data == "user_panel":
        await query.message.reply_text(
            "🌿 پنل کاربری شما\n\n"
            "از دستورات ربات استفاده کن یا پیام بفرست."
        )
        return

    if user_id not in ADMINS and data != "user_panel":
        await query.message.reply_text("❌ دسترسی نداری.")
        return

    if data == "open_admin":
        keyboard = [
            [InlineKeyboardButton("📊 آمار کاربران", callback_data="admin_stats")],
            [InlineKeyboardButton("📅 آمار روزانه", callback_data="daily_stats")],
            [InlineKeyboardButton("📂 لیست کاربران", callback_data="admin_users")],
            [InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data="admin_broadcast")],
            [InlineKeyboardButton("✉️ ارسال به یک کاربر", callback_data="send_to_one")],
            [InlineKeyboardButton("🚫 بلاک کاربر", callback_data="block_user")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            "🛠 پنل مدیریت",
            reply_markup=reply_markup)

    elif data == "admin_stats":
        users = load_users()
        blocked = load_blocked()

        await query.message.reply_text(
            f"📊 آمار ربات\n\n"
            f"👤 تعداد کل کاربران: {len(users)}\n"
            f"🚫 کاربران بلاک‌شده: {len(blocked)}"
        )

    elif data == "daily_stats":
        users = load_users()
        today = datetime.now().strftime("%Y-%m-%d")

        count = 0
        for user in users.values():
            joined_at = user.get("joined_at", "")
            if joined_at.startswith(today):
                count += 1

        await query.message.reply_text(
            f"📅 آمار امروز\n\n"
            f"👤 کاربران جدید امروز: {count}"
        )

    elif data == "admin_users":
        users = load_users()

        if not users:
            await query.message.reply_text("هیچ کاربری ثبت نشده.")
            return

        text = "📂 لیست کاربران:\n\n"
        for user in list(users.values())[:50]:
            name = user.get("first_name") or "بدون نام"
            username = user.get("username") or "ندارد"
            joined_at = user.get("joined_at") or "نامشخص"

            text += (
                f"👤 {name}\n"
                f"🆔 {user['id']}\n"
                f"📎 @{username}\n"
                f"🕒 {joined_at}\n\n"
            )

        await query.message.reply_text(text)

    elif data == "admin_broadcast":
        admin_state[user_id] = {"mode": "broadcast"}
        await query.message.reply_text("📢 پیام همگانی را بفرست.")

    elif data == "send_to_one":
        admin_state[user_id] = {"mode": "send_to_one_waiting_id"}
        await query.message.reply_text("✉️ آیدی عددی کاربر را بفرست.")

    elif data == "block_user":
        admin_state[user_id] = {"mode": "block_user"}
        await query.message.reply_text("🚫 آیدی عددی کاربری که می‌خواهی بلاک شود را بفرست.")

def is_blocked(user_id: int):
    blocked = load_blocked()
    return user_id in blocked

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "راهنمای ربات\n\n"
        "/start - شروع ربات\n"
        "/help - نمایش راهنما\n"
        "/admin - پنل مدیریت\n\n"
        "اگر ادمین باشی، می‌تونی از پنل مدیریت استفاده کنی."
    )
    await update.message.reply_text(text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text.strip()

    register_user(user)

    if is_blocked(user_id):
        await update.message.reply_text("❌ شما توسط مدیر مسدود شده‌اید.")
        return

    if user_id in ADMINS and user_id in admin_state:
        state = admin_state[user_id]
        mode = state.get("mode")

        if mode == "broadcast":
            users = load_users()
            blocked = load_blocked()

            success = 0
            failed = 0

            for uid in users.keys():
                uid_int = int(uid)

                if uid_int in blocked:
                    continue

                try:
                    await context.bot.send_message(chat_id=uid_int, text=text)
                    success += 1
                except:
                    failed += 1

            del admin_state[user_id]

            await update.message.reply_text(
                f"✅ پیام همگانی ارسال شد.\n\n"
                f"✔️ موفق: {success}\n"
                f"❌ ناموفق: {failed}"
            )
            return

        elif mode == "send_to_one_waiting_id":
            if not text.isdigit():
                await update.message.reply_text("❌ آیدی باید عددی باشد. دوباره بفرست.")
                return

            admin_state[user_id] = {
                "mode": "send_to_one_waiting_message",
                "target_id": int(text)
            }

            await update.message.reply_text(" حالا پیام موردنظر را بفرست.")
            return

        elif mode == "send_to_one_waiting_message":
            target_id = state.get("target_id")

            try:
                await context.bot.send_message(chat_id=target_id, text=text)
                await update.message.reply_text("✅ پیام ارسال شد.")
            except:
                await update.message.reply_text("❌ ارسال پیام ناموفق بود.")

            del admin_state[user_id]
            return

        elif mode == "block_user":
            if not text.isdigit():
                await update.message.reply_text("❌ آیدی باید عددی باشد.")
                return

            target_id = int(text)
            blocked = load_blocked()

            if target_id not in blocked:
                blocked.append(target_id)
                save_blocked(blocked)

            del admin_state[user_id]

            await update.message.reply_text(f"کاربر {target_id} بلاک شد.")
            return

    await update.message.reply_text(
        f"پیام شما دریافت شد:\n\n{text}"
    )


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
            "قابلیت ارسال پیام همگانی رو بعداً پیاده‌سازی می‌کنیم."
        )
        
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMINS:
        await update.message.reply_text("❌ شما مدیر نیستید.")
        return

    keyboard = [
        [InlineKeyboardButton("📊 آمار کاربران", callback_data="open_admin")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "⚙️ پنل مدیریت",
        reply_markup=reply_markup
    )
    
         
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(admin_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_panel))


    print("✅ ربات فعال شد...")
    app.run_polling()


if __name__ == "__main__":
    main()

