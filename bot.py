from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import sqlite3

from config import (
    TOKEN,
    ADMINS,
    REFERRAL_REWARD,
)

from db import (
    get_connection,
    init_db,
)

from utils import (
    is_admin,
    build_join_keyboard,
    is_user_member,
    is_spam,
    clear_spam
)


# =========================================
# منوی اصلی
# =========================================

def main_menu(user_id=None):

    keyboard = [
        ["💼 حساب من"],
        ["🎁 دریافت سکه رایگان"],
        ["🐪 دریافت شتر رایگان"],
        ["🐪 خرید شتر اختصاصی"],
        ["📨 پشتیبانی"],
    ]

    if user_id in ADMINS:
        keyboard.append(["⚙️ پنل مدیریت"])

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

# =========================================
# پیام عضویت اجباری
# =========================================
async def join_required_message(update, context):

    text = (
        "❌ برای استفاده از ربات باید ابتدا "
        "در کانال‌ها/گروه‌های زیر عضو شوی."
    )

    if update.message:

        await update.message.reply_text(
            text,
            reply_markup=build_join_keyboard()
        )

    elif update.callback_query:

        await update.callback_query.message.edit_text(
            text,
            reply_markup=build_join_keyboard()
        )


#===============================
#تابع پرداخت پاداش
#================================

async def process_referral_reward(invited_id, context):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT invited_by, referral_rewarded FROM users WHERE user_id=?",
        (invited_id,)
    )

    user = cur.fetchone()

    if not user:
        conn.close()
        return

    inviter_id = user["invited_by"]
    rewarded = user["referral_rewarded"]

    if inviter_id and rewarded == 0:

        cur.execute("""
        UPDATE users
        SET coins = coins + ?, invites = invites + 1
        WHERE user_id=?
        """, (REFERRAL_REWARD, inviter_id))

        cur.execute("""
        UPDATE users
        SET referral_rewarded = 1
        WHERE user_id=?
        """, (invited_id,))

        conn.commit()

        try:
            await context.bot.send_message(
                inviter_id,
                f"🎉 یک نفر با لینک شما عضو شد و {REFERRAL_REWARD} سکه گرفتید."
            )
        except:
            pass

    conn.close()


# =========================================
# بررسی عضویت
# =========================================
async def check_membership_callback(update, context):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if not await is_user_member(context.bot, user_id):
        await query.message.edit_text(
            "❌ هنوز عضو همه کانال‌ها نیستی.",
            reply_markup=build_join_keyboard()
        )
        return

    # --- بخش جدید: واریز پاداش در لحظه تایید عضویت ---
    await process_referral_reward(user_id, context)
    # -----------------------------------------------

    clear_spam(context, user_id)

    await query.message.edit_text(
        "✅ عضویت شما تایید شد."
    )


# =========================================
# ثبت کاربر
# =========================================
async def register_user(
    user_id,
    username,
    invited_by=None,
    bot=None
):
    conn = get_connection()
    cur = conn.cursor()

    # بررسی اینکه کاربر قبلاً وجود دارد یا نه
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    exists = cur.fetchone()

    if not exists:
        # ثبت کاربر جدید
        cur.execute("""
        INSERT INTO users(
            user_id,
            username,
            invited_by
        )
        VALUES(?,?,?)
        """, (user_id, username, invited_by))

        # =========================
        # ثبت رفرال (بدون دادن سکه)
        # =========================
        if invited_by and invited_by != user_id:
            cur.execute("SELECT user_id FROM users WHERE user_id=?", (invited_by,))
            inviter = cur.fetchone()

            if inviter:
                cur.execute("""
                INSERT OR IGNORE INTO referrals(
                    inviter_id,
                    invited_id
                )
                VALUES(?,?)
                """, (invited_by, user_id))

        conn.commit()

    conn.close()


# =========================================
# گرفتن کاربر
# =========================================
def get_user(user_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user_id,)
    )

    user = cur.fetchone()

    conn.close()

    return user


# =========================================
# گرفتن آمار
# =========================================
def get_stats():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM referrals")
    refs = cur.fetchone()[0]

    cur.execute("""
    SELECT COUNT(*) FROM inventory
    WHERE is_used=0
    """)

    stock = cur.fetchone()[0]

    conn.close()

    return users, refs, stock


