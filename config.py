import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "database", "bot.db")

TOKEN = "8720876053:AAEpwBoaAEQZqtwbsqz98-7oA3tu-12i2W0"

DEFAULT_LANG = "fa"


ADMINS = [
    400900388,
    1483857146
]

SUPPORT_ID = "@arminkarimi4"
SELLER_ID = "@arminkarimi4"

#DATABASE_PATH = "database/bot.db"

REFERRAL_REWARD = 1

PLANS = {
    1: {"price": 1, "name": "استخونی 🐪", "traffic": "15MB"},
    2: {"price": 3, "name": "نی قلیون 🐪", "traffic": "50MB"},
    3: {"price": 5, "name": "فیت 🐪", "traffic": "80MB"},
    4: {"price": 10, "name": "توپر 🐪", "traffic": "200MB"},
}

LOW_STOCK_WARNING = 3

# =========================
# Forced Join
# =========================

REQUIRED_CHATS = [
    {
        "chat_id": "@Shotor_AR",
        "title": "کانال اصلی"
    },
    {
        "chat_id": "@shotorAR_GP",
        "title": "گروه پشتیبانی"
    }
]

# =========================
# Anti Spam
# =========================

SPAM_WINDOW_SECONDS = 5
SPAM_MAX_ACTIONS = 4

