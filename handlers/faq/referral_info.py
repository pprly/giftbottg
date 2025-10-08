"""
Информация о реферальной программе
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


router = Router()


@router.callback_query(F.data == "faq_referral")
async def show_referral_info(callback: CallbackQuery):
    """
    Информация о реферальной программе
    """
    text = (
        "👥 **РЕФЕРАЛЬНАЯ ПРОГРАММА**\n\n"
        
        "**Как получить ссылку:**\n"
        "1️⃣ Нажмите \"📊 Моя статистика\" в главном меню\n"
        "2️⃣ Скопируйте вашу уникальную реферальную ссылку\n"
        "3️⃣ Поделитесь ей с друзьями\n\n"
        
        "**Как работает:**\n"
        "• Друг переходит по вашей ссылке\n"
        "• Подписывается на канал\n"
        "• Вы получаете +1 очко 🌟\n\n"
        
        "**Для чего нужны очки:**\n"
        "• Участие в реферальных конкурсах\n"
        "• Больше очков = больше шанс победить\n"
        "• Показывает вашу активность в сообществе\n"
        "• Открывает достижения\n\n"
        
        "**Правила:**\n"
        "• Нельзя использовать свою же ссылку\n"
        "• Реферал должен подписаться на канал\n"
        "• Один человек может быть рефералом только один раз\n"
        "• Ваш реферал тоже может приглашать друзей"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад к FAQ", callback_data="how_to_participate")
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()
