"""
Утилиты для форматирования текстов и сообщений
"""


def format_time_left(minutes: int) -> str:
    """
    Правильное склонение времени
    
    Args:
        minutes: Количество минут
        
    Returns:
        Отформатированная строка, например: "5 минут", "1 минута", "2 минуты"
    """
    if minutes == 1:
        return "1 минута"
    elif minutes in [2, 3, 4]:
        return f"{minutes} минуты"
    else:
        return f"{minutes} минут"


def format_participant_list(participants: list, include_blockquote: bool = True) -> str:
    """
    Форматирование списка участников с эмодзи
    
    Args:
        participants: Список участников из БД
        include_blockquote: Использовать ли HTML blockquote
        
    Returns:
        Отформатированный список
    """
    lines = []
    
    for p in participants:
        emoji = p['comment_text']
        
        # Если есть username - показываем его, если нет - показываем имя
        if p['username'] and p['username'] != "noname":
            display_name = f"@{p['username']}"
        else:
            display_name = p['full_name']
        
        line = f"{p['position']} {emoji} — {display_name}"
        lines.append(line)
    
    text = "\n".join(lines)
    
    if include_blockquote:
        return f"<blockquote>\n{text}\n</blockquote>"
    else:
        return text


def format_number(num: int) -> str:
    """
    Форматирование числа с разделителями
    
    Args:
        num: Число
        
    Returns:
        Отформатированное число, например: "1 000", "10 500"
    """
    return f"{num:,}".replace(",", " ")


def format_achievement_progress(current: int, required: int) -> str:
    """
    Форматирование прогресса достижения
    
    Args:
        current: Текущее значение
        required: Необходимое значение
        
    Returns:
        Строка прогресса, например: "(15/50)"
    """
    return f"({current}/{required})"


def format_progress_bar(current: int, required: int, length: int = 10) -> str:
    """
    Создание прогресс-бара
    
    Args:
        current: Текущее значение
        required: Необходимое значение
        length: Длина прогресс-бара (количество символов)
        
    Returns:
        Прогресс-бар, например: "████░░░░░░ 40%"
    """
    if required == 0:
        return "█" * length + " 100%"
    
    progress = min(current / required, 1.0)  # Не больше 100%
    filled = int(progress * length)
    empty = length - filled
    
    bar = "█" * filled + "░" * empty
    percent = int(progress * 100)
    
    return f"{bar} {percent}%"