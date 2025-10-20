from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import config

router = Router()

@router.message(Command("publish_rules"))
async def publish_rules(message: Message):
    """Публикация правил в канале с кнопкой"""
    
    # Проверка что это админ
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("⛔ У вас нет доступа!")
        return
    
    # Короткий текст правил
    text = (
        "📢 **ПРАВИЛА УЧАСТИЯ В КОНКУРСАХ**\n\n"
        "🎯 **Как участвовать:**\n"
        "1. Подпишитесь на канал\n"
        "2. Напишите комментарий под постом\n"
        "3. Дождитесь результатов\n\n"
        "💰 **Типы конкурсов:**\n"
        "🆓 Голосовательные, Рандомайзер\n"
        "⭐ 1 звезда: Спам-конкурсы\n\n"
        "⚠️ **Написав комментарий, вы соглашаетесь:**\n"
        "• На публикацию @username\n"
        "• С обработкой данных ботом\n"
        "• С полными правилами конкурсов\n\n"
        "❌ **Запрещено:** мультиаккаунты, спам, боты\n"
        "🚫 Нарушение = дисквалификация\n\n"
        "🎁 Призы выдаются в течение 7 дней\n\n"
        "✅ Соответствует Terms of Service Telegram\n\n"
        "👇 Откройте бота для просмотра полных правил"
    )
    
    # Deep link в бота
    bot_info = await message.bot.get_me()
    bot_username = bot_info.username
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📖 Открыть полные правила",
            url=f"https://t.me/{bot_username}?start=rules"
        )]
    ])
    
    # Отправляем в канал
    await message.bot.send_message(
        chat_id=config.CHANNEL_ID,
        text=text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    
    await message.answer("✅ Правила опубликованы в канале!")