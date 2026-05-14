# =========================
# ULTRA SECURE TELEGRAM BOT
# Python Telegram Bot v20+
# =========================

import json
import os
import time
import datetime
import logging

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
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
# CONFIG
# =========================

TOKEN = "8720876053:AAEm9TwoD4c8-ndZLAixw7KMBNaPTdF5Eys"

ADMINS = [400900388, 1483857146]

CHANNELS = [
    "@Shotor_AR",
    "@shotorAR_GP"
]

SUPPORT_ID = "@arminkarimi4"

DB_FILE = "database.json"

PLAN_PRICE = {
    "camel_1": 1,
    "camel_2": 3,
    "camel_3": 5,
    "camel_4": 10
}

BUY_COOLDOWN = 15
INVITE_REWARD = 1

# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# =========================
# DEFAULT DATABASE
# =========================

DEFAULT_DB = {
    "users": {},
    "blocked": [],
    "plans": {
        "camel_1": [],
        "camel_2": [],
        "camel_3": [],
        "camel_4": []
    },
    "daily_users": [],
    "last_day": str(datetime.date.today())
}

# =========================
# CREATE DATABASE
# =========================

if not os.path.exists(DB_FILE):

    with open(DB_FILE, "w", encoding="utf-8") as f:

        json.dump(
            DEFAULT_DB,
            f,
            indent=4,
            ensure_ascii=False
        )

# =========================
# DATABASE
# =========================

def load_db():

    try:

        with open(DB_FILE, "r", encoding="utf-8") as f:

            data = json.load(f)

    except:

        data = DEFAULT_DB.copy()

    today = str(datetime.date.today())

    if data.get("last_day") != today:

        data["daily_users"] = []
        data["last_day"] = today

        save_db(data)

    return data

def save_db(data):

    with open(DB_FILE, "w", encoding="utf-8") as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )

# =========================
# USER DEFAULT
# =========================

def create_user(inviter=None):

    return {
        "coins": 0,
        "invites": 0,
        "joined": str(datetime.date.today()),
        "invited_by": inviter,
        "last_buy": 0
    }

# =========================
# MEMBERSHIP CHECK
# =========================

async def check_join(user_id, bot):

    for ch in CHANNELS:

        try:

            member = await bot.get_chat_member(
                ch,
                user_id
            )

            if member.status not in [
                "member",
                "administrator",
                "creator"
            ]:
                return False

        except Exception as e:

            print("JOIN ERROR:", e)

            return False

    return True

# =========================
# FORCE JOIN
# =========================

