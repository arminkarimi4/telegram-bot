import json
import os
from pathlib import Path
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# --- تنظیمات ربات ---
TOKEN = "8720876053:AAEm9TwoD4c8-ndZLAixw7KMBNaPTdF5Eys"
ADMINS = [400900388, 1483857146] # لیست آیدی عددی ادمین ها
REQUIRED_CHANNELS = [
    "@Shotor_AR",
    "@shotorAR_GP"
]

# --- مدیریت فایل های داده ---
DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True) # ساخت پوشه data اگر وجود ندارد
USERS_FILE = DATA_DIR / "users.json"
BLOCKED_FILE = DATA_DIR / "blocked.json"

admin_state = {} # ذخیره موقت حالت ادمین برای عملیات چند مرحله ای

def load_json(file_path, default):
    """بارگذاری داده از فایل JSON یا برگرداندن مقدار پیش فرض در صورت خطا/نبود فایل."""
    if not file_path.exists():
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {file_path}. Returning default.")
        return default
    except Exception as e:
        print(f"An unexpected error occurred while loading {file_path}: {e}")
        return default

def save_json(file_path, data):
    """ذخیره داده در فایل JSON."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_users():
    """بارگذاری لیست کاربران."""
    return load_json(USERS_FILE, {})

def save_users(users):
    """ذخیره لیست کاربران."""
    save_json(USERS_FILE, users)

def load_blocked():
    """بارگذاری لیست کاربران بلاک شده."""
    return load_json(BLOCKED_FILE, [])

def save_blocked(blocked):
    """ذخیره لیست کاربران بلاک شده."""
    save_json(BLOCKED_FILE, blocked)

# --- توابع کمکی ربات ---
async def check_membership(user_id, context):
    """بررسی عضویت کاربر در کانال های اجباری."""
    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            print(f"Error checking membership for {user_id} in {channel}: {e}")
            return False
    return True

def join_channels_keyboard():
    """کیبورد اینلاین برای عضویت در کانال ها."""
    keyboard = [
        [InlineKeyboardButton("📢 کانال اول", url="https://t.me/Shotor_AR")],
        [InlineKeyboardButton("📢 کانال دوم", url="https://t.me/shotorAR_GP")],
        [InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_join")]
    ]
    return InlineKeyboardMarkup(keyboard)

def register_user(user, referrer_id=None):
    """ثبت نام کاربر جدید و اعمال سیستم رفرال."""
    users = load_users()
    uid = str(user.id)

    if uid not in users:
        users[uid] = {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "joined_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "coins": 0,
            "referrals": 0,
            "test_accounts": 0,
            "purchases": 0,
            "referrer": referrer_id # آیدی معرف
        }

        # اگر معرف وجود داشته باشد و خودش کاربر باشد، سکه اضافه شود
        if referrer_id and str(referrer_id) in users:
            users[str(referrer_id)]["coins"] += 1
            users[str(referrer_id)]["referrals"] += 1

    save_users(users)

def user_panel_keyboard(user_id):
    """کیبورد پاسخ (Reply Keyboard) برای پنل کاربری اصلی."""
    keyboard = [
        [KeyboardButton("خرید اشتراک")],
        [KeyboardButton("کیف پول"), KeyboardButton("شارژ کیف پول")],
        [KeyboardButton("سرویس های من")],
        [KeyboardButton("پشتیبانی")],
        [KeyboardButton("حساب کاربری")],
        [KeyboardButton("دریافت سکه رایگان")],
        [KeyboardButton("🔑 دریافت اکانت تست")]
    ]

    if user_id in ADMINS:
        keyboard.append([KeyboardButton("⚙️ پنل مدیریت")])

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

def is_blocked(user_id: int):
    """بررسی اینکه آیا کاربر بلاک شده است یا خیر."""
    blocked = load_blocked()
    return user_id in blocked

# --- هندلرها ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر دستور /start."""
    user = update.effective_user
    referrer_id = None

    if context.args:
        if context.args[0].isdigit():
            referrer_id = int(context.args[0])

    register_user(user, referrer_id)

    is_member = await check_membership(user.id, context)

    if not is_member:
        await update.message.reply_text(
            "برای استفاده از ربات، ابتدا در کانال های زیر عضو شوید.",
            reply_markup=join_channels_keyboard()
        )
        return

    await update.message.reply_text(
        "✅ عضویت شما تایید شد.\n\nخوش آمدید، ریحانه.\nیکی از گزینه‌های زیر را انتخاب کنید.",
        reply_markup=user_panel_keyboard(user.id)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر دستور /help."""
    text = (
        "راهنمای ربات\n\n"
        "/start - شروع ربات\n"
        "/help - نمایش راهنما\n"
        "/admin - پنل مدیریت (فقط برای ادمین ها)\n\n"
        "اگر ادمین باشی، می‌تونی از پنل مدیریت استفاده کنی."
    )
    await update.message.reply_text(text)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر دستور /admin."""
    user_id = update.effective_user.id

    if user_id not in ADMINS:
        await update.message.reply_text("❌ شما مدیر نیستید.")
        return

    # کیبورد اینلاین برای باز کردن پنل مدیریت (دکمه "آمار کاربران" برای ورود به پنل)
    keyboard = [
        [InlineKeyboardButton("📊 آمار و مدیریت", callback_data="open_admin")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "⚙️ پنل مدیریت",
        reply_markup=reply_markup
    )

async def user_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر پیام های متنی که از کیبورد اصلی کاربر می آیند."""
    text = update.message.text
    user_id = update.effective_user.id

    # خرید اشتراک
    if text == "خرید اشتراک":
        await update.message.reply_text(
            "بخش خرید اشتراک\n\n"
            "لطفا سرویس موردنظر خود را انتخاب کنید."
        )

    # کیف پول
    elif text == "کیف پول":
        await update.message.reply_text(
            "موجودی کیف پول شما:\n\n"
            "0 تومان" # این بخش نیاز به پیاده سازی منطق کیف پول دارد
        )

    # شارژ کیف پول
    elif text == "شارژ کیف پول":
        await update.message.reply_text(
            "بخش شارژ کیف پول\n\n"
            "مبلغ موردنظر را وارد کنید." # این بخش نیاز به پیاده سازی منطق شارژ دارد
        )

    # سرویس های من
    elif text == "سرویس های من":
        await update.message.reply_text(
            "لیست سرویس های فعال شما:\n\n"
            "هنوز سرویسی ندارید." # این بخش نیاز به پیاده سازی نمایش سرویس ها دارد
        )

    # پشتیبانی
    elif text == "پشتیبانی":
        await update.message.reply_text(
            "پشتیبانی\n\n"
            "پیام خود را ارسال کنید تا به تیم پشتیبانی منتقل شود." # این بخش نیاز به پیاده سازی منطق پشتیبانی دارد
        )

    # پنل مدیریت
    elif text == "⚙️ پنل مدیریت":
        if user_id not in ADMINS:
            await update.message.reply_text("❌ شما مدیر نیستید و دسترسی به این بخش ندارید.")
            return
        
        # نمایش کیبورد مدیریت اینلاین
        keyboard = [
            [InlineKeyboardButton("آمار کاربران", callback_data="admin_stats")],
            [InlineKeyboardButton("آمار روزانه", callback_data="daily_stats")],
            [InlineKeyboardButton("لیست کاربران", callback_data="admin_users")],
            [InlineKeyboardButton("ارسال پیام همگانی", callback_data="admin_broadcast")],
            [InlineKeyboardButton("ارسال به یک کاربر", callback_data="send_to_one")],
            [InlineKeyboardButton("بلاک کاربر", callback_data="block_user")]
        ]
        await update.message.reply_text(
            "⚙️ پنل مدیریت",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # حساب کاربری
    elif text == "حساب کاربری":
        users = load_users()
        user_data = users.get(str(user_id), {})

        coins = user_data.get("coins", 0)
        referrals = user_data.get("referrals", 0)
        tests = user_data.get("test_accounts", 0)
        purchases = user_data.get("purchases", 0)

        keyboard = [
            [InlineKeyboardButton(f"🪙 تعداد سکه: {coins}", callback_data="none")],
            [InlineKeyboardButton(f"👥 تعداد رفرال: {referrals}", callback_data="none")],
            [InlineKeyboardButton(f"🔑 اکانت تست: {tests}", callback_data="none")],
            [InlineKeyboardButton(f"🛒 تعداد خریدها: {purchases}", callback_data="none")]
        ]
        await update.message.reply_text(
            "اطلاعات حساب شما:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # دریافت سکه رایگان
    elif text == "دریافت سکه رایگان":
        bot_username = (await context.bot.get_me()).username
        invite_link = f"https://t.me/{bot_username}?start={user_id}"

        await update.message.reply_text(
            "با لینک زیر دوستان خود را دعوت کنید.\n"
            "به ازای هر دعوت موفق 1 سکه دریافت می‌کنید.\n\n"
            f"🔗 {invite_link}"
        )

    # دریافت اکانت تست
    elif text == "🔑 دریافت اکانت تست":
        keyboard = [
            [InlineKeyboardButton("یک سکه / 10MB (تست)", callback_data="test_1_10mb")],
            [InlineKeyboardButton("سه سکه / 50MB (تست)", callback_data="test_2_50mb")],
            [InlineKeyboardButton("پنج سکه / 80MB (تست)", callback_data="test_3_80mb")],
            [InlineKeyboardButton("ده سکه / 200MB (تست)", callback_data="test_4_200mb")]
        ]
        await update.message.reply_text(
            "یکی از گزینه ها را برای دریافت اکانت تست انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:
        # اگر پیام متنی شناخته شده ای نبود، به پنل اصلی برگردانده شود
        await update.message.reply_text(
            "گزینه نامعتبر است. لطفاً یکی از دکمه‌ها را انتخاب کنید.",
            reply_markup=user_panel_keyboard(user_id)
        )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر CallbackQuery ها (کلیک روی دکمه های اینلاین)."""
    query = update.callback_query
    await query.answer() # مهم: برای جلوگیری از ماندن حالت لودینگ روی دکمه

    user_id = query.from_user.id
    data = query.data

    # --- عملیات مربوط به عضویت ---
    if data == "check_join":
        is_member = await check_membership(user_id, context)
        if not is_member:
            await query.message.reply_text(
                "❌ شما هنوز در همه کانال های مورد نیاز عضو نشده‌اید. لطفاً ابتدا عضو شوید.",
                reply_markup=join_channels_keyboard()
            )
        else:
            await query.message.reply_text(
                "✅ عضویت شما تایید شد.\n\nبه پنل اصلی خوش آمدید، ریحانه.",
                reply_markup=user_panel_keyboard(user_id)
            )
        return

    # --- عملیات مربوط به اکانت تست ---
    # اکانت تست: یک سکه / 10MB
    elif data == "test_1_10mb":
        users = load_users()
        user = users.get(str(user_id))

        if not user:
            await query.message.reply_text("❌ اطلاعات کاربر پیدا نشد. لطفاً /start را بزنید.")
            return
        if user.get("coins", 0) < 1:
            await query.message.reply_text("❌ سکه کافی ندارید. برای دریافت سکه می‌توانید از بخش 'دریافت سکه رایگان' استفاده کنید.")
            return

        user["coins"] -= 1
        user["test_accounts"] = user.get("test_accounts", 0) + 1
        save_users(users)
        await query.message.reply_text("✅ اکانت تست 10MB برای شما فعال شد.")

    # اکانت تست: سه سکه / 50MB
    elif data == "test_2_50mb":
        users = load_users()
        user = users.get(str(user_id))

        if not user:
            await query.message.reply_text("❌ اطلاعات کاربر پیدا نشد. لطفاً /start را بزنید.")
            return
        if user.get("coins", 0) < 3:
            await query.message.reply_text("❌ سکه کافی ندارید. برای دریافت سکه می‌توانید از بخش 'دریافت سکه رایگان' استفاده کنید.")
            return

        user["coins"] -= 3
        user["test_accounts"] = user.get("test_accounts", 0) + 1
        save_users(users)
        await query.message.reply_text("✅ اکانت تست 50MB برای شما فعال شد.")

    # اکانت تست: پنج سکه / 80MB
    elif data == "test_3_80mb":
        users = load_users()
        user = users.get(str(user_id))

        if not user:
            await query.message.reply_text("❌ اطلاعات کاربر پیدا نشد. لطفاً /start را بزنید.")
            return
        if user.get("coins", 0) < 5:
            await query.message.reply_text("❌ سکه کافی ندارید. برای دریافت سکه می‌توانید از بخش 'دریافت سکه رایگان' استفاده کنید.")
            return

        user["coins"] -= 5
        user["test_accounts"] = user.get("test_accounts", 0) + 1
        save_users(users)
        await query.message.reply_text("✅ اکانت تست 80MB برای شما فعال شد.")

    # اکانت تست: ده سکه / 200MB
    elif data == "test_4_200mb":
        users = load_users()
        user = users.get(str(user_id))

        if not user:
            await query.message.reply_text("❌ اطلاعات کاربر پیدا نشد. لطفاً /start را بزنید.")
            return
        if user.get("coins", 0) < 10:
            await query.message.reply_text("❌ سکه کافی ندارید. برای دریافت سکه می‌توانید از بخش 'دریافت سکه رایگان' استفاده کنید.")
            return

        user["coins"] -= 10
        user["test_accounts"] = user.get("test_accounts", 0) + 1
        save_users(users)
        await query.message.reply_text("✅ اکانت تست 200MB برای شما فعال شد.")

    # --- عملیات مربوط به پنل ادمین ---
    # دسترسی ادمین
    elif data.startswith("admin_") or data == "open_admin":
        if user_id not in ADMINS:
            await query.message.reply_text("❌ دسترسی نداری. شما مدیر نیستید.")
            return

        # باز کردن پنل مدیریت (این دکمه فقط برای نمایش کیبورد کامل مدیریت است)
        if data == "open_admin":
            keyboard = [
                [InlineKeyboardButton("📊 آمار کاربران", callback_data="admin_stats")],
                [InlineKeyboardButton("📅 آمار روزانه", callback_data="daily_stats")],
                [InlineKeyboardButton("📝 لیست کاربران", callback_data="admin_users")],
                [InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data="admin_broadcast")],
                [InlineKeyboardButton("📨 ارسال به یک کاربر", callback_data="send_to_one")],
                [InlineKeyboardButton("🚫 بلاک کاربر", callback_data="block_user")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "🛠 پنل مدیریت کامل",
                reply_markup=reply_markup
            )

        # آمار کاربران
        elif data == "admin_stats":
            users = load_users()
            blocked = load_blocked()
            await query.message.reply_text(
                f"📊 آمار ربات\n\n"
                f"👤 تعداد کل کاربران: {len(users)}\n"
                f"🚫 کاربران بلاک شده: {len(blocked)}"
            )

        # آمار روزانه
        elif data == "daily_stats":
            users = load_users()
            today = datetime.now().strftime("%Y-%m-%d")
            count = 0
            for user_data in users.values():
                joined_at = user_data.get("joined_at", "")
                if joined_at.startswith(today):
                    count += 1
            await query.message.reply_text(
                f"📅 آمار امروز\n\n"
                f"👤 کاربران جدید امروز: {count}"
            )

        # لیست کاربران
        elif data == "admin_users":
            users = load_users()
            if not users:
                await query.message.reply_text("هیچ کاربری ثبت نشده است.")
                return
            
            text = "📋 لیست کاربران (50 کاربر اول):\n\n"
            for user_data in list(users.values())[:50]:
                name = user_data.get("first_name") or "بدون نام"
                username = user_data.get("username") or "ندارد"
                joined_at = user_data.get("joined_at") or "نامشخص"
                text += (
                    f"👤 {name}\n"
                    f"🆔 {user_data['id']}\n"
                    f"📎 @{username}\n"
                    f"🕒 {joined_at}\n\n"
                )
            await query.message.reply_text(text)

        # پیام همگانی
        elif data == "admin_broadcast":
            admin_state[user_id] = {"mode": "broadcast"}
            await query.message.reply_text("📨 پیام همگانی را ارسال کنید.")

        # ارسال به یک کاربر
        elif data == "send_to_one":
            admin_state[user_id] = {"mode": "send_to_one_waiting_id"}
            await query.message.reply_text("🆔 آیدی عددی کاربر مورد نظر را ارسال کنید.")

        # بلاک کاربر
        elif data == "block_user":
            admin_state[user_id] = {"mode": "block_user"}
            await query.message.reply_text("🚫 آیدی عددی کاربری که می‌خواهید بلاک شود را ارسال کنید.")

    # --- حالت پیش فرض برای دکمه های نامعتبر ---
    else:
        # اگر callback_data به "none" اشاره داشت (مثل دکمه های اطلاعات حساب کاربری)
        if data == "none":
            pass # کاری نکن
        else:
            await query.message.reply_text("❓ دکمه نامعتبر یا عملیات ناشناخته است.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر اصلی برای پیام های متنی (غیر از دستورات و CallbackQuery ها)."""
    user = update.effective_user
    user_id = user.id
    text = update.message.text.strip()

    register_user(user)

    # بررسی عضویت
    is_member = await check_membership(user_id, context)
    if not is_member:
        await update.message.reply_text(
            "❌ برای استفاده از ربات باید در کانال های مورد نیاز عضو شوید.",
            reply_markup=join_channels_keyboard()
        )
        return

    # بررسی بلاک بودن
    if is_blocked(user_id):
        await update.message.reply_text("❌ شما توسط مدیر مسدود شده‌اید و نمی‌توانید از ربات استفاده کنید.")
        return

    # مدیریت حالت ادمین برای عملیات چند مرحله ای (پیام همگانی، ارسال به یک کاربر، بلاک)
    if user_id in ADMINS and user_id in admin_state:
        state = admin_state[user_id]
        mode = state.get("mode")

        # حالت ارسال پیام همگانی
        if mode == "broadcast":
            users = load_users()
            blocked = load_blocked()
            success = 0
            failed = 0

            for uid in users.keys():
                uid_int = int(uid)
                if uid_int in blocked: # اگر کاربر بلاک شده بود، پیام برایش ارسال نشود
                    continue
                try:
                    await context.bot.send_message(chat_id=uid_int, text=text)
                    success += 1
                except Exception as e:
                    print(f"Failed to send broadcast to {uid_int}: {e}")
                    failed += 1
            
            del admin_state[user_id] # حذف حالت ادمین پس از اتمام عملیات
            await update.message.reply_text(
                f"✅ پیام همگانی ارسال شد.\n\n"
                f"✔️ موفق: {success}\n"
                f"❌ ناموفق: {failed}"
            )
            return

        # حالت انتظار برای آیدی کاربر برای ارسال به یک نفر
        elif mode == "send_to_one_waiting_id":
            if not text.isdigit():
                await update.message.reply_text("❌ آیدی باید یک عدد باشد. لطفاً دوباره آیدی عددی کاربر را ارسال کنید.")
                return
            admin_state[user_id] = {
                "mode": "send_to_one_waiting_message",
                "target_id": int(text)
            }
            await update.message.reply_text("حالا پیام مورد نظر را برای ارسال به این کاربر ارسال کنید.")
            return

        # حالت انتظار برای پیام جهت ارسال به یک نفر
        elif mode == "send_to_one_waiting_message":
            target_id = state.get("target_id")
            try:
                await context.bot.send_message(chat_id=target_id, text=text)
                await update.message.reply_text("✅ پیام با موفقیت ارسال شد.")
            except Exception as e:
                print(f"Failed to send message to {target_id}: {e}")
                await update.message.reply_text("❌ ارسال پیام ناموفق بود. ممکن است کاربر ربات را بلاک کرده باشد.")
            del admin_state[user_id]
            return

        # حالت بلاک کاربر
        elif mode == "block_user":
            if not text.isdigit():
                await update.message.reply_text("❌ آیدی باید عددی باشد. لطفاً دوباره آیدی عددی کاربر را ارسال کنید.")
                return
            target_id = int(text)
            blocked = load_blocked()
            if target_id not in blocked:
                blocked.append(target_id)
                save_blocked(blocked)
                await update.message.reply_text(f"🚫 کاربر {target_id} با موفقیت بلاک شد.")
            else:
                await update.message.reply_text(f"❕ کاربر {target_id} از قبل بلاک شده بود.")
            del admin_state[user_id]
            return

    # اگر پیام از ادمین نبود یا حالت ادمین فعالی وجود نداشت، به هندلر پنل کاربری فرستاده شود
    await user_panel_handler(update, context)


def main():
    """تابع اصلی برای راه اندازی ربات."""
    app = ApplicationBuilder().token(TOKEN).build()

    # --- هندلرهای دستورات ---
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command)) # تغییر نام به admin_command
    app.add_handler(CommandHandler("help", help_command))

    # --- هندلرهای CallbackQuery (دکمه های اینلاین) ---
    app.add_handler(CallbackQueryHandler(buttons))

    # --- هندلر پیام های متنی (غیر از دستورات) ---
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ ربات فعال شد...")
    app.run_polling()


if __name__ == "__main__":
    main()
