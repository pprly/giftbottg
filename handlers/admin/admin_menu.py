"""
Главное меню админ-панели
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import config
from database_postgres import db


router = Router()


def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id == config.ADMIN_ID


async def show_admin_menu(callback: CallbackQuery):
    """Показать админ-панель"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🎲 Создать конкурс", callback_data="create_contest")
    builder.button(text="📊 Активные конкурсы", callback_data="active_contests")
    builder.button(text="🛑 Отменить конкурс", callback_data="cancel_contest")
    builder.button(text="📈 Статистика", callback_data="admin_stats")
    builder.button(text="🔙 В главное меню", callback_data="back_to_menu")
    builder.adjust(2, 1, 1, 1)
    
    await callback.message.edit_text(
        config.MESSAGES["start_admin"],
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(Command("chatid"))
async def get_chat_id(message: Message):
    """Команда для получения ID чата (для настройки)"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        f"ℹ️ **Информация о чате:**\n\n"
        f"ID чата: `{message.chat.id}`\n"
        f"Тип: {message.chat.type}\n"
        f"Username: @{message.chat.username if message.chat.username else 'нет'}",
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "active_contests")
async def show_active_contests(callback: CallbackQuery):
    """Показать ВСЕ активные конкурсы"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа!", show_alert=True)
        return
    
    contests = await db.get_active_contests()
    
    if not contests:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Назад", callback_data="admin_panel")
        
        await callback.message.edit_text(
            "ℹ️ Нет активных конкурсов",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        return
    
    text = f"📥 **АКТИВНЫЕ КОНКУРСЫ** ({len(contests)})\n\n"
    
    for contest in contests:
        # Форматируем условия участия
        entry_conditions = contest.get('entry_conditions', {})
        conditions_text = ""
        
        if 'first_n' in entry_conditions:
            conditions_text += f"• Первые {entry_conditions['first_n']} человек\n"
        if 'min_referrals' in entry_conditions:
            conditions_text += f"• Минимум {entry_conditions['min_referrals']} рефералов\n"
        if 'min_contests' in entry_conditions:
            conditions_text += f"• Минимум {entry_conditions['min_contests']} участий\n"
        if entry_conditions.get('all_subscribers'):
            conditions_text += "• Все подписчики канала\n"
        
        if not conditions_text:
            conditions_text = "• Написать комментарий\n"
        
        participants_count = await db.get_participants_count(contest['id'])
        
        text += f"━━━━━━━━━━━━━━━━\n"
        text += f"🆔 **Конкурс #{contest['id']}**\n"
        text += f"🎁 Приз: {contest['prize']}\n"
        text += f"📝 Тип: {config.CONTEST_TYPES.get(contest['contest_type'], {}).get('name', contest['contest_type'])}\n"
        text += f"📊 Статус: {contest['status']}\n"
        text += f"👥 Участников: {participants_count}/{contest['participants_count']}\n"
        text += f"⏰ Таймер: {contest['timer_minutes']} мин\n\n"
    
    text += "━━━━━━━━━━━━━━━━"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="admin_panel")
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def show_admin_stats(callback: CallbackQuery):
    """Показать статистику (заглушка)"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа!", show_alert=True)
        return
    
    text = (
        "📈 **СТАТИСТИКА**\n\n"
        "🚧 Раздел в разработке!\n\n"
        "Скоро здесь появится:\n"
        "• Общее количество конкурсов\n"
        "• Общее количество участников\n"
        "• Статистика по типам конкурсов\n"
        "• ТОП самых активных пользователей\n"
        "• График активности"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="admin_panel")
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_contest")
async def cancel_contest_menu(callback: CallbackQuery):
    """Меню выбора конкурса для отмены"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа!", show_alert=True)
        return
    
    # Получаем ВСЕ активные конкурсы
    contests = await db.get_active_contests()
    
    if not contests:
        await callback.answer("ℹ️ Нет активных конкурсов для отмены", show_alert=True)
        return
    
    # Если конкурс один - показываем подтверждение сразу
    if len(contests) == 1:
        contest = contests[0]
        participants_count = await db.get_participants_count(contest['id'])
        
        text = (
            "⚠️ **ОТМЕНА КОНКУРСА**\n\n"
            f"🆔 ID: {contest['id']}\n"
            f"🎁 Приз: {contest['prize']}\n"
            f"📊 Статус: {contest['status']}\n"
            f"👥 Участников: {participants_count}/{contest['participants_count']}\n\n"
            "❗️ Вы уверены что хотите отменить этот конкурс?\n\n"
            "⚠️ **Это действие необратимо!**\n"
            "• Конкурс будет помечен как 'ended'\n"
            "• Уведомление будет отправлено в канал\n"
            "• Данные участников сохранятся в БД"
        )
        
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Да, отменить", callback_data=f"confirm_cancel_{contest['id']}")
        builder.button(text="❌ Нет, вернуться", callback_data="admin_panel")
        builder.adjust(1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    # Если конкурсов несколько - показываем список для выбора
    text = f"🛑 **ОТМЕНА КОНКУРСА**\n\n"
    text += f"Активных конкурсов: **{len(contests)}**\n\n"
    text += "Выберите конкурс для отмены:\n\n"
    
    builder = InlineKeyboardBuilder()
    
    for contest in contests:
        participants_count = await db.get_participants_count(contest['id'])
        button_text = f"#{contest['id']}: {contest['prize'][:20]} ({participants_count} уч.)"
        builder.button(text=button_text, callback_data=f"select_cancel_{contest['id']}")
    
    builder.button(text="🔙 Назад", callback_data="admin_panel")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("select_cancel_"))
