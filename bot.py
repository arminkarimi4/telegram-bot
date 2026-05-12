import json
import os

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
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
    }
}

# ====================================
# ساخت دیتابیس
# ====================================

if not os.path.exists(DB_FILE):

    with open(DB_FILE, "w") as f:
        json.dump(
            DEFAULT_DATA,
            f,
            indent=4
        )

# ====================================
# توابع دیتابیس
# ====================================

def load_data():

    try:

        with open(DB_FILE, "r") as f:
            return json.load(f)

    except:

        return DEFAULT_DATA.copy()

def save_data(data):

    with open(DB_FILE, "w") as f:
        json.dump(
            data,
            f,
            indent=4
        )

# ====================================
# بررسی عضویت
# ====================================

async def check_membership(user_id, bot):

    for channel in CHANNELS:

        try:

            member = await bot.get_chat_member(
                channel,
                user_id
            )

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

        [KeyboardButton("📢 ارسال همگانی")],

        [KeyboardButton("➕ شارژ پلن 1")],

        [KeyboardButton("➕ شارژ پلن 2")],

        [KeyboardButton("➕ شارژ پلن 3")],

        [KeyboardButton("➕ شارژ پلن 4")],

        [KeyboardButton("📦 موجودی پلن ها")]
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

# ====================================
# استارت
# ====================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    data = load_data()

    users = data["users"]

    user_id = str(user.id)

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

    inviter_id = users[user_id]["invited_by"]

    if inviter_id and inviter_id in users:

        if not users[user_id].get("rewarded"):

            users[inviter_id]["coins"] += 1
            users[inviter_id]["invites"] += 1

            users[user_id]["rewarded"] = True

            try:

                await context.bot.send_message(
                    chat_id=int(inviter_id),
                    text="""
🎉 یک نفر با لینک شما عضو شد.

✅ 1 سکه دریافت کردید.
"""
                )

            except:
                pass

    save_data(data)

    await update.message.reply_text(
        "✅ خوش آمدید.",
        reply_markup=user_panel(
            user.id in ADMIN_ID
        )
    )

# ====================================
# بررسی عضویت دکمه
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

    data = load_data()

    users = data["users"]

    user_id = str(user.id)

    users[user_id]["joined"] = True

    inviter_id = users[user_id]["invited_by"]

    if inviter_id and inviter_id in users:

        if not users[user_id].get("rewarded"):

            users[inviter_id]["coins"] += 1
            users[inviter_id]["invites"] += 1

            users[user_id]["rewarded"] = True

    save_data(data)

    await query.message.reply_text(
        "✅ عضویت تایید شد.",
        reply_markup=user_panel(
            user.id in ADMIN_ID
        )
    )

# ====================================
# خرید پلن
# ====================================

