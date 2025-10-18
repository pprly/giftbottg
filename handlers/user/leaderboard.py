"""
ТОП игроков (Лидерборды)
3 категории: рефералы, победы, активность
"""

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils import markdown
from database_postgres import db
import config

def escape_markdown(text: str) -> str:
    """Экранирует спецсимволы Markdown"""
    if not text:
        return text
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in chars:
        text = text.replace(char, '\\' + char)
    return text

router = Router()


async def check_user_subscription(bot: Bot, user_id: int) -> bool:
    """Проверка подписки пользователя на канал"""
    try:
        member = await bot.get_chat_member(chat_id=config.CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"⚠️ Ошибка проверки подписки для {user_id}: {e}")
        return False


async def get_user_info(bot: Bot, user_id: int) -> tuple[str, bool]:
    """
    Получить имя пользователя и статус подписки
    
    Returns:
        tuple (display_name, is_subscribed)
    """
    try:
        user = await bot.get_chat(user_id)
        
        # Формируем отображаемое имя
        if user.username:
            display_name = f"@{user.username}"
        else:
            display_name = user.first_name
        
        # Проверяем подписку
        is_subscribed = await check_user_subscription(bot, user_id)
        
        return (display_name, is_subscribed)
    except Exception as e:
        print(f"⚠️ Ошибка получения информации о пользователе {user_id}: {e}")
        return (f"User {user_id}", False)


@router.callback_query(F.data == "leaderboard")
async def show_leaderboard_menu(callback: CallbackQuery):
    """Главное меню лидербордов"""
    text = (
        "🔝 **ТОП ИГРОКОВ**\n\n"
        "Выберите категорию рейтинга:"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 ТОП по рефералам", callback_data="top_referrals")
    builder.button(text="🏆 ТОП по победам", callback_data="top_wins")
    builder.button(text="🎯 ТОП по активности", callback_data="top_contests")
    builder.button(text="🔙 Назад в меню", callback_data="back_to_menu")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "top_referrals")
