"""
Статистика пользователя
Показывает реферальную ссылку, счётчики, прогресс
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database_postgres import db


router = Router()


@router.callback_query(F.data == "my_stats")
async def show_my_stats(callback: CallbackQuery):
    """
    Показать статистику пользователя
    """
    user_id = callback.from_user.id
    
    # Получаем статистику из БД
    stats = await db.get_user_stats(user_id)
    referral_count = await db.get_referral_count(user_id)
    
    # Формируем реферальную ссылку
    bot_username = (await callback.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    text = (
        "📊 **ВАША СТАТИСТИКА**\n\n"
        f"🔗 **Реферальная ссылка:**\n"
        f"`{referral_link}`\n\n"
        f"👥 Рефералов: {referral_count}\n"
        f"🎯 Участий в конкурсах: {stats['total_contests']}\n"
        f"🏆 Побед: {stats['total_wins']}\n\n"
        f"💡 Нажмите на ссылку выше, чтобы скопировать её и поделиться с друзьями!"
    )
    
    # Если есть победы по типам, показываем детальную статистику
    if stats['total_wins'] > 0:
        text += "\n\n📈 **Победы по типам:**\n"
        if stats.get('voting_wins', 0) > 0:
            text += f"🗳️ Голосовательные: {stats['voting_wins']}\n"
        if stats.get('random_wins', 0) > 0:
            text += f"🎰 Рандомайзер: {stats['random_wins']}\n"
        if stats.get('referral_wins', 0) > 0:
            text += f"👥 Реферальные: {stats['referral_wins']}\n"
        if stats.get('activity_wins', 0) > 0:
            text += f"⚡ Активность: {stats['activity_wins']}\n"
    
    # Если есть серии побед, показываем
    if stats.get('best_win_streak', 0) > 0:
        text += f"\n🔥 **Лучшая серия побед:** {stats['best_win_streak']}\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад в меню", callback_data="back_to_menu")
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()