# =========================================
# دریافت پلن
# =========================================
def claim_plan(user_id, plan_id):

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("BEGIN IMMEDIATE")

        cur.execute(
            "SELECT * FROM users WHERE user_id=?",
            (user_id,)
        )

        user = cur.fetchone()

        if user["is_blocked"] == 1:
            return False, "اکانت شما بلاک شده"

        cur.execute(
            "SELECT * FROM plans WHERE id=?",
            (plan_id,)
        )

        plan = cur.fetchone()

        if not plan:
            return False, "پلن یافت نشد"

        if user["coins"] < plan["price"]:
            return False, "سکه کافی نداری"

        cur.execute("""
        SELECT * FROM inventory
        WHERE
            plan_id=?
            AND is_used=0
        LIMIT 1
        """, (plan_id,))

        config = cur.fetchone()

        if not config:
            return False, "موجودی تمام شده"

        # کم کردن سکه
        cur.execute("""
        UPDATE users
        SET coins=coins-?
        WHERE user_id=?
        """, (
            plan["price"],
            user_id
        ))

        # استفاده کانفیگ
        cur.execute("""
        UPDATE inventory
        SET
            is_used=1,
            used_by=?,
            used_at=CURRENT_TIMESTAMP
        WHERE id=?
        """, (
            user_id,
            config["id"]
        ))

        # ثبت claim
        cur.execute("""
        INSERT INTO claims(
            user_id,
            plan_id,
            config_id
        )
        VALUES(?,?,?)
        """, (
            user_id,
            plan_id,
            config["id"]
        ))

        conn.commit()

        return True, config["config"]

    except Exception as e:

        conn.rollback()

        return False, str(e)

    finally:

        conn.close()


# =========================================
# START
# =========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    user_id = user.id
    username = user.username or ""

    invited_by = None

    if context.args:

        try:
            invited_by = int(context.args[0])

            if invited_by == user_id:
                invited_by = None

        except:
            invited_by = None

    await register_user(
        user_id,
        username,
        invited_by,
        context.bot
    )

    # =========================
    # Forced Join Check
    # =========================
    if not await is_user_member(context.bot, user_id):

        await update.message.reply_text(
            "برای استفاده از ربات ابتدا عضو کانال‌ها شو 👇",
            reply_markup=build_join_keyboard()
        )

        return

    await update.message.reply_text(
        f"سلام {user.first_name} 🌿",
        reply_markup=main_menu(user_id)
    )


# =========================================
# حساب من
# =========================================
async def account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    # anti spam
    if is_spam(context, query.from_user.id):

        await query.answer(
            "⏳ کمی صبر کن.",
            show_alert=True
        )

        return

    # forced join
    if not await is_user_member(context.bot, query.from_user.id):

        await join_required_message(update, context)

        return

    await query.answer()

    user = get_user(query.from_user.id)

    text = f"""
💼 حساب شما

🆔 {user['user_id']}
🪙 سکه: {user['coins']}
👥 دعوت‌ها: {user['invites']}
"""

    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
        ])
    )


# =========================================
# لینک دعوت
# =========================================
async def free_coin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if is_spam(context, query.from_user.id):

        await query.answer(
            "⏳ کمی صبر کن.",
            show_alert=True
        )

        return

    if not await is_user_member(context.bot, query.from_user.id):

        await join_required_message(update, context)

        return

    await query.answer()

    bot_username = (await context.bot.get_me()).username

    link = f"https://t.me/{bot_username}?start={query.from_user.id}"

    text = f"""
🎁 لینک دعوت شما:

{link}

✅ هر دعوت = {REFERRAL_REWARD} سکه
"""

    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
        ])
    )


