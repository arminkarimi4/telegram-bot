from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BotCommand
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# =========================
# تنظیمات
# =========================

TOKEN = "8720876053:AAEm9TwoD4c8-ndZLAixw7KMBNaPTdF5Eys"

ADMINS = [400900388, 1483857146]

CHANNEL_IDS = [
    "@Shotor_AR",
    "@shotorAR_GP"
]

CHANNEL_LINKS = [
    "https://t.me/Shotor_AR",
    "https://t.me/shotorAR_GP"
]

users = set()

# =========================
# بررسی عضویت
# =========================

async def check_membership(bot, user_id):

    for channel in CHANNEL_IDS:

        try:
            member = await bot.get_chat_member(channel, user_id)

            if member.status in ["left", "kicked"]:
                return False

        except:
            return False

    return True

# =========================
# دکمه عضویت
# =========================

def join_channels_keyboard():

    keyboard = []

    for i, link in enumerate(CHANNEL_LINKS):

        keyboard.append([
            InlineKeyboardButton(
                f"عضویت در کانال {i+1}",
                url=link
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "✅ بررسی عضویت",
            callback_data="check_join"
        )
    ])

    return InlineKeyboardMarkup(keyboard)

# =========================
# پنل کاربر
# =========================

def user_panel_keyboard(user_id):

    keyboard = [

        [KeyboardButton("حساب کاربری")],

        [KeyboardButton("🪙 دریافت سکه رایگان")],

        [KeyboardButton("🐪 دریافت شتر رایگان")],

        [KeyboardButton("📩 دریافت شتر اختصاصی")]
    ]

    if user_id in ADMINS:

        keyboard.append([
            KeyboardButton("⚙️ پنل مدیریت")
        ])

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

# =========================
# استارت
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    users.add(user.id)

    is_member = await check_membership(
        context.bot,
        user.id
    )

    if not is_member:

        await update.message.reply_text(
            "❌ برای استفاده از ربات ابتدا در کانال ها عضو شوید.",
            reply_markup=join_channels_keyboard()
        )

        return

    await update.message.reply_text(
        "✅ عضویت شما تایید شد"
    )

    await update.message.reply_text(
        "✅ پنل اصلی",
        reply_markup=user_panel_keyboard(user.id)
    )

