"""
Конфигурация Contest Bot v2.4
Использует переменные окружения для безопасности
"""

import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# ============== ОСНОВНЫЕ НАСТРОЙКИ ==============

# Токен бота (из .env)
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME", "starsdropsrobot")

# ID администратора (из .env)
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "adjetsky")

# ID бота (извлекается из токена)
BOT_ID = int(BOT_TOKEN.split(":")[0]) if BOT_TOKEN else 0

# Проверка критических переменных
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env файле!")
if not ADMIN_ID:
    raise ValueError("❌ ADMIN_ID не найден в .env файле!")

# ============== КАНАЛЫ И ГРУППЫ ==============

# ID канала (из .env)
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
DISCUSSION_GROUP_ID = int(os.getenv("DISCUSSION_GROUP_ID", 0))
CHANNEL_INVITE_LINK = os.getenv("CHANNEL_INVITE_LINK", "")
BOT_INVITE_LINK = os.getenv("BOT_INVITE_LINK", "")

if not CHANNEL_ID or not DISCUSSION_GROUP_ID:
    raise ValueError("❌ CHANNEL_ID или DISCUSSION_GROUP_ID не найдены в .env!")

# ============== БАЗА ДАННЫХ ==============

# PostgreSQL (из .env)
POSTGRES_DSN = os.getenv("DATABASE_URL")

if not POSTGRES_DSN:
    raise ValueError("❌ DATABASE_URL не найден в .env файле!")

# SQLite (для старой версии, опционально)
SQLITE_DATABASE_PATH = "contest_bot.db"

# ============== НАСТРОЙКИ КОНКУРСОВ ==============

# Настройки по умолчанию
DEFAULT_PARTICIPANTS_COUNT = 10
MAX_PARTICIPANTS_COUNT = 15
DEFAULT_TIMER_MINUTES = 60

# Интервал проверки комментариев (секунды)
COMMENT_CHECK_INTERVAL = 15

# Эмодзи для участников (15 уникальных)
PARTICIPANT_EMOJIS = [
    "😈", "❤️", "💩", "🏆", "👻", 
    "🔥", "💊", "💅", "🙈", "🕊", 
    "👀", "😡", "🐳", "💯", "👍"
]

# ============== ТИПЫ КОНКУРСОВ ==============

CONTEST_TYPES = {
    "voting_contest": {
        "name": "🗳️ Голосовательный",
        "description": "Админ выбирает победителя вручную"
    },
    "random_contest": {
        "name": "🎰 Рандомайзер",
        "description": "Победитель выбирается случайно"
    },
    "spam_contest": {
        "name": "⚡ Спам-конкурс",
        "description": "Победитель написал больше всех сообщений"
    }
}

# ============== УСЛОВИЯ УЧАСТИЯ ==============

ENTRY_CONDITIONS = {
    "first_n": {
        "name": "👥 Первые N человек",
        "description": "Только первые участники, кто написал комментарий"
    },
    "min_referrals": {
        "name": "🔗 Минимум рефералов",
        "description": "Участвовать могут только те, у кого есть рефералы"
    },
    "min_contests": {
        "name": "🎯 Минимум участий",
        "description": "Участвовать могут только активные пользователи"
    },
    "max_contests": {
        "name": "🆕 Максимум участий",
        "description": "Ограничить максимальное количество участий (например, только новички)"
    },
}

# ============== ДОСТИЖЕНИЯ ==============

ACHIEVEMENTS = {
    # Участие в конкурсах
    "participation": {
        "newbie": {"name": "Новичок", "emoji": "🎯", "required": 5},
        "advanced": {"name": "Продвинутый", "emoji": "⭐", "required": 50},
        "veteran": {"name": "Ветеран", "emoji": "🛡️", "required": 250},
        "legend": {"name": "Легенда", "emoji": "👑", "required": 1000}
    },
    
    # Победы
    "wins": {
        "lucky": {"name": "Везунчик", "emoji": "🍀", "required": 5},
        "winner": {"name": "Победитель", "emoji": "🏅", "required": 30},
        "champion": {"name": "Чемпион", "emoji": "🏆", "required": 100},
        "king": {"name": "Король", "emoji": "👑", "required": 1000}
    },
    
    # Рефералы
    "referrals": {
        "friend": {"name": "Друг", "emoji": "👋", "required": 5},
        "popular": {"name": "Популярный", "emoji": "🌟", "required": 25},
        "influencer": {"name": "Лидер мнений", "emoji": "💫", "required": 100},
        "blogger": {"name": "Блогер", "emoji": "🚀", "required": 1000}
    },
    
    # Особые (серии побед)
    "special": {
        "lucky_streak": {"name": "Просто повезло", "emoji": "🎲", "required": 2},
        "win_streak": {"name": "Серия побед", "emoji": "🔥", "required": 3},
        "unstoppable": {"name": "Невозмутимый", "emoji": "⚡", "required": 5}
    }
}

# ============== ТЕКСТЫ СООБЩЕНИЙ ==============

MESSAGES = {
    # Админ-панель
    "start_admin": "🎮 **Админ-панель Contest Bot v2.4**\n\nВыберите действие:",
    
    # Главное меню пользователя
    "start_user": (
        "🎮 **Зазвездился - Бот**\n\n"
        "Участвуйте в конкурсах и приглашайте друзей!\n\n"
        "Выберите действие:"
    ),
    
    # Подписка
    "not_subscribed": "⚠️ Вы не подписаны на канал!\n\n👉 Подпишитесь на канал для участия в конкурсе.",
    
    # Реферальная система
    "referral_welcome": (
        "👋 Привет!\n\n"
        "Вас пригласил: {referrer_name}\n\n"
        "🎁 Подпишитесь на наш канал, чтобы участвовать в конкурсах "
        "и помочь другу получить реферальное очко!\n\n"
        "После подписки нажмите кнопку ниже:"
    ),
    
    "referral_success": (
        "✅ Отлично! Вы подписались на канал.\n\n"
        "🎁 Реферальное очко начислено пригласившему!\n\n"
        "Теперь вы можете участвовать в конкурсах."
    ),
    
    "new_referral": (
        "🎉 У вас новый реферал!\n\n"
        "Пользователь {name} подписался по вашей ссылке.\n"
        "+1 очко! 🌟"
    )
}

# ============== АВТОМАТИЧЕСКОЕ ПРИНЯТИЕ ЗАЯВОК ==============

AUTO_APPROVE_ENABLED = True

print("✅ Конфигурация загружена из .env")