# =========================================
# پلن‌ها
# =========================================
async def free_plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if is_spam(context, query.from_user.id):

        await query.answer(
            "⏳ کمی صبر کن.",
            show_alert=True
        )

        return

    if not await is_user_member(context.bot, query.from_user.id):

        await join_required_message(update, context)

        return

    await query.answer()

    keyboard = [
        [InlineKeyboardButton("(استخونی🐪)15MB | 1🪙", callback_data="plan_1")],
        [InlineKeyboardButton("(نی قلیون🐪)50MB | 3🪙", callback_data="plan_2")],
        [InlineKeyboardButton("(فیت🐪)80MB | 5🪙", callback_data="plan_3")],
        [InlineKeyboardButton("(توپر🐪)200MB | 10🪙", callback_data="plan_4")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]

    await query.message.edit_text(
        "🐪 انتخاب پلن",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================
# دریافت کانفیگ
# =========================================
async def claim_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if is_spam(context, query.from_user.id):
        await query.answer("⏳ کمی صبر کن.", show_alert=True)
        return

    if not await is_user_member(context.bot, query.from_user.id):
        await join_required_message(update, context)
        return

    await query.answer()

    plan_id = int(query.data.split("_")[1])
    print("PLAN CLICKED:", plan_id)

    success, result = claim_plan(query.from_user.id, plan_id)

    if success:

        text = f"✅ کانفیگ شما:\n\n<code>{result}</code>"

        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
            ])
        )

    else:

        await query.message.edit_text(
            f"❌ {result}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
            ])
        )


# =========================================
# باز کردن پنل ادمین از دکمه ریپلای
# =========================================
async def open_admin_panel_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = message.from_user.id

    # anti spam
    if is_spam(context, user_id):
        await message.reply_text("⏳ کمی صبر کن.")
        return

    # forced join
    if not await is_user_member(context.bot, user_id):
        await join_required_message(update, context)
        return

    if user_id not in ADMINS:
        return

    keyboard = [
        [
            InlineKeyboardButton("📊 آمار", callback_data="admin_stats"),
            InlineKeyboardButton("👥 کاربران", callback_data="admin_users_by_coins")
        ],
        [
            InlineKeyboardButton("🔍 جستجو", callback_data="admin_find_user"),
            InlineKeyboardButton("🎯 تنظیم سکه", callback_data="admin_set_coins")
        ],
        [
            InlineKeyboardButton("⛔ بلاک", callback_data="admin_block"),
            InlineKeyboardButton("✅ آنبلاک", callback_data="admin_unblock")
        ],
        [
            InlineKeyboardButton("📂 مدیریت پلن‌ها", callback_data="admin_manage_plans")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")
        ]
    ]

    await message.reply_text(
        "⚙️ پنل مدیریت",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



# =========================================
# پنل ادمین
# =========================================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    if not query:
        return

    # anti spam
    if is_spam(context, query.from_user.id):
        await query.answer("⏳ کمی صبر کن.", show_alert=True)
        return

    # forced join
    if not await is_user_member(context.bot, query.from_user.id):
        await join_required_message(update, context)
        return

    if query.from_user.id not in ADMINS:
        return

    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton("📊 آمار", callback_data="admin_stats"),
            InlineKeyboardButton("👥 کاربران", callback_data="admin_users_by_coins")
        ],
        [
            InlineKeyboardButton("🔍 جستجو", callback_data="admin_find_user"),
            InlineKeyboardButton("🎯 تنظیم سکه", callback_data="admin_set_coins")
        ],
        [
            InlineKeyboardButton("⛔ بلاک", callback_data="admin_block"),
            InlineKeyboardButton("✅ آنبلاک", callback_data="admin_unblock")
        ],
        [
            InlineKeyboardButton("📂 مدیریت پلن‌ها", callback_data="admin_manage_plans")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")
        ]
    ]

    await query.message.edit_text(
        "⚙️ پنل مدیریت",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================================
# زیرمنوی مدیریت پلن‌ها
# =========================================
async def admin_manage_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton("➕ شارژ پلن 1", callback_data="admin_add_config_1"),
            InlineKeyboardButton("🗑 حذف پلن 1", callback_data="confirm_delete_plan_1")
        ],
        [
            InlineKeyboardButton("➕ شارژ پلن 2", callback_data="admin_add_config_2"),
            InlineKeyboardButton("🗑 حذف پلن 2", callback_data="confirm_delete_plan_2")
        ],
        [
            InlineKeyboardButton("➕ شارژ پلن 3", callback_data="admin_add_config_3"),
            InlineKeyboardButton("🗑 حذف پلن 3", callback_data="confirm_delete_plan_3")
        ],
        [
            InlineKeyboardButton("➕ شارژ پلن 4", callback_data="admin_add_config_4"),
            InlineKeyboardButton("🗑 حذف پلن 4", callback_data="confirm_delete_plan_4")
        ],
        [
            InlineKeyboardButton("📦 موجودی پلن‌ها", callback_data="admin_stock")
        ],
        [
            InlineKeyboardButton("🗑 حذف لینک خراب", callback_data="delete_single_config_start")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")
        ]
    ]

    await query.message.edit_text(
        "📂 مدیریت پلن‌ها",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================================
# آمار
# =========================================
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    users, refs, stock = get_stats()

    text = f"""
📊 آمار ربات

👤 کاربران: {users}
👥 رفرال: {refs}
📦 موجودی: {stock}
"""

    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")]
        ])
    )