async def force_join(update, context):

    joined = await check_join(
        update.effective_user.id,
        context.bot
    )

    if joined:
        return True

    keyboard = [

        [
            InlineKeyboardButton(
                "عضویت کانال",
                url="https://t.me/Shotor_AR"
            )
        ],

        [
            InlineKeyboardButton(
                "عضویت گروه",
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

    await update.effective_message.reply_text(
        "❌ ابتدا عضو کانال ها شوید",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return False

# =========================
# MENUS
# =========================

def user_menu(admin=False):

    keyboard = [

        [KeyboardButton("👤 حساب من")],

        [KeyboardButton("🪙 دریافت سکه رایگان")],

        [KeyboardButton("🐪 دریافت شتر رایگان")],

        [KeyboardButton("🛒 خرید شتر اختصاصی")],

        [KeyboardButton("🆘 پشتیبانی")]
    ]

    if admin:

        keyboard.append(
            [KeyboardButton("⚙️ پنل مدیریت")]
        )

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

def admin_menu():

    keyboard = [

        [
            KeyboardButton("📊 آمار کاربران"),
            KeyboardButton("📈 آمار روزانه")
        ],

        [
            KeyboardButton("📋 لیست کاربران")
        ],

        [
            KeyboardButton("📨 پیام به کاربر"),
            KeyboardButton("📢 ارسال همگانی")
        ],

        [
            KeyboardButton("⛔ بلاک کاربر"),
            KeyboardButton("✅ آنبلاک کاربر")
        ],

        [
            KeyboardButton("🛠 مدیریت پلن ها")
        ],

        [
            KeyboardButton("🔄 ریست وضعیت")
        ],

        [
            KeyboardButton("🔙 بازگشت")
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

def plans_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "➕ شارژ پلن 1",
                callback_data="add_plan1"
            ),

            InlineKeyboardButton(
                "🗑 حذف پلن 1",
                callback_data="clear_plan1"
            )
        ],

        [
            InlineKeyboardButton(
                "➕ شارژ پلن 2",
                callback_data="add_plan2"
            ),

            InlineKeyboardButton(
                "🗑 حذف پلن 2",
                callback_data="clear_plan2"
            )
        ],

        [
            InlineKeyboardButton(
                "➕ شارژ پلن 3",
                callback_data="add_plan3"
            ),

            InlineKeyboardButton(
                "🗑 حذف پلن 3",
                callback_data="clear_plan3"
            )
        ],

        [
            InlineKeyboardButton(
                "➕ شارژ پلن 4",
                callback_data="add_plan4"
            ),

            InlineKeyboardButton(
                "🗑 حذف پلن 4",
                callback_data="clear_plan4"
            )
        ],

        [
            InlineKeyboardButton(
                "📦 موجودی پلن ها",
                callback_data="stock"
            )
        ],

        [
            InlineKeyboardButton(
                "🗑 حذف لینک خراب",
                callback_data="delete_bad"
            )
        ],

        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="back_admin"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)

def back_menu():

    return ReplyKeyboardMarkup(
        [[KeyboardButton("❌ لغو عملیات")]],
        resize_keyboard=True
    )

# =========================
# COMMANDS
# =========================

async def set_commands(app):

    commands = [

        BotCommand("start", "شروع ربات"),

        BotCommand("panel", "پنل مدیریت"),

        BotCommand("restart", "ریست وضعیت")
    ]

    await app.bot.set_my_commands(commands)

# =========================
# START
# =========================

async def start(update: Update,
                context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    user = update.effective_user

    uid = str(user.id)

    db = load_db()

    if uid in db["blocked"]:

        await update.message.reply_text(
            "❌ شما بلاک شده اید"
        )

        return

    inviter = None

    if context.args:

        inviter = str(context.args[0])

    # جلوگیری از self invite
    if inviter == uid:

        inviter = None

    # ساخت کاربر
    if uid not in db["users"]:

        db["users"][uid] = create_user()

        db["daily_users"].append(uid)

        # پاداش دعوت
        if (
            inviter
            and inviter in db["users"]
            and inviter != uid
        ):

            db["users"][uid]["invited_by"] = inviter

            db["users"][inviter]["coins"] += INVITE_REWARD

            db["users"][inviter]["invites"] += 1

            try:

                await context.bot.send_message(
                    inviter,
                    f"🎉 کاربر جدید عضو شد\n✅ {INVITE_REWARD} سکه دریافت کردید"
                )

            except:
                pass

        save_db(db)

    # عضویت اجباری
    if not await force_join(update, context):
        return

    await update.message.reply_text(
        f"خوش آمدید {user.first_name}",
        reply_markup=user_menu(user.id in ADMINS)
    )

# =========================
# CHECK JOIN
# =========================

async def check_join_callback(update: Update,
                              context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    joined = await check_join(
        query.from_user.id,
        context.bot
    )

    if not joined:

        await query.message.reply_text(
            "❌ هنوز عضو نشده اید"
        )

        return

    await query.message.reply_text(
        "✅ عضویت تایید شد",
        reply_markup=user_menu(
            query.from_user.id in ADMINS
        )
    )

# =========================
# BUY MENU
# =========================

async def buy_menu(update, context):

    keyboard = [

        [
            InlineKeyboardButton(
                "یک سکه / 15MB(🐪استخونی)",
                callback_data="buy_camel_1"
            )
        ],

        [
            InlineKeyboardButton(
                "سه سکه / 50MB(🐪نی قلیون)",
                callback_data="buy_camel_2"
            )
        ],

        [
            InlineKeyboardButton(
                "پنج سکه / 80MB(🐪فیت)",
                callback_data="buy_camel_3"
            )
        ],

        [
            InlineKeyboardButton(
                "ده سکه / 200mg(🐪توپر)",
                callback_data="buy_camel_4"
            )
        ]
    ]

    await update.message.reply_text(
        "پلن موردنظر را انتخاب کنید",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# BUY PLAN
# =========================

async def buy_plan(update: Update,
                   context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    uid = str(query.from_user.id)

    db = load_db()

    # چک بلاک
    if uid in db["blocked"]:

        return

    # چک عضویت
    joined = await check_join(
        query.from_user.id,
        context.bot
    )

    if not joined:

        await query.message.reply_text(
            "❌ ابتدا عضو کانال ها شوید"
        )

        return

    if uid not in db["users"]:

        return

    plan = query.data.replace("buy_", "")

    if plan not in db["plans"]:

        await query.message.reply_text(
            "❌ پلن نامعتبر"
        )

        return

    user = db["users"][uid]

    # cooldown
    now = time.time()

    if now - user.get("last_buy", 0) < BUY_COOLDOWN:

        await query.message.reply_text(
            f"⏳ لطفا {BUY_COOLDOWN} ثانیه صبر کنید"
        )

        return

    price = PLAN_PRICE[plan]

    if user["coins"] < price:

        await query.message.reply_text(
            "❌ سکه کافی ندارید"
        )

        return

    if len(db["plans"][plan]) == 0:

        await query.message.reply_text(
            "❌ موجودی این پلن تمام شده"
        )

        return

    config = db["plans"][plan].pop(0)

    user["coins"] -= price

    user["last_buy"] = now

    save_db(db)

    await query.message.reply_text(
        f"✅ خرید موفق\n\n{config}"
    )

# =========================
# TEXT HANDLER
# =========================

async def messages(update: Update,
                   context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    user = update.effective_user

    uid = str(user.id)

    db = load_db()

    users = db["users"]

    # بلاک
    if uid in db["blocked"]:

        return

    # وجود کاربر
    if uid not in users:

        return

    # عضویت اجباری
    if not await force_join(update, context):

        return

    # =====================
    # CANCEL
    # =====================

    if text == "❌ لغو عملیات":

        context.user_data.clear()

        await update.message.reply_text(
            "✅ عملیات لغو شد",
            reply_markup=user_menu(
                user.id in ADMINS
            )
        )

        return

    # =====================
    # BACK
    # =====================

    if text == "🔙 بازگشت":

        context.user_data.clear()

        await update.message.reply_text(
            "✅ بازگشت",
            reply_markup=user_menu(
                user.id in ADMINS
            )
        )

        return

    # =====================
    # ACCOUNT
    # =====================

    if text == "👤 حساب من":

        data = users[uid]

        bot_username = (
            await context.bot.get_me()
        ).username

        invite_link = (
            f"https://t.me/{bot_username}?start={uid}"
        )

        await update.message.reply_text(

            f"👤 اطلاعات حساب\n\n"

            f"🆔 آیدی: {uid}\n"

            f"🪙 سکه: {data['coins']}\n"

            f"👥 دعوت ها: {data['invites']}\n\n"

            f"🔗 لینک دعوت:\n{invite_link}"
        )

    # =====================
    # FREE COIN
    # =====================

    elif text == "🪙 دریافت سکه رایگان":

        bot_username = (
            await context.bot.get_me()
        ).username

        link = (
            f"https://t.me/{bot_username}?start={uid}"
        )

        await update.message.reply_text(

            "✅ با دعوت هر نفر سکه بگیر\n\n"

            f"{link}"
        )

    # =====================
    # BUY
    # =====================

    elif text == "🐪 دریافت شتر رایگان":

        await buy_menu(update, context)

    # =====================
    # SUPPORT
    # =====================

    elif text == "🛒 خرید شتر اختصاصی":

        keyboard = [[

            InlineKeyboardButton(
                "ارتباط با پشتیبانی",
                url=f"https://t.me/{SUPPORT_ID.replace('@','')}"
            )
        ]]

        await update.message.reply_text(
            "برای خرید اختصاصی کلیک کنید",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif text == "🆘 پشتیبانی":

        keyboard = [[

            InlineKeyboardButton(
                "پشتیبانی",
                url=f"https://t.me/{SUPPORT_ID.replace('@','')}"
            )
        ]]

        await update.message.reply_text(
            "ارتباط با پشتیبانی",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =====================
    # ADMIN PANEL
    # =====================

    elif text == "⚙️ پنل مدیریت":

        if user.id not in ADMINS:
            return

        await update.message.reply_text(
            "⚙️ پنل مدیریت",
            reply_markup=admin_menu()
        )

    # =====================
    # STATS
    # =====================

    elif text == "📊 آمار کاربران":

        if user.id not in ADMINS:
            return

        await update.message.reply_text(
            f"👥 تعداد کل کاربران: {len(users)}"
        )

    elif text == "📈 آمار روزانه":

        if user.id not in ADMINS:
            return

        await update.message.reply_text(
            f"📈 کاربران امروز: {len(db['daily_users'])}"
        )

    # =====================
    # USERS LIST
    # =====================

    elif text == "📋 لیست کاربران":

        if user.id not in ADMINS:
            return

        msg = "\n".join(users.keys())

        if not msg:

            msg = "لیست خالی است"

        await update.message.reply_text(
            msg[:4000]
        )

    # =====================
    # BROADCAST
    # =====================

    elif text == "📢 ارسال همگانی":

        if user.id not in ADMINS:
            return

        context.user_data.clear()

        context.user_data["broadcast"] = True

        await update.message.reply_text(
            "پیام را ارسال کنید",
            reply_markup=back_menu()
        )

    elif context.user_data.get("broadcast"):

        sent = 0

        for u in users:

            try:

                await context.bot.send_message(
                    chat_id=int(u),
                    text=text
                )

                sent += 1

            except:
                pass

        context.user_data.clear()

        await update.message.reply_text(
            f"✅ برای {sent} نفر ارسال شد",
            reply_markup=admin_menu()
        )

    # =====================
    # PM
    # =====================

    elif text == "📨 پیام به کاربر":

        if user.id not in ADMINS:
            return

        context.user_data.clear()

        context.user_data["pm_user"] = True

        await update.message.reply_text(
            "آیدی عددی کاربر را ارسال کنید",
            reply_markup=back_menu()
        )

    elif context.user_data.get("pm_user"):

        if not text.isdigit():

            await update.message.reply_text(
                "❌ آیدی نامعتبر"
            )

            return

        context.user_data["target_user"] = text

        context.user_data["pm_user"] = False

        context.user_data["pm_text"] = True

        await update.message.reply_text(
            "متن پیام را ارسال کنید"
        )

    elif context.user_data.get("pm_text"):

        try:

            await context.bot.send_message(
                int(context.user_data["target_user"]),
                text
            )

            await update.message.reply_text(
                "✅ پیام ارسال شد",
                reply_markup=admin_menu()
            )

        except:

            await update.message.reply_text(
                "❌ خطا در ارسال"
            )

        context.user_data.clear()

    # =====================
    # BLOCK
    # =====================

    elif text == "⛔ بلاک کاربر":

        if user.id not in ADMINS:
            return

        context.user_data["block"] = True

        await update.message.reply_text(
            "آیدی کاربر را ارسال کنید",
            reply_markup=back_menu()
        )

    elif context.user_data.get("block"):

        if text not in db["blocked"]:

            db["blocked"].append(text)

            save_db(db)

        context.user_data.clear()

        await update.message.reply_text(
            "✅ بلاک شد",
            reply_markup=admin_menu()
        )

    # =====================
    # UNBLOCK
    # =====================

    elif text == "✅ آنبلاک کاربر":

        if user.id not in ADMINS:
            return

        context.user_data["unblock"] = True

        await update.message.reply_text(
            "آیدی را ارسال کنید",
            reply_markup=back_menu()
        )

    elif context.user_data.get("unblock"):

        if text in db["blocked"]:

            db["blocked"].remove(text)

            save_db(db)

        context.user_data.clear()

        await update.message.reply_text(
            "✅ آنبلاک شد",
            reply_markup=admin_menu()
        )

    # =====================
    # PLAN MANAGEMENT
    # =====================

    elif text == "🛠 مدیریت پلن ها":

        if user.id not in ADMINS:
            return

        await update.message.reply_text(
            "مدیریت پلن ها",
            reply_markup=plans_menu()
        )

    # =====================
    # ADD PLAN
    # =====================

    elif context.user_data.get("add_plan"):

        plan = context.user_data["add_plan"]

        links = [

            i.strip()

            for i in text.split("\n")

            if i.strip().startswith(
                (
                    "vless://",
                    "vmess://",
                    "trojan://"
                )
            )
        ]

        unique_links = list(set(links))

        db["plans"][plan].extend(unique_links)

        save_db(db)

        context.user_data.clear()

        await update.message.reply_text(
            f"✅ {len(unique_links)} کانفیگ ذخیره شد",
            reply_markup=plans_menu()
        )

    # =====================
    # DELETE BAD LINK
    # =====================

    elif context.user_data.get("delete_link"):

        deleted = False

        for plan in db["plans"]:

            if text in db["plans"][plan]:

                db["plans"][plan].remove(text)

                deleted = True

        save_db(db)

        context.user_data.clear()

        if deleted:

            await update.message.reply_text(
                "✅ حذف شد",
                reply_markup=plans_menu()
            )

        else:

            await update.message.reply_text(
                "❌ پیدا نشد",
                reply_markup=plans_menu()
            )

    # =====================
    # RESET
    # =====================

    elif text == "🔄 ریست وضعیت":

        context.user_data.clear()

        await update.message.reply_text(
            "✅ وضعیت ریست شد",
            reply_markup=admin_menu()
        )

# =========================
# CALLBACKS
# =========================

async def plans_callback(update: Update,
                         context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    data = query.data

    db = load_db()

    if query.from_user.id not in ADMINS:
        return

    # BACK
    if data == "back_admin":

        await query.message.reply_text(
            "⚙️ پنل مدیریت",
            reply_markup=admin_menu()
        )

    # STOCK
    elif data == "stock":

        msg = "📦 موجودی پلن ها\n\n"

        for p in db["plans"]:

            msg += (
                f"{p} : "
                f"{len(db['plans'][p])}\n"
            )

        await query.message.reply_text(msg)

    # DELETE BAD
    elif data == "delete_bad":

        context.user_data.clear()

        context.user_data["delete_link"] = True

        await query.message.reply_text(
            "لینک خراب را ارسال کنید",
            reply_markup=back_menu()
        )

    # ADD PLAN
    elif data.startswith("add_plan"):

        number = data[-1]

        context.user_data.clear()

        context.user_data["add_plan"] = (
            f"camel_{number}"
        )

        await query.message.reply_text(
            "لینک ها را ارسال کنید",
            reply_markup=back_menu()
        )

    # CLEAR PLAN
    elif data.startswith("clear_plan"):

        number = data[-1]

        db["plans"][f"camel_{number}"] = []

        save_db(db)

        await query.message.reply_text(
            f"✅ پلن {number} پاک شد",
            reply_markup=plans_menu()
        )

# =========================
# RESTART
# =========================

async def restart(update: Update,
                  context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    await update.message.reply_text(
        "✅ وضعیت شما ریست شد",
        reply_markup=user_menu(
            update.effective_user.id in ADMINS
        )
    )

# =========================
# PANEL
# =========================

async def panel(update: Update,
                context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id not in ADMINS:
        return

    await update.message.reply_text(
        "⚙️ پنل مدیریت",
        reply_markup=admin_menu()
    )

# =========================
# ERROR
# =========================

async def error_handler(update, context):

    print("ERROR:", context.error)

# =========================
# MAIN
# =========================

def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("restart", restart)
    )

    app.add_handler(
        CommandHandler("panel", panel)
    )

    app.add_handler(
        CallbackQueryHandler(
            check_join_callback,
            pattern="check_join"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            buy_plan,
            pattern="buy_"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            plans_callback,
            pattern="^(add_plan|clear_plan|stock|delete_bad|back_admin)"
        )
    )

    app.add_handler(

        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            messages
        )
    )

    app.add_error_handler(
        error_handler
    )

    app.post_init = set_commands

    print("BOT RUNNING...")

    app.run_polling()

# =========================
# RUN
# =========================

if __name__ == "__main__":

    main()