async def select_contest_to_cancel(callback: CallbackQuery):
    """Показать подтверждение для выбранного конкурса"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа!", show_alert=True)
        return
    
    # Извлекаем ID конкурса
    contest_id = int(callback.data.replace("select_cancel_", ""))
    
    # Получаем конкурс
    contest = await db.get_contest_by_id(contest_id)
    
    if not contest:
        await callback.answer("❌ Конкурс не найден", show_alert=True)
        return
    
    participants_count = await db.get_participants_count(contest['id'])
    
    text = (
        "⚠️ **ОТМЕНА КОНКУРСА**\n\n"
        f"🆔 ID: {contest['id']}\n"
        f"🎁 Приз: {contest['prize']}\n"
        f"📊 Статус: {contest['status']}\n"
        f"👥 Участников: {participants_count}/{contest['participants_count']}\n\n"
        "❗️ Вы уверены что хотите отменить этот конкурс?\n\n"
        "⚠️ **Это действие необратимо!**\n"
        "• Конкурс будет помечен как 'ended'\n"
        "• Уведомление будет отправлено в канал\n"
        "• Данные участников сохранятся в БД"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, отменить", callback_data=f"confirm_cancel_{contest['id']}")
    builder.button(text="🔙 К списку конкурсов", callback_data="cancel_contest")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_cancel_"))
async def confirm_cancel_contest(callback: CallbackQuery):
    """Подтверждение отмены конкурса"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа!", show_alert=True)
        return
    
    # Извлекаем ID конкурса
    contest_id = int(callback.data.replace("confirm_cancel_", ""))
    
    # Получаем конкурс
    contest = await db.get_contest_by_id(contest_id)
    
    if not contest:
        await callback.answer("❌ Конкурс не найден", show_alert=True)
        return
    
    # Проверяем что конкурс активный
    if contest['status'] == 'ended':
        await callback.answer("ℹ️ Конкурс уже завершён", show_alert=True)
        return
    
    # Меняем статус на 'ended'
    await db.update_contest_status(contest_id, 'ended')
    
    # Отправляем уведомление в канал
    try:
        await callback.bot.send_message(
            chat_id=config.CHANNEL_ID,
            text=(
                f"⚠️ **КОНКУРС #{contest_id} ОТМЕНЁН**\n\n"
                f"🎁 Приз: {contest['prize']}\n\n"
                "Конкурс был отменён администратором.\n"
                "Следите за новыми анонсами!"
            ),
            parse_mode="Markdown"
        )
        print(f"✅ Уведомление об отмене конкурса #{contest_id} опубликовано в канале")
    except Exception as e:
        print(f"⚠️ Не удалось опубликовать уведомление: {e}")
    
    # Уведомляем админа
    text = (
        "✅ **КОНКУРС ОТМЕНЁН**\n\n"
        f"🆔 ID: {contest_id}\n"
        f"🎁 Приз: {contest['prize']}\n\n"
        "Конкурс успешно завершён со статусом 'ended'.\n"
        "Уведомление опубликовано в канале."
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 В админ-панель", callback_data="admin_panel")
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()