#==========================
#لیست کاربران بر اساس سکه
#===========================

async def admin_users_by_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id, username, coins, invites, is_blocked
        FROM users
        ORDER BY coins DESC, user_id ASC
        LIMIT 50
    """)

    rows = cur.fetchall()
    conn.close()

    if not rows:
        await query.message.edit_text(
            "❌ هیچ کاربری پیدا نشد",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")]
            ])
        )
        return

    text = "🏆 کاربران بر اساس سکه\n\n"

    for i, row in enumerate(rows, start=1):
        user_id, username, coins, invites, is_blocked = row
        uname = f"@{username}" if username else "ندارد"
        text += (
            f"{i}. {uname}\n"
            f"🆔 {user_id}\n"
            f"🪙 {coins} | 👥 {invites} | 🚫 {'بله' if is_blocked else 'خیر'}\n\n"
        )

    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")]
        ])
    )


# =========================================
# موجودی
# =========================================
async def admin_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    conn = get_connection()
    cur = conn.cursor()

    text = "📦 موجودی پلن‌ها\n\n"

    for plan_id in [1, 2, 3, 4]:

        cur.execute("""
        SELECT COUNT(*) FROM inventory
        WHERE
            plan_id=?
            AND is_used=0
        """, (plan_id,))

        count = cur.fetchone()[0]

        text += f"پلن {plan_id}: {count}\n"

    conn.close()

    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")]
        ])
    )


#===================
#تغییر موجودی کامل
#====================

async def admin_set_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["state"] = "admin_set_coins_user"
    await query.message.edit_text("آیدی کاربر را برای تنظیم موجودی ارسال کن")


# =========================================
# شارژ پلن‌ها (افزودن چند کانفیگ برای یک پلن)
# =========================================
async def admin_add_config_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # مشخص کردن شماره پلن از دکمه‌ای که زده شده
    plan_id = int(query.data.split("_")[-1])
    context.user_data["add_plan_id"] = plan_id
    context.user_data["state"] = "waiting_config_bulk"

    await query.message.edit_text(
        f"📥 کانفیگ‌های پلن {plan_id} را بفرست.\n\n"
        f"🔹 هر کانفیگ باید در یک خط باشد.\n"
        f"🔹 فقط لینک‌هایی مثل:\n"
        f"vless://...\nvmess://...\ntrojan://...\nss://...\n\n"
        f"✔️ مثال:\n"
        f"vless://aaa\n"
        f"vmess://bbb\n"
        f"trojan://ccc",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ لغو", callback_data="admin_manage_plans")]
        ])
    )


# =========================================
# شروع حذف تکی کانفیگ / حذف لینک خراب
# =========================================
async def delete_single_config_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["state"] = "waiting_for_delete_config"

    await query.message.edit_text(
        "🔍 کانفیگ کامل را ارسال کن تا حذف شود:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ انصراف", callback_data="admin_manage_plans")]
        ])
    )


#=======================
# برای دکمه های ریپلای 
#=======================

async def menu_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == "💼 حساب من":
        user = get_user(user_id)
        if not user:
            await update.message.reply_text("❌ کاربر یافت نشد.")
            return

        msg = f"""
💼 حساب شما

🆔 آیدی: {user['user_id']}
🪙 سکه‌ها: {user['coins']}
👥 دعوت‌ها: {user['invites']}
"""
        await update.message.reply_text(msg)

    elif text == "🎁 دریافت سکه رایگان":
        bot_username = (await context.bot.get_me()).username
        invite_link = f"https://t.me/{bot_username}?start={user_id}"

        msg = f"""
🎁 کسب سکه رایگان

لینک دعوت اختصاصی شما:

{invite_link}