# =========================
# انتخاب زبان
# =========================

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "🇮🇷 فارسی",
                callback_data="lang_fa"
            ),

            InlineKeyboardButton(
                "🇬🇧 English",
                callback_data="lang_en"
            )
        ]
    ]

    await update.message.reply_text(
        "🌐 زبان خود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# پنل مدیریت
# =========================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in ADMINS:
        return

    keyboard = [

        [
            InlineKeyboardButton(
                "👥 آمار کاربران",
                callback_data="admin_stats"
            )
        ],

        [
            InlineKeyboardButton(
                "📅 آمار روزانه",
                callback_data="daily_stats"
            )
        ],

        [
            InlineKeyboardButton(
                "📋 لیست کاربران",
                callback_data="admin_users"
            )
        ],

        [
            InlineKeyboardButton(
                "📢 ارسال پیام همگانی",
                callback_data="admin_broadcast"
            )
        ],

        [
            InlineKeyboardButton(
                "📨 ارسال به یک کاربر",
                callback_data="send_to_one"
            )
        ],

        [
            InlineKeyboardButton(
                "🚫 بلاک کاربر",
                callback_data="block_user"
            )
        ],

        [
            InlineKeyboardButton(
                "🐪 شارژ شتر رایگان",
                callback_data="charge_camel"
            )
        ],

        [
            InlineKeyboardButton(
                "🪙 شارژ سکه",
                callback_data="charge_coin"
            )
        ]
    ]

    await update.message.reply_text(
        "⚙️ پنل مدیریت",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# پنل کاربر
# =========================

async def user_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    user = update.effective_user

    # حساب کاربری
    if text == "حساب کاربری":

        await update.message.reply_text(
            f"""
👤 اطلاعات حساب

🆔 آیدی عددی:
{user.id}

👤 نام:
{user.first_name}
"""
        )

    # سکه رایگان
    elif text == "🪙 دریافت سکه رایگان":

        await update.message.reply_text(
            "🪙 بزودی فعال می‌شود."
        )

    # شتر رایگان
    elif text == "🐪 دریافت شتر رایگان":

        keyboard = [

            [
                InlineKeyboardButton(
                    "یک سکه / 10MB(🐪 استخونی)",
                    callback_data="camel_1"
                )
            ],

            [
                InlineKeyboardButton(
                    "سه سکه / 50MB(🐪 نی قلیون)",
                    callback_data="camel_2"
                )
            ],

            [
                InlineKeyboardButton(
                    "پنج سکه / 80MB(🐪 فیت)",
                    callback_data="camel_3"
                )
            ],

            [
                InlineKeyboardButton(
                    "ده سکه / 200MB(🐪 توپر)",
                    callback_data="camel_4"
                )
            ]
        ]

        await update.message.reply_text(
            "🐪 یکی از گزینه ها را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # شتر اختصاصی
    elif text == "📩 دریافت شتر اختصاصی":

        keyboard = [
            [
                InlineKeyboardButton(
                    "📩 ارتباط با پشتیبانی",
                    url="https://t.me/arminkarimi4"
                )
            ]
        ]

        await update.message.reply_text(
            "برای دریافت شتر اختصاصی به آیدی زیر پیام دهید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # پنل مدیریت
    elif text == "⚙️ پنل مدیریت":

        await admin(update, context)

# =========================
# دکمه های اینلاین
# =========================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    data = query.data

    user_id = query.from_user.id

    # بررسی عضویت
    if data == "check_join":

        is_member = await check_membership(
            context.bot,
            user_id
        )

        if not is_member:

            await query.message.reply_text(
                "❌ شما هنوز در همه کانال ها عضو نشده‌اید.",
                reply_markup=join_channels_keyboard()
            )

        else:

            await query.message.reply_text(
                "✅ عضویت شما تایید شد"
            )

            await query.message.reply_text(
                "✅ پنل اصلی",
                reply_markup=user_panel_keyboard(user_id)
            )

    # شتر استخونی
    elif data == "camel_1":

        await query.message.reply_text(
            "🐪 شتر استخونی بزودی ارسال می‌شود."
        )

    # شتر نی قلیون
    elif data == "camel_2":

        await query.message.reply_text(
            "🐪 شتر نی قلیون بزودی ارسال می‌شود."
        )

    # شتر فیت
    elif data == "camel_3":

        await query.message.reply_text(
            "🐪 شتر فیت بزودی ارسال می‌شود."
        )

    # شتر توپر
    elif data == "camel_4":

        await query.message.reply_text(
            "🐪 شتر توپر بزودی ارسال می‌شود."
        )

    # آمار کاربران
    elif data == "admin_stats":

        await query.message.reply_text(
            f"👥 تعداد کاربران:\n{len(users)}"
        )

    # آمار روزانه
    elif data == "daily_stats":

        await query.message.reply_text(
            "📅 آمار روزانه بزودی اضافه می‌شود."
        )

    # لیست کاربران
    elif data == "admin_users":

        await query.message.reply_text(
            "📋 لیست کاربران بزودی اضافه می‌شود."
        )

    # ارسال همگانی
    elif data == "admin_broadcast":

        await query.message.reply_text(
            "📢 بخش ارسال همگانی بزودی اضافه می‌شود."
        )

    # ارسال به یک کاربر
    elif data == "send_to_one":

        await query.message.reply_text(
            "📨 بخش ارسال به یک کاربر بزودی اضافه می‌شود."
        )

    # بلاک کاربر
    elif data == "block_user":

        await query.message.reply_text(
            "🚫 بخش بلاک کاربر بزودی اضافه می‌شود."
        )

    # شارژ شتر
    elif data == "charge_camel":

        await query.message.reply_text(
            "🐪 بخش شارژ شتر رایگان فعال شد."
        )

    # شارژ سکه
    elif data == "charge_coin":

        await query.message.reply_text(
            "🪙 بخش شارژ سکه فعال شد."
        )

    # زبان فارسی
    elif data == "lang_fa":

        context.user_data["lang"] = "fa"

        await query.message.reply_text(
            "✅ زبان شما روی فارسی تنظیم شد."
        )

        await query.message.reply_text(
            "♻️ برای شروع مجدد /start را بزنید."
        )

    # زبان انگلیسی
    elif data == "lang_en":

        context.user_data["lang"] = "en"

        await query.message.reply_text(
            "🇬🇧 Your language is set to English."
        )

        await query.message.reply_text(
            "♻️ Press /start to restart."
        )

# =========================
# منوی دستورات تلگرام
# =========================

async def set_commands(app):

    commands = [

        BotCommand(
            "start",
            "♻️ شروع مجدد"
        ),

        BotCommand(
            "language",
            "🌐 انتخاب زبان"
        )
    ]

    await app.bot.set_my_commands(commands)

# =========================
# اجرای ربات
# =========================

def main():

    app = Application.builder().token(TOKEN).build()

    # تنظیم منوی تلگرام
    app.post_init = set_commands

    # هندلرها
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("language", language)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            user_panel_handler
        )
    )

    app.add_handler(
        CallbackQueryHandler(buttons)
    )

    print("Bot is running...")

    app.run_polling()

# =========================

if __name__ == "__main__":
    main()
