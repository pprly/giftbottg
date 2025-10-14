"""
Статистика пользователя
Показывает реферальную ссылку, счётчики, прогресс
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database_postgres import db
from urllib.parse import quote


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
        "📊 <b>ВАША СТАТИСТИКА</b>\n\n"
        f"👥 Рефералов: {referral_count}\n"
        f"🎯 Участий в конкурсах: {stats['total_contests']}\n"
        f"🏆 Побед: {stats['total_wins']}\n\n"
        f"💡 <b>Пригласите друзей!</b>\n"
        f"Нажмите кнопку ниже, выберите чат и отправьте приглашение!"
    )
    
    # Если есть победы по типам
    if stats['total_wins'] > 0:
        text += "\n\n📈 <b>Победы по типам:</b>\n"
        if stats.get('voting_wins', 0) > 0:
            text += f"🗳️ Голосовательные: {stats['voting_wins']}\n"
        if stats.get('random_wins', 0) > 0:
            text += f"🎰 Рандомайзер: {stats['random_wins']}\n"
        if stats.get('spam_wins', 0) > 0:
            text += f"⚡ Спам-конкурс: {stats['spam_wins']}\n"
    
    # Серии побед
    if stats.get('best_win_streak', 0) > 0:
        text += f"\n🔥 <b>Лучшая серия побед:</b> {stats['best_win_streak']}\n"
    
    builder = InlineKeyboardBuilder()
    
    # ✅ НОВАЯ КНОПКА - Inline Mode
    builder.button(
        text="📤 Пригласить друга", 
        switch_inline_query="приглашение"  # Открывает список чатов
    )
    
    # Дополнительная кнопка - скопировать ссылку (для тех, кто хочет отправить вручную)
    # builder.button(
    #    text="🔗 Скопировать ссылку",
    #    callback_data="copy_referral_link"
    #)
    
    builder.button(text="🔙 Назад в меню", callback_data="back_to_menu")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "copy_referral_link")
async def copy_referral_link(callback: CallbackQuery):
    """
    Показать ссылку для копирования
    """
    user_id = callback.from_user.id
    bot_username = (await callback.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    await callback.answer(
        f"Ваша реферальная ссылка:\n{referral_link}\n\nСкопируйте и отправьте друзьям!",
        show_alert=True
    )