✅ به ازای هر نفر که:
1️⃣ با لینک شما وارد ربات شود  
2️⃣ عضو کانال‌های اجباری شود  
🪙 یک سکه به شما تعلق می‌گیرد.
"""
        await update.message.reply_text(msg)

    elif text == "🐪 دریافت شتر رایگان":
        keyboard = [
            [InlineKeyboardButton("(استخونی🐪) 15MB | 1🪙", callback_data="plan_1")],
            [InlineKeyboardButton("(نی قلیون🐪) 50MB | 3🪙", callback_data="plan_2")],
            [InlineKeyboardButton("(فیت🐪) 80MB | 5🪙", callback_data="plan_3")],
            [InlineKeyboardButton("(توپر🐪) 200MB | 10🪙", callback_data="plan_4")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
    
        await update.message.reply_text(
            "یکی از پلن‌های زیر را انتخاب کنید:",
            reply_markup=reply_markup
        )    


    elif text == "🐪 خرید شتر اختصاصی":
        await update.message.reply_text(
            "برای خرید شتر اختصاصی، با آیدی زیر ارتباط بگیر:\n"
            "@arminkarimi4"
        )

    elif text == "📨 پشتیبانی":
        await update.message.reply_text(
            "برای ارتباط با پشتیبانی به آیدی زیر پیام بده:\n@arminkarimi4"
        )

    elif text == "⚙️ پنل مدیریت":
        await open_admin_panel_from_message(update, context)


# =========================================
# پردازش پیام ادمین
# =========================================
async def admin_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    state = context.user_data.get("state")

    # اگر ادمین در حالت خاصی نیست → پیام باید به منوی اصلی برود
    if not state:
        return await menu_message_handler(update, context)

    # =========================
    # شارژ پلن‌ها — افزودن چند کانفیگ
    # =========================
    elif state == "waiting_config_bulk":
        plan_id = context.user_data.get("add_plan_id")
        lines = update.message.text.split("\n")

        conn = get_connection()
        cur = conn.cursor()

        added = 0

        for cfg in lines:
            cfg = cfg.strip()

            if cfg.startswith(("vless://", "vmess://", "trojan://", "ss://")):
                cur.execute(
                    "INSERT INTO inventory (plan_id, config, is_used) VALUES (?, ?, 0)",
                    (plan_id, cfg)
                )
                added += 1

        conn.commit()
        conn.close()

        context.user_data["state"] = None
        context.user_data.pop("add_plan_id", None)

        await update.message.reply_text(
            f"✅ {added} کانفیگ برای پلن {plan_id} اضافه شد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_manage_plans")]
            ])
        )
        return



# =========================
#  پیدا کردن کاربر
# =========================
    elif state == "find_user":
        try:
           user_id = int(update.message.text)
        except:
            await update.message.reply_text("❌ آیدی نامعتبر است")
            return   

        user = get_user(user_id)

        if user:
                await update.message.reply_text(
                   f"ID: {user['user_id']}\n"
                   f"Coins: {user['coins']}\n"
                   f"Invites: {user['invites']}\n"
                   f"Blocked: {user['is_blocked']}"
                )
        else:
            await update.message.reply_text("کاربر پیدا نشد")

        context.user_data["state"] = None


# =========================
#  بلاک کاربر
# =========================
    elif state == "block_user":
        try:
            user_id = int(update.message.text)
        except:
            await update.message.reply_text("❌ آیدی نامعتبر است")
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_blocked=1 WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()

        await update.message.reply_text("✅ کاربر بلاک شد")
        context.user_data["state"] = None


# =========================
#  آنبلاک
# =========================
    elif state == "unblock_user":
        try:
            user_id = int(update.message.text)
        except:
            await update.message.reply_text("❌ آیدی نامعتبر است")
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_blocked=0 WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()

        await update.message.reply_text("✅ کاربر آنبلاک شد")
        context.user_data["state"] = None

    # =========================
    #  تنظیم سکه – مرحله ۱
    # =========================
    
    elif state == "admin_set_coins_user":
        try:
            context.user_data["target_user_id"] = int(update.message.text)
            context.user_data["state"] = "admin_set_coins_amount"

            keyboard = [
                [InlineKeyboardButton("❌ انصراف", callback_data="admin_panel")]
            ]

            await update.message.reply_text(
                "عدد نهایی موجودی را بفرست",
                 reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except:
            await update.message.reply_text("❌ آیدی نامعتبر است")


    # =========================
    #  تنظیم سکه – مرحله ۲
    # =========================
    elif state == "admin_set_coins_amount":
        try:
            amount = int(update.message.text)
            target_user_id = context.user_data.get("target_user_id")

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE users SET coins = ? WHERE user_id = ?", (amount, target_user_id))
            conn.commit()
            conn.close()

            await update.message.reply_text("✅ موجودی کاربر با موفقیت تغییر کرد")
        except:
            await update.message.reply_text("❌ مقدار نامعتبر است")

        context.user_data["state"] = None
        context.user_data.pop("target_user_id", None)
    
    
    
  #==========================
  # حذف تکی کانفینگ
  #==========================
  
    elif state == "waiting_for_delete_config":
        config_text = update.message.text

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM inventory WHERE config=?", (config_text,))
        deleted = cur.rowcount
        conn.commit()
        conn.close()

        if deleted > 0:
            await update.message.reply_text("✅ کانفیگ مورد نظر از دیتابیس حذف شد.")
        else:
            await update.message.reply_text("❌ چنین کانفیگی در انبار یافت نشد.")
        
        context.user_data["state"] = None # پاک کردن وضعیت ادمین
    
#===================================
#تایید دو مرحبه برای حذف کانفینگ
#====================================
# ===================================
# تایید دو مرحله‌ای برای حذف کانفیگ
# ===================================
async def confirm_delete_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    plan_id = int(query.data.split("_")[-1])

    keyboard = [
        [InlineKeyboardButton("✅ بله، حذف کن", callback_data=f"delete_plan_final_{plan_id}")],
        [InlineKeyboardButton("❌ لغو", callback_data="admin_manage_plans")] # اصلاح شد
    ]

    await query.message.edit_text(
        f"⚠️ مطمئنی می‌خواهی تمام کانفیگ‌های پلن {plan_id} را حذف کنی؟\nاین عملیات قابل بازگشت نیست!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def delete_plan_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    plan_id = int(query.data.split("_")[-1])

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM inventory WHERE plan_id=?", (plan_id,))
    deleted_count = cur.rowcount
    conn.commit()
    conn.close()

    await query.message.edit_text(
        f"✅ تعداد {deleted_count} کانفیگ از پلن {plan_id} حذف شد.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 بازگشت به مدیریت حذف", callback_data="admin_manage_plans")]]
        )
    )


# =========================================
# ریست کامل
# =========================================
async def admin_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    if query.from_user.id not in ADMINS:
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM inventory")
    cur.execute("DELETE FROM claims")

    conn.commit()
    conn.close()

    await query.message.edit_text(
        "✅ inventory و claims پاک شدند",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")]
        ])
    )


# =========================================
# خرید
# =========================================
async def buy_plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if is_spam(context, query.from_user.id):

        await query.answer(
            "⏳ کمی صبر کن.",
            show_alert=True
        )

        return

    if not await is_user_member(context.bot, query.from_user.id):

        await join_required_message(update, context)

        return

    await query.answer()

    await query.message.edit_text(
        "@arminkarimi4",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
        ])
    )

async def admin_find_user(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    context.user_data["state"] = "find_user"

    keyboard = [
        [InlineKeyboardButton("❌ انصراف", callback_data="admin_panel")]
    ]

    await query.message.edit_text(
        "🔍 آیدی کاربر را بفرست:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



async def admin_block(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    context.user_data["state"] = "block_user"

    keyboard = [
        [InlineKeyboardButton("❌ انصراف", callback_data="admin_panel")]
    ]

    await query.message.edit_text(
        "🚫 آیدی کاربر برای بلاک را بفرست:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def admin_unblock(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    context.user_data["state"] = "unblock_user"

    keyboard = [
        [InlineKeyboardButton("❌ انصراف", callback_data="admin_panel")]
    ]

    await query.message.edit_text(
        "✅ آیدی کاربر برای آنبلاک را بفرست:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================================
# پشتیبانی
# =========================================
async def support_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if is_spam(context, query.from_user.id):

        await query.answer(
            "⏳ کمی صبر کن.",
            show_alert=True
        )

        return

    if not await is_user_member(context.bot, query.from_user.id):

        await join_required_message(update, context)

        return

    await query.answer()

    await query.message.edit_text(
        "@arminkarimi4",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
        ])
    )


# =========================================
# بازگشت
# =========================================
async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # حذف پیام قبلی (inline)
    try:
        await query.message.delete()
    except:
        pass

    await context.bot.send_message(
        chat_id=query.from_user.id,
        text="🏠 منوی اصلی",
        reply_markup=main_menu(query.from_user.id)
    )

# =========================================
# MAIN
# =========================================
def main():

    init_db()

    app = Application.builder().token(TOKEN).build()

    # commands
    app.add_handler(CommandHandler("start", start))

    # membership
    app.add_handler(
        CallbackQueryHandler(
            check_membership_callback,
            pattern="^check_membership$"
        )
    )

    # callbacks
    #app.add_handler(CallbackQueryHandler(account_callback, pattern="^account$", filters=filters.ChatType.PRIVATE))
    app.add_handler(CallbackQueryHandler(free_coin_callback, pattern="^free_coin$", filters=filters.ChatType.PRIVATE))
    app.add_handler(CallbackQueryHandler(free_plan_callback, pattern="^free_plan$", filters=filters.ChatType.PRIVATE))
    app.add_handler(CallbackQueryHandler(claim_callback, pattern="^plan_\d+$", filters=filters.ChatType.PRIVATE)) # دقت کن، pattern باید با $ تموم بشه چون خود plan_id بعدش میاد

    # Admin callbacks - اینها را هم به private محدود کن، چون کاربر عادی نباید به پنل ادمین دسترسی داشته باشه
    app.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin_panel$", filters=filters.ChatType.PRIVATE))
    app.add_handler(CallbackQueryHandler(admin_manage_plans, pattern="^admin_manage_plans$", filters=filters.ChatType.PRIVATE))
    app.add_handler(CallbackQueryHandler(admin_stats, pattern="^admin_stats$", filters=filters.ChatType.PRIVATE))
    app.add_handler(CallbackQueryHandler(admin_stock, pattern="^admin_stock$", filters=filters.ChatType.PRIVATE))
    app.add_handler(CallbackQueryHandler(admin_reset, pattern="^admin_reset$", filters=filters.ChatType.PRIVATE))
    app.add_handler(CallbackQueryHandler(admin_users_by_coins, pattern="^admin_users_by_coins$", filters=filters.ChatType.PRIVATE))
    app.add_handler(CallbackQueryHandler(admin_set_coins, pattern="^admin_set_coins$", filters=filters.ChatType.PRIVATE))


    app.add_handler(CallbackQueryHandler(buy_plan_callback, pattern="^buy_plan$", filters=filters.ChatType.PRIVATE))
    app.add_handler(CallbackQueryHandler(support_callback, pattern="^support$", filters=filters.ChatType.PRIVATE))
    app.add_handler(CallbackQueryHandler(back_main, pattern="^back_main$", filters=filters.ChatType.PRIVATE))

    app.add_handler(CallbackQueryHandler(admin_find_user, pattern="^admin_find_user$", filters=filters.ChatType.PRIVATE))
    app.add_handler(CallbackQueryHandler(admin_block, pattern="^admin_block$", filters=filters.ChatType.PRIVATE))
    app.add_handler(CallbackQueryHandler(admin_unblock, pattern="^admin_unblock$", filters=filters.ChatType.PRIVATE))

    app.add_handler(CallbackQueryHandler(admin_add_config_start, pattern="^admin_add_config_", filters=filters.ChatType.PRIVATE)) # این هم pattern اش باید کامل باشه
    app.add_handler(CallbackQueryHandler(delete_single_config_start, pattern="^delete_single_config_start$", filters=filters.ChatType.PRIVATE))
    app.add_handler(CallbackQueryHandler(confirm_delete_plan, pattern="^confirm_delete_plan_", filters=filters.ChatType.PRIVATE)) # این هم pattern اش باید کامل باشه
    app.add_handler(CallbackQueryHandler(delete_plan_final, pattern="^delete_plan_final_", filters=filters.ChatType.PRIVATE)) # این هم pattern اش باید کامل باشه


    # Message handlers (فقط متن‌های معمولی، نه دستورات)
    admin_filter = filters.User(user_id=ADMINS) # این فیلتر ادمین‌هاست

    # پیام‌های متنی ادمین در چت خصوصی
    app.add_handler(
        MessageHandler(admin_filter & filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, admin_message_handler)
    )

    # پیام‌های متنی عادی کاربران در چت خصوصی
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, menu_message_handler)
    )



    print("BOT STARTED")

    app.run_polling()



if __name__ == "__main__":
    main()
