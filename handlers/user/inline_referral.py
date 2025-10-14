"""
Inline Mode для реферальной системы
Отправка приглашений через красивые сообщения
"""

from aiogram import Router
from aiogram.types import (
    InlineQuery, 
    InlineQueryResultArticle, 
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

router = Router()


@router.inline_query()
async def inline_referral(query: InlineQuery):
    """
    Обработка inline запросов для реферальной системы
    Пользователь нажимает кнопку → выбирает чат → отправляется приглашение
    """
    
    user_id = query.from_user.id
    bot_username = (await query.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    # Кнопка под сообщением (КЛИКАБЕЛЬНАЯ!)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎉 Присоединиться к конкурсам!", 
            url=referral_link
        )]
    ])
    
    # Текст сообщения
    message_text = (
        "🎁 <b>Вас пригласили в Sonfix!</b>\n\n"
        "У нас розыгрыши подарков, звёзд, ТГ премиумов 🏆\n\n"
        "👇 Нажми кнопку ниже, чтобы присоединиться:"
    )
    
    # Результат для отображения в списке выбора чата
    result = InlineQueryResultArticle(
        id="referral_invite",
        title="🎉 Пригласить друга в конкурсы",
        description="Нажми сюда что-бы пригласить",
        input_message_content=InputTextMessageContent(
            message_text=message_text,
            parse_mode="HTML"
        ),
        reply_markup=keyboard,
        thumbnail_url="https://db.stickerswiki.app/api/files/1nlpavfhdos0lje/3ry7c7z21om65e5/randgift_logo_v3ezses0o6.png"  # Иконка подарка
    )
    
    # Отправляем результат (cache_time=1 чтобы всегда показывать актуальное)
    await query.answer(
        results=[result], 
        cache_time=1,
        is_personal=True  # Персональный результат
    )
