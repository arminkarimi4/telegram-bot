import json
import os
import datetime

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    MenuButtonCommands
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ====================================
# تنظیمات
# ====================================

TOKEN = "8720876053:AAEm9TwoD4c8-ndZLAixw7KMBNaPTdF5Eys"

ADMIN_ID = [
    400900388,
    1483857146
]

CHANNELS = [
    "@Shotor_AR",
    "@shotorAR_GP"
]

DB_FILE = "users.json"

# ====================================
# دیتابیس پیشفرض
# ====================================

DEFAULT_DATA = {
    "users": {},
    "plans": {
        "camel_1": [],
        "camel_2": [],
        "camel_3": [],
        "camel_4": []
    },
    "blocked": [],
    "daily_join": [],
    "last_day": str(datetime.date.today()),
    "language": {}
}

# ====================================
# ساخت دیتابیس
# ====================================

if not os.path.exists(DB_FILE):

    with open(DB_FILE, "w") as f:
        json.dump(DEFAULT_DATA, f, indent=4)

# ====================================
# توابع دیتابیس
# ====================================

def load_data():

    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
    except:
        data = DEFAULT_DATA.copy()

    if "language" not in data:
        data["language"] = {}

    today = str(datetime.date.today())

    if data.get("last_day") != today:
        data["daily_join"] = []
        data["last_day"] = today
        save_data(data)

    return data


def save_data(data):

    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ====================================
# بررسی عضویت
# ====================================

async def check_membership(user_id, bot):

    for channel in CHANNELS:

        try:

            member = await bot.get_chat_member(channel, user_id)

            if member.status not in [
                "member",
                "administrator",
                "creator"
            ]:
                return False

        except:
            return False

    return True

# ====================================
# پنل کاربر
# ====================================

def user_panel(is_admin=False):

    keyboard = [

        [KeyboardButton("👤 حساب کاربری")],

        [KeyboardButton("🪙 دریافت سکه رایگان")],

        [KeyboardButton("🐪 دریافت شتر رایگان")],

        [KeyboardButton("📩 خرید شتر اختصاصی")]

    ]

    if is_admin:

        keyboard.append(
            [KeyboardButton("⚙️ پنل مدیریت")]
        )

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

# ====================================
# پنل مدیریت
# ====================================

