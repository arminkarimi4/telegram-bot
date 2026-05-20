import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import (
    REQUIRED_CHATS,
    SPAM_WINDOW_SECONDS,
    SPAM_MAX_ACTIONS
)


# =========================
# Admin Check
# =========================

def is_admin(user_id, admins):
    return user_id in admins


# =========================
# Forced Join
# =========================

def build_join_keyboard():
    """
    ساخت کیبورد عضویت اجباری با دکمه‌های ورود + دکمه بررسی عضویت
    """
    keyboard = []

    for chat in REQUIRED_CHATS:
        chat_id = chat["chat_id"]
        title = chat["title"]

        # تبدیل @channelname به لینک مستقیم
        if str(chat_id).startswith("@"):
            link = f"https://t.me/{chat_id.replace('@', '')}"
        else:
            # اگر ID عددی بود
            link = f"https://t.me/{chat_id}"

        keyboard.append([
            InlineKeyboardButton(
                f"عضویت در {title}",
                url=link
            )
        ])

    # دکمه بررسی عضویت
    keyboard.append([
        InlineKeyboardButton(
            "✅ بررسی عضویت",
            callback_data="check_membership"
        )
    ])

    return InlineKeyboardMarkup(keyboard)

async def is_user_member(bot, user_id):
    for chat in REQUIRED_CHATS:
        try:
            member = await bot.get_chat_member(chat["chat_id"], user_id)
            # اگر وضعیت عضو نباشد (left یا kicked)
            if member.status in ["left", "kicked"]:
                return False
        except Exception as e:
            print(f"Error checking membership in {chat['chat_id']}: {e}")
            # اگر خطا داد (مثلا ربات ادمین نیست)، حتما باید False برگردانیم
            return False 
    return True



# =========================
# Anti Spam System
# =========================

def is_spam(context, user_id):
    now = time.time()

    if "spam_tracker" not in context.application.bot_data:
        context.application.bot_data["spam_tracker"] = {}

    tracker = context.application.bot_data["spam_tracker"]

    # اگر اولین درخواست این کاربره
    if user_id not in tracker:
        tracker[user_id] = []

    # ثبت زمان عمل
    tracker[user_id].append(now)

    # پاکسازی اعمال قدیمی
    tracker[user_id] = [
        t for t in tracker[user_id]
        if now - t <= SPAM_WINDOW_SECONDS
    ]

    # اگر تعداد اعمال بیش از حد مجاز باشد → اسپم
    return len(tracker[user_id]) > SPAM_MAX_ACTIONS


def clear_spam(context, user_id):
    if "spam_tracker" in context.application.bot_data:
        context.application.bot_data["spam_tracker"].pop(user_id, None)