async def buy_plan(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user = query.from_user

    user_id = str(user.id)

    data = load_data()

    users = data["users"]

    plan = query.data

    prices = {
        "buy_camel_1": 1,
        "buy_camel_2": 3,
        "buy_camel_3": 5,
        "buy_camel_4": 10
    }

    plan_map = {
        "buy_camel_1": "camel_1",
        "buy_camel_2": "camel_2",
        "buy_camel_3": "camel_3",
        "buy_camel_4": "camel_4"
    }

    if users[user_id]["coins"] < prices[plan]:

        await query.message.reply_text(
            "❌ سکه کافی ندارید."
        )

        return

    db_plan = plan_map[plan]

    if len(data["plans"][db_plan]) <= 0:

        await query.message.reply_text(
            "❌ موجودی این پلن تمام شده."
        )

        return

    users[user_id]["coins"] -= prices[plan]

    config = data["plans"][db_plan].pop(0)

    save_data(data)

    await query.message.reply_text(
        f"""
✅ خرید با موفقیت انجام شد.

🔗 کانفیگ شما:

{config}
"""
    )

# ====================================
# پیام ها
# ====================================

async def messages(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text

    user = update.effective_user

    user_id = str(user.id)

    data = load_data()

    users = data["users"]

    # =========================
    # حساب کاربری
    # =========================

    if text == "👤 حساب کاربری":

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

    # =========================
    # دریافت سکه رایگان
    # =========================

    elif text == "🪙 دریافت سکه رایگان":

        bot_username = (
            await context.bot.get_me()
        ).username

        invite_link = (
            f"https://t.me/{bot_username}"
            f"?start={user.id}"
        )

        keyboard = [

            [
                InlineKeyboardButton(
                    "📨 اشتراک گذاری لینک",
                    url=f"https://t.me/share/url?url={invite_link}"
                )
            ]
        ]

        await update.message.reply_text(
            f"""
🪙 دریافت سکه رایگان

✅ با دعوت هر نفر:
1 سکه رایگان دریافت می‌کنید.

🔗 لینک اختصاصی شما:

{invite_link}
""",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

    # =========================
    # دریافت شتر رایگان
    # =========================

    elif text == "🐪 دریافت شتر رایگان":

        keyboard = [

            [
                InlineKeyboardButton(
                    "یک سکه / 10mg(🐪استخونی)",
                    callback_data="buy_camel_1"
                )
            ],

            [
                InlineKeyboardButton(
                    "سه سکه / 50mg(🐪نی قلیون)",
                    callback_data="buy_camel_2"
                )
            ],

            [
                InlineKeyboardButton(
                    "پنج سکه / 80mg(🐪فیت)",
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
            "🐪 یکی از پلن ها را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

    # =========================
    # خرید اختصاصی
    # =========================

    elif text == "📩 خرید شتر اختصاصی":

        await update.message.reply_text(
            """
📩 برای خرید شتر اختصاصی
به آیدی زیر پیام دهید:

@YOUR_ID
"""
        )

    # =========================
    # پنل مدیریت
    # =========================

    elif text == "⚙️ پنل مدیریت":

        if user.id not in ADMIN_ID:

            return

        await update.message.reply_text(
            "⚙️ پنل مدیریت",
            reply_markup=admin_panel()
        )

    # =========================
    # آمار کاربران
    # =========================

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

    # =========================
    # موجودی پلن ها
    # =========================

    elif text == "📦 موجودی پلن ها":

        if user.id not in ADMIN_ID:

            return

        text_msg = f"""
📦 موجودی پلن ها

پلن 1:
{len(data['plans']['camel_1'])}

پلن 2:
{len(data['plans']['camel_2'])}

پلن 3:
{len(data['plans']['camel_3'])}

پلن 4:
{len(data['plans']['camel_4'])}
"""

        await update.message.reply_text(
            text_msg
        )

    # =========================
    # شارژ پلن ها
    # =========================

    elif text.startswith("➕ شارژ پلن"):

        if user.id not in ADMIN_ID:

            return

        plan_number = text[-1]

        context.user_data["waiting_plan"] = (
            f"camel_{plan_number}"
        )

        await update.message.reply_text(
            """
🔗 لینک ها را ارسال کنید.

هر لینک در یک خط.
"""
        )

    # =========================
    # ذخیره لینک ها
    # =========================

    elif "waiting_plan" in context.user_data:

        if user.id not in ADMIN_ID:

            return

        plan = context.user_data["waiting_plan"]

        links = text.split("\n")

        data["plans"][plan].extend(links)

        save_data(data)

        del context.user_data["waiting_plan"]

        await update.message.reply_text(
            "✅ لینک ها ذخیره شدند."
        )

    # =========================
    # ارسال همگانی
    # =========================

    elif text == "📢 ارسال همگانی":

        if user.id not in ADMIN_ID:

            return

        context.user_data["broadcast"] = True

        await update.message.reply_text(
            "📨 پیام همگانی را ارسال کنید."
        )

    # =========================
    # انجام ارسال همگانی
    # =========================

    elif context.user_data.get("broadcast"):

        if user.id not in ADMIN_ID:

            return

        sent = 0

        failed = 0

        for uid in users:

            try:

                await context.bot.send_message(
                    chat_id=int(uid),
                    text=text
                )

                sent += 1

            except:

                failed += 1

        context.user_data["broadcast"] = False

        await update.message.reply_text(
            f"""
✅ ارسال انجام شد.

✔️ موفق:
{sent}

❌ ناموفق:
{failed}
"""
        )

# ====================================
# main
# ====================================

def main():

    app = Application.builder().token(
        TOKEN
    ).build()

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
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
            pattern="buy_camel_"
        )
    )

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
