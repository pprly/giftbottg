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
        "📊 **ВАША СТАТИСТИКА**\n\n"
        f"👥 Рефералов: {referral_count}\n"
        f"🎯 Участий в конкурсах: {stats['total_contests']}\n"
        f"🏆 Побед: {stats['total_wins']}\n\n"
        f"🔗 **Реферальная ссылка:**\n"
        f"`{referral_link}`\n\n"
        f"💡 **Как пригласить друга:**\n"
        f"1️⃣ Нажмите \"📤 Пригласить друга\"\n"
        f"2️⃣ Выберите чат и отправьте\n"
        f"3️⃣ Друг нажмет на ссылку\n"
        f"4️⃣ Вам начислится реферал!"
    )
    
    # Если есть победы по типам, показываем детальную статистику
    if stats['total_wins'] > 0:
        text += "\n\n📈 **Победы по типам:**\n"
        if stats.get('voting_wins', 0) > 0:
            text += f"🗳️ Голосовательные: {stats['voting_wins']}\n"
        if stats.get('random_wins', 0) > 0:
            text += f"🎰 Рандомайзер: {stats['random_wins']}\n"
        if stats.get('spam_wins', 0) > 0:
            text += f"⚡ Спам-конкурс: {stats['spam_wins']}\n"
    
    # Если есть серии побед, показываем
    if stats.get('best_win_streak', 0) > 0:
        text += f"\n🔥 **Лучшая серия побед:** {stats['best_win_streak']}\n"
    
    builder = InlineKeyboardBuilder()
    
    # Кнопка для приглашения друзей (откроет список чатов)
    from urllib.parse import quote
    invite_text = quote(f"🎉 Присоединяйся к конкурсам!\n{referral_link}")
    builder.button(
        text="📤 Пригласить друга", 
        url=f"https://t.me/share/url?url={quote(referral_link)}&text={invite_text}"
    )
    
    # Кнопка для копирования (покажет alert с ссылкой)
    builder.button(text="📋 Показать ссылку", callback_data=f"show_ref_{user_id}")
    
    builder.button(text="🔙 Назад в меню", callback_data="back_to_menu")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("show_ref_"))
async def show_referral_link(callback: CallbackQuery):
    """Показать реферальную ссылку в alert окне"""
    user_id = int(callback.data.split("_")[2])
    bot_username = (await callback.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    await callback.answer(
        f"📋 Ваша реферальная ссылка:\n\n{referral_link}\n\nДолгое нажатие для копирования",
        show_alert=True
    )