def admin_panel():

    keyboard = [

        [KeyboardButton("📊 آمار کاربران")],

        [KeyboardButton("📈 آمار روزانه")],

        [KeyboardButton("📋 لیست کاربران")],

        [KeyboardButton("📨 ارسال پیام به کاربر")],

        [KeyboardButton("📢 ارسال همگانی")],

        [KeyboardButton("⛔ بلاک کاربر")],

        [KeyboardButton("🛠 شارژ ربات")],

        [KeyboardButton("🔙 بازگشت")]

    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

# ====================================
# پنل شارژ
# ====================================

def charge_menu():

    keyboard = [

        [KeyboardButton("➕ شارژ پلن 1")],

        [KeyboardButton("➕ شارژ پلن 2")],

        [KeyboardButton("➕ شارژ پلن 3")],

        [KeyboardButton("➕ شارژ پلن 4")],

        [KeyboardButton("📦 موجودی پلن ها")],

        [KeyboardButton("🔙 بازگشت")]

    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

def back():
    return ReplyKeyboardMarkup([[KeyboardButton("🔙 بازگشت")]],resize_keyboard=True)

# ====================================
# انتخاب زبان
# ====================================

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [

        [KeyboardButton("فارسی")],

        [KeyboardButton("English")]

    ]

    await update.message.reply_text(
        "زبان مورد نظر را انتخاب کنید",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

# ====================================
# استارت
# ====================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()    

    user = update.effective_user

    data = load_data()

    users = data["users"]

    user_id = str(user.id)

    if user_id in data["blocked"]:
        await update.message.reply_text("❌ شما بلاک شده اید")
        return

    inviter = None

    if context.args:

        try:

            inviter = str(context.args[0])

            if inviter == user_id:
                inviter = None

        except:
            inviter = None

    if user_id not in users:

        users[user_id] = {
            "coins": 0,
            "joined": False,
            "invites": 0,
            "invited_by": inviter
        }

        data["daily_join"].append(user_id)

        save_data(data)

    joined = await check_membership(
        user.id,
        context.bot
    )

    if not joined:

        keyboard = [

            [
                InlineKeyboardButton(
                    "عضویت کانال 1",
                    url="https://t.me/Shotor_AR"
                )
            ],

            [
                InlineKeyboardButton(
                    "عضویت کانال 2",
                    url="https://t.me/shotorAR_GP"
                )
            ],

            [
                InlineKeyboardButton(
                    "✅ بررسی عضویت",
                    callback_data="check_join"
                )
            ]
        ]

        await update.message.reply_text(
            "❌ ابتدا در کانال ها عضو شوید.",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

        return

    users[user_id]["joined"] = True

    save_data(data)

    await update.message.reply_text(
        "خوش آمدید.",
        reply_markup=user_panel(
            user.id in ADMIN_ID
        )
    )

# ====================================
# بررسی عضویت
# ====================================

async def check_join_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user = query.from_user

    joined = await check_membership(
        user.id,
        context.bot
    )

    if not joined:

        await query.message.reply_text(
            "❌ هنوز عضو کانال ها نیستید."
        )

        return

    await query.message.reply_text(
        "✅ عضویت تایید شد.",
        reply_markup=user_panel(
            user.id in ADMIN_ID
        )
    )

# ====================================
# حذف لینک
# ====================================

async def delete_menu(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    keyboard=[

        [InlineKeyboardButton("یک سکه / 10mg(🐪استخونی)",callback_data="delete_camel_1")],
        [InlineKeyboardButton("سه سکه / 50mg(🐪نی قلیون)",callback_data="delete_camel_2")],
        [InlineKeyboardButton("پنج سکه / 80mg(🐪فیت)",callback_data="delete_camel_3")],
        [InlineKeyboardButton("ده سکه / 200mg(🐪توپر)",callback_data="delete_camel_4")]

    ]

    await query.message.reply_text(
        "پلن مورد نظر را انتخاب کنید",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def delete_plan(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    plan = query.data.replace("delete_","")

    data = load_data()

    links = data["plans"][plan]

    if not links:

        await query.message.reply_text("❌ این پلن خالی است")
        return

    msg=""

    for i,l in enumerate(links):
        msg+=f"{i+1} - {l}\n"

    msg+="\nشماره لینک مورد نظر برای حذف را ارسال کنید"

    context.user_data["delete_plan"]=plan

    await query.message.reply_text(msg)

# ====================================
# پیام ها
# ====================================

async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    user = update.effective_user

    user_id = str(user.id)

    data = load_data()

    users = data["users"]

    # شروع مجدد
    if text in ["شروع مجدد", "/start", "استارت"]:

        await start(update, context)

    # زبان فارسی
    elif text == "فارسی":

        data["language"][user_id] = "fa"

        save_data(data)

        await update.message.reply_text(
            "✅ زبان روی فارسی تنظیم شد",
            reply_markup=user_panel(
                user.id in ADMIN_ID
            )
        )

    # زبان انگلیسی
    elif text == "English":

        data["language"][user_id] = "en"

        save_data(data)

        await update.message.reply_text(
            "✅ Language changed to English",
            reply_markup=user_panel(
                user.id in ADMIN_ID
            )
        )

    elif text == "🔙 بازگشت":

        context.user_data.clear()

        await update.message.reply_text(
            "بازگشت",
            reply_markup=user_panel(
                user.id in ADMIN_ID
            )
        )

    elif text == "👤 حساب کاربری":

        info = users[user_id]

        await update.message.reply_text(
            f"""
👤 حساب کاربری

🆔 آیدی:
{user.id}

🪙 سکه:
{info['coins']}

👥 تعداد دعوت:
{info['invites']}
"""
        )

    elif text == "⚙️ پنل مدیریت":

        if user.id not in ADMIN_ID:
            return

        await update.message.reply_text(
            "⚙️ پنل مدیریت",
            reply_markup=admin_panel()
        )

    elif text == "📊 آمار کاربران":

        if user.id not in ADMIN_ID:
            return

        total_users = len(users)

        await update.message.reply_text(
            f"""
📊 آمار ربات

👥 تعداد کاربران:
{total_users}
"""
        )

    elif text == "📈 آمار روزانه":

        if user.id not in ADMIN_ID:
            return

        today = len(data["daily_join"])

        await update.message.reply_text(
            f"📊 کاربران امروز: {today}"
        )

    elif text == "📋 لیست کاربران":

        if user.id not in ADMIN_ID:
            return

        msg=""

        for u in users:
            msg+=u+"\n"

        await update.message.reply_text(msg[:4000])

    elif text == "⛔ بلاک کاربر":

        if user.id not in ADMIN_ID:
            return

        context.user_data["block"]=True

        await update.message.reply_text(
            "آیدی کاربر را ارسال کنید",
            reply_markup=back()
        )

    elif context.user_data.get("block"):

        data["blocked"].append(text)

        save_data(data)

        context.user_data.clear()

        await update.message.reply_text(
            "✅ کاربر بلاک شد",
            reply_markup=admin_panel()
        )

    elif text == "📢 ارسال همگانی":

        if user.id not in ADMIN_ID:
            return

        context.user_data["broadcast"]=True

        await update.message.reply_text(
            "📨 پیام همگانی را ارسال کنید."
        )

    elif context.user_data.get("broadcast"):

        sent=0
        failed=0

        for uid in users:

            try:
                await context.bot.send_message(int(uid),text)
                sent+=1
            except:
                failed+=1

        context.user_data["broadcast"]=False

        await update.message.reply_text(
            f"""
✅ ارسال انجام شد.

✔️ موفق:
{sent}

❌ ناموفق:
{failed}
"""
        )

    elif text == "🛠 شارژ ربات":

        await update.message.reply_text(
            "مدیریت پلن ها",
            reply_markup=charge_menu()
        )

    elif "➕ شارژ پلن" in text:

        if user.id not in ADMIN_ID:
            return

        plan_number = text[-1]

        context.user_data["waiting_plan"] = f"camel_{plan_number}"

        await update.message.reply_text(
            """
🔗 لینک ها را ارسال کنید.

هر لینک در یک خط.
"""
        )

    elif context.user_data.get("waiting_plan"):

        plan = context.user_data["waiting_plan"]

        links = text.split("\n")

        data["plans"][plan].extend(links)

        save_data(data)

        del context.user_data["waiting_plan"]

        await update.message.reply_text(
            "✅ لینک ها ذخیره شدند."
        )

    elif text == "📦 موجودی پلن ها":

        msg=""

        for p,links in data["plans"].items():

            msg+=f"\n{p}\n"

            if not links:
                msg+="خالی\n"
            else:
                for i,l in enumerate(links):
                    msg+=f"{i+1}- {l}\n"

        keyboard=[[InlineKeyboardButton("🗑 حذف لینک",callback_data="del")]]

        await update.message.reply_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif context.user_data.get("delete_plan"):

        plan=context.user_data["delete_plan"]

        try:

            index=int(text)-1

            removed=data["plans"][plan].pop(index)

            save_data(data)

            context.user_data.clear()

            await update.message.reply_text(
                f"✅ لینک حذف شد\n{removed}"
            )

        except:

            await update.message.reply_text(
                "❌ شماره نامعتبر است"
            )

# ====================================
# تنظیم منوی تلگرام
# ====================================

async def set_menu(app):

    await app.bot.set_my_commands([
        ("start", "شروع مجدد"),
        ("language", "تغییر زبان")
    ])

# ====================================
# main
# ====================================

def main():

    app = Application.builder().token(
        TOKEN
    ).build()

    # تنظیم منوی تلگرام
    app.post_init = set_menu

    # دستورات
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "language",
            language_command
        )
    )

    # کال‌بک‌ها
    app.add_handler(
        CallbackQueryHandler(
            check_join_callback,
            pattern="check_join"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            delete_menu,
            pattern="del"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            delete_plan,
            pattern="delete_camel_"
        )
    )

    # پیام ها
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            messages
        )
    )

    print("Bot Running...")

    app.run_polling()

# ====================================
# اجرا
# ====================================

if __name__ == "__main__":

    main()
