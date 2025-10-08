"""
Сообщения об ошибках для фильтров участия в конкурсах
Персонализированные подсказки для каждого типа ошибки
"""

# Username бота для ссылок
BOT_USERNAME = "Zazvezdilsya_bot"


def format_rejection_message(error_type: str, required: int = 0, current: int = 0) -> str:
    """
    Форматирование сообщения об отказе в участии
    
    Args:
        error_type: Тип ошибки ('min_referrals', 'min_contests', 'max_contests')
        required: Требуемое значение
        current: Текущее значение у пользователя
        
    Returns:
        Отформатированное сообщение с подсказками и ссылкой на бота
    """
    
    messages = {
        "min_referrals": {
            "emoji": "🔗",
            "reason": f"Нужно минимум {required} рефералов (у вас: {current})",
            "tips": [
                "💡 Как получить рефералов:",
                "• Пригласите друзей по своей реферальной ссылке",
                "• Получите ссылку в боте командой /start",
                "• Каждый подписавшийся друг = +1 реферал"
            ]
        },
        
        "min_contests": {
            "emoji": "🎯",
            "reason": f"Нужно минимум {required} участий в конкурсах (у вас: {current})",
            "tips": [
                "💡 Как получить больше участий:",
                "• Участвуйте в других конкурсах",
                "• Следите за анонсами в канале",
                "• Каждое участие приближает к цели"
            ]
        },
        
        "max_contests": {
            "emoji": "🆕",
            "reason": f"Этот конкурс только для участников с максимум {required} участиями (у вас: {current})",
            "tips": [
                "💡 Этот конкурс для новичков:",
                "• Дайте шанс другим участникам",
                "• Следующий конкурс может быть для вас!",
                "• Следите за анонсами в канале"
            ]
        },
        
        "not_subscribed": {
            "emoji": "⚠️",
            "reason": "Вы не подписаны на канал",
            "tips": [
                "💡 Что нужно сделать:",
                "• Подпишитесь на канал",
                "• Напишите комментарий снова",
                "• Участие в конкурсах доступно только для подписчиков"
            ]
        },
        
        "previous_winner": {
            "emoji": "🏆",
            "reason": "Вы были победителем в прошлом конкурсе этого типа",
            "tips": [
                "💡 Поздравляем с прошлой победой!",
                "• Дайте шанс другим участникам",
                "• Вы сможете участвовать в следующем конкурсе",
                "• Следите за новыми анонсами"
            ]
        }
    }
    
    # Получаем данные для этого типа ошибки
    msg_data = messages.get(error_type)
    
    if not msg_data:
        # Если тип ошибки неизвестен, возвращаем базовое сообщение
        return (
            f"❌ К сожалению, вы не можете участвовать в этом конкурсе.\n\n"
            f"📋 Подробности в боте: @{BOT_USERNAME}"
        )
    
    # Формируем красивое сообщение
    message_parts = [
        f"{msg_data['emoji']} **К сожалению, вы не можете участвовать в этом конкурсе.**\n",
        f"📋 **Причина:** {msg_data['reason']}\n"
    ]
    
    # Добавляем подсказки
    if msg_data['tips']:
        message_parts.append("\n".join(msg_data['tips']))
        message_parts.append("")  # Пустая строка
    
    # Добавляем ссылку на бота
    message_parts.append(f"👉 Подробнее в боте: @{BOT_USERNAME}")
    message_parts.append(f"📞 Вопросы? Напишите админу: @nbtov")
    
    return "\n".join(message_parts)


# Готовые сообщения для быстрого использования
def get_min_referrals_error(required: int, current: int) -> str:
    """Сообщение об ошибке: мало рефералов"""
    return format_rejection_message("min_referrals", required, current)


def get_min_contests_error(required: int, current: int) -> str:
    """Сообщение об ошибке: мало участий"""
    return format_rejection_message("min_contests", required, current)


def get_max_contests_error(required: int, current: int) -> str:
    """Сообщение об ошибке: слишком много участий"""
    return format_rejection_message("max_contests", required, current)


def get_not_subscribed_error() -> str:
    """Сообщение об ошибке: не подписан на канал"""
    return format_rejection_message("not_subscribed")


def get_previous_winner_error() -> str:
    """Сообщение об ошибке: был победителем в прошлом конкурсе"""
    return format_rejection_message("previous_winner")
