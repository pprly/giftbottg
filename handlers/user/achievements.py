"""
Система достижений
Проверка и отображение бейджей пользователя
"""

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import config
from database_postgres import db


router = Router()


async def check_achievements(bot: Bot, user_id: int):
    """
    Проверка всех достижений пользователя
    Вызывается после важных событий (участие, победа, реферал)
    """
    stats = await db.get_user_stats(user_id)
    new_achievements = []
    
    # 🎯 Достижения за участие
    participation_levels = [
        ("newbie", 5),
        ("advanced", 50),
        ("veteran", 250),
        ("legend", 1000)
    ]
    
    for level, required in participation_levels:
        if stats['total_contests'] >= required:
            unlocked = await db.check_and_unlock_achievement(user_id, "participation", level)
            if unlocked:
                new_achievements.append({
                    "type": "participation",
                    "level": level,
                    "emoji": config.ACHIEVEMENTS["participation"][level]["emoji"],
                    "name": config.ACHIEVEMENTS["participation"][level]["name"]
                })
    
    # 🏆 Достижения за победы
    wins_levels = [
        ("lucky", 5),
        ("winner", 30),
        ("champion", 100),
        ("king", 1000)
    ]
    
    for level, required in wins_levels:
        if stats['total_wins'] >= required:
            unlocked = await db.check_and_unlock_achievement(user_id, "wins", level)
            if unlocked:
                new_achievements.append({
                    "type": "wins",
                    "level": level,
                    "emoji": config.ACHIEVEMENTS["wins"][level]["emoji"],
                    "name": config.ACHIEVEMENTS["wins"][level]["name"]
                })
    
    # 👥 Достижения за рефералов
    referral_count = await db.get_referral_count(user_id)
    referral_levels = [
        ("friend", 5),
        ("popular", 25),
        ("influencer", 100),
        ("blogger", 1000)
    ]
    
    for level, required in referral_levels:
        if referral_count >= required:
            unlocked = await db.check_and_unlock_achievement(user_id, "referrals", level)
            if unlocked:
                new_achievements.append({
                    "type": "referrals",
                    "level": level,
                    "emoji": config.ACHIEVEMENTS["referrals"][level]["emoji"],
                    "name": config.ACHIEVEMENTS["referrals"][level]["name"]
                })
    
    # Отправляем уведомления о новых достижениях
    for achievement in new_achievements:
        try:
            await bot.send_message(
                user_id,
                f"🎉 **НОВОЕ ДОСТИЖЕНИЕ!**\n\n"
                f"{achievement['emoji']} **{achievement['name']}**\n\n"
                f"Посмотреть все достижения: /start → 🏆 Достижения",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"⚠️ Не удалось отправить уведомление о достижении: {e}")


@router.callback_query(F.data == "achievements")
async def show_achievements(callback: CallbackQuery):
    """Показать все достижения пользователя"""
    user_id = callback.from_user.id
    stats = await db.get_user_stats(user_id)
    referral_count = await db.get_referral_count(user_id)
    
    text = "🏆 **ВАШИ ДОСТИЖЕНИЯ**\n\n"
    
    # 🎯 Участие
    text += "🎯 **Участие в конкурсах:**\n"
    participation_levels = [
        ("newbie", 5, "Новичок"),
        ("advanced", 50, "Продвинутый"),
        ("veteran", 250, "Ветеран"),
        ("legend", 1000, "Легенда")
    ]
    
    for level, required, name in participation_levels:
        has = await db.has_achievement(user_id, "participation", level)
        current = stats['total_contests']
        
        if has:
            text += f"   ✅ {name} ({required})\n"
        else:
            text += f"   🔒 {name} ({current}/{required})\n"
    
    # 🏆 Победы
    text += "\n🏆 **Победы:**\n"
    wins_levels = [
        ("lucky", 5, "Везунчик"),
        ("winner", 30, "Победитель"),
        ("champion", 100, "Чемпион"),
        ("king", 1000, "Король")
    ]
    
    for level, required, name in wins_levels:
        has = await db.has_achievement(user_id, "wins", level)
        current = stats['total_wins']
        
        if has:
            text += f"   ✅ {name} ({required})\n"
        else:
            text += f"   🔒 {name} ({current}/{required})\n"
    
    # 👥 Рефералы
    text += "\n👥 **Рефералы:**\n"
    referral_levels = [
        ("friend", 5, "Друг"),
        ("popular", 25, "Популярный"),
        ("influencer", 100, "Лидер мнений"),
        ("blogger", 1000, "Блогер")
    ]
    
    for level, required, name in referral_levels:
        has = await db.has_achievement(user_id, "referrals", level)
        current = referral_count
        
        if has:
            text += f"   ✅ {name} ({required})\n"
        else:
            text += f"   🔒 {name} ({current}/{required})\n"
    
    # 🔥 Особые достижения (заглушка)
    text += "\n🔥 **Особые достижения:**\n"
    text += "   🔒 Просто повезло (0/2 подряд)\n"
    text += "   🔒 Серия побед (0/3 подряд)\n"
    text += "   🔒 Невозмутимый (0/5 подряд)\n"
    text += "\n💡 Серии побед будут добавлены позже!"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад в меню", callback_data="back_to_menu")
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()