async def show_top_referrals(callback: CallbackQuery):
    """ТОП по рефералам (только подписанные)"""
    user_id = callback.from_user.id
    
    # Получаем топ-20 (с запасом, т.к. будем фильтровать)
    top_users = await db.get_top_by_referrals(limit=20)
    
    if not top_users:
        text = "📊 **ТОП ПО РЕФЕРАЛАМ**\n\n❌ Пока нет данных"
    else:
        # Фильтруем только подписанных
        filtered_users = []
        for user in top_users:
            is_subscribed = await check_user_subscription(callback.bot, user['user_id'])
            if is_subscribed:
                user_name, _ = await get_user_info(callback.bot, user['user_id'])
                filtered_users.append({
                    'user_id': user['user_id'],
                    'name': user_name,
                    'points': user['referral_points']
                })
            
            # Останавливаемся когда набрали 10 подписанных
            if len(filtered_users) >= 10:
                break
        
        if not filtered_users:
            text = "📊 **ТОП ПО РЕФЕРАЛАМ**\n\n❌ Пока нет данных"
        else:
            text = "👥 **ТОП ПО РЕФЕРАЛАМ**\n\n"
            
            # Формируем топ-10
            for idx, user in enumerate(filtered_users, 1):
                # Эмодзи для топ-3
                if idx == 1:
                    emoji = "🥇"
                elif idx == 2:
                    emoji = "🥈"
                elif idx == 3:
                    emoji = "🥉"
                else:
                    emoji = f"{idx}."
                
                # Подсветка текущего пользователя
                if user['user_id'] == user_id:
                    text += f"**{emoji} {user['name']} — {user['points']} реф.**\n"
                else:
                    text += f"{emoji} {user['name']} — {user['points']} реф.\n"
            
            # Позиция текущего пользователя
            position, total = await db.get_user_position(user_id, 'referrals')
            
            # Проверяем подписан ли текущий пользователь
            user_subscribed = await check_user_subscription(callback.bot, user_id)
            
            if position > 0 and user_subscribed:
                text += f"\n━━━━━━━━━━━━━━━━\n"
                if position <= 10 and user_id in [u['user_id'] for u in filtered_users]:
                    text += f"📍 Вы в топ-10! Поздравляем! 🎉"
                else:
                    referral_count = await db.get_referral_count(user_id)
                    text += f"📍 **Ваша позиция:** {position} место\n"
                    text += f"👥 **Ваши рефералы:** {referral_count}"
            elif not user_subscribed:
                text += f"\n━━━━━━━━━━━━━━━━\n"
                text += "⚠️ Вы не подписаны на канал\n"
                text += "💡 Подпишитесь, чтобы попасть в рейтинг!"
            else:
                text += f"\n━━━━━━━━━━━━━━━━\n"
                text += "📍 У вас пока нет рефералов\n"
                text += "💡 Пригласите друзей, чтобы попасть в рейтинг!"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 К выбору категории", callback_data="leaderboard")
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "top_wins")
async def show_top_wins(callback: CallbackQuery):
    """ТОП по победам (только подписанные)"""
    user_id = callback.from_user.id
    
    # Получаем топ-20 (с запасом)
    top_users = await db.get_top_by_wins(limit=20)
    
    if not top_users:
        text = "📊 **ТОП ПО ПОБЕДАМ**\n\n❌ Пока нет данных"
    else:
        # Фильтруем только подписанных
        filtered_users = []
        for user in top_users:
            is_subscribed = await check_user_subscription(callback.bot, user['user_id'])
            if is_subscribed:
                user_name, _ = await get_user_info(callback.bot, user['user_id'])
                filtered_users.append({
                    'user_id': user['user_id'],
                    'name': user_name,
                    'wins': user['total_wins']
                })
            
            if len(filtered_users) >= 10:
                break
        
        if not filtered_users:
            text = "📊 **ТОП ПО ПОБЕДАМ**\n\n❌ Пока нет данных"
        else:
            text = "🏆 **ТОП ПО ПОБЕДАМ**\n\n"
            
            for idx, user in enumerate(filtered_users, 1):
                if idx == 1:
                    emoji = "🥇"
                elif idx == 2:
                    emoji = "🥈"
                elif idx == 3:
                    emoji = "🥉"
                else:
                    emoji = f"{idx}."
                
                if user['user_id'] == user_id:
                    text += f"**{emoji} {user['name']} — {user['wins']} побед**\n"
                else:
                    text += f"{emoji} {user['name']} — {user['wins']} побед\n"
            
            position, total = await db.get_user_position(user_id, 'wins')
            user_subscribed = await check_user_subscription(callback.bot, user_id)
            
            if position > 0 and user_subscribed:
                text += f"\n━━━━━━━━━━━━━━━━\n"
                if position <= 10 and user_id in [u['user_id'] for u in filtered_users]:
                    text += f"📍 Вы в топ-10! Поздравляем! 🎉"
                else:
                    stats = await db.get_user_stats(user_id)
                    text += f"📍 **Ваша позиция:** {position} место\n"
                    text += f"🏆 **Ваши победы:** {stats['total_wins']}"
            elif not user_subscribed:
                text += f"\n━━━━━━━━━━━━━━━━\n"
                text += "⚠️ Вы не подписаны на канал\n"
                text += "💡 Подпишитесь, чтобы попасть в рейтинг!"
            else:
                text += f"\n━━━━━━━━━━━━━━━━\n"
                text += "📍 У вас пока нет побед\n"
                text += "💡 Участвуйте в конкурсах, чтобы попасть в рейтинг!"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 К выбору категории", callback_data="leaderboard")
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "top_contests")
async def show_top_contests(callback: CallbackQuery):
    """ТОП по активности (только подписанные)"""
    user_id = callback.from_user.id
    
    # Получаем топ-20 (с запасом)
    top_users = await db.get_top_by_contests(limit=20)
    
    if not top_users:
        text = "📊 **ТОП ПО АКТИВНОСТИ**\n\n❌ Пока нет данных"
    else:
        # Фильтруем только подписанных
        filtered_users = []
        for user in top_users:
            is_subscribed = await check_user_subscription(callback.bot, user['user_id'])
            if is_subscribed:
                user_name, _ = await get_user_info(callback.bot, user['user_id'])
                filtered_users.append({
                    'user_id': user['user_id'],
                    'name': user_name,
                    'contests': user['total_contests']
                })
            
            if len(filtered_users) >= 10:
                break
        
        if not filtered_users:
            text = "📊 **ТОП ПО АКТИВНОСТИ**\n\n❌ Пока нет данных"
        else:
            text = "🎯 **ТОП ПО АКТИВНОСТИ**\n\n"
            
            for idx, user in enumerate(filtered_users, 1):
                if idx == 1:
                    emoji = "🥇"
                elif idx == 2:
                    emoji = "🥈"
                elif idx == 3:
                    emoji = "🥉"
                else:
                    emoji = f"{idx}."
                
                if user['user_id'] == user_id:
                    text += f"**{emoji} {user['name']} — {user['contests']} участий**\n"
                else:
                    text += f"{emoji} {user['name']} — {user['contests']} участий\n"
            
            position, total = await db.get_user_position(user_id, 'contests')
            user_subscribed = await check_user_subscription(callback.bot, user_id)
            
            if position > 0 and user_subscribed:
                text += f"\n━━━━━━━━━━━━━━━━\n"
                if position <= 10 and user_id in [u['user_id'] for u in filtered_users]:
                    text += f"📍 Вы в топ-10! Поздравляем! 🎉"
                else:
                    stats = await db.get_user_stats(user_id)
                    text += f"📍 **Ваша позиция:** {position} место\n"
                    text += f"🎯 **Ваши участия:** {stats['total_contests']}"
            elif not user_subscribed:
                text += f"\n━━━━━━━━━━━━━━━━\n"
                text += "⚠️ Вы не подписаны на канал\n"
                text += "💡 Подпишитесь, чтобы попасть в рейтинг!"
            else:
                text += f"\n━━━━━━━━━━━━━━━━\n"
                text += "📍 Вы ещё не участвовали в конкурсах\n"
                text += "💡 Примите участие, чтобы попасть в рейтинг!"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 К выбору категории", callback_data="leaderboard")
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()
