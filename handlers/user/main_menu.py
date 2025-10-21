"""
Главное меню для пользователей
Первый экран при /start
"""

from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo
import config


router = Router()


def get_main_menu_keyboard(user_id: int):
    """
    Создание клавиатуры главного меню
    Разная для админа и обычных пользователей
    """
    builder = InlineKeyboardBuilder()
    
    # 🆕 ГЛАВНАЯ КНОПКА - Открыть Mini App
    builder.button(
        text="🚀 Открыть приложение",
        web_app=WebAppInfo(url="https://pprly.github.io/giftbottg/")
    )
    
    # Основные кнопки для всех
    builder.button(text="📊 Моя статистика", callback_data="my_stats")
    builder.button(text="🏆 Достижения", callback_data="achievements")
    builder.button(text="🔝 ТОП игроков", callback_data="leaderboard")
    builder.button(text="❓ Как участвовать", callback_data="how_to_participate")
    
    # Админ-панель только для админа
    if user_id == config.ADMIN_ID:
        builder.button(text="👑 Админ-панель", callback_data="admin_panel")
    
    # Настройка расположения кнопок
    if user_id == config.ADMIN_ID:
        builder.adjust(1, 2, 2, 1, 1)  # WebApp отдельно, потом 2-2-1-1
    else:
        builder.adjust(1, 2, 2, 1)  # WebApp отдельно, потом 2-2-1
    
    return builder.as_markup()


@router.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject):
    """
    Команда /start - главное меню или реферальный флоу
    """
    user_id = message.from_user.id
    
    # Получаем аргументы команды правильно
    args = command.args  # ← ИСПРАВЛЕНО: используем CommandObject
    
    # Проверяем реферальную ссылку
    if args and args.startswith("ref_"):
        # Это реферальный переход - обрабатываем в referral.py
        from handlers.user.referral import handle_referral_link
        await handle_referral_link(message, args)
        return
    
    # Обычное главное меню
    await show_main_menu(message)


async def show_main_menu(message: Message):
    """
    Показать главное меню
    """
    user_id = message.from_user.id
    
    await message.answer(
        config.MESSAGES["start_user"],
        reply_markup=get_main_menu_keyboard(user_id),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """
    Вернуться в главное меню
    """
    await callback.message.edit_text(
        config.MESSAGES["start_user"],
        reply_markup=get_main_menu_keyboard(callback.from_user.id),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: CallbackQuery):
    """
    Переход в админ-панель
    """
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔️ У вас нет доступа!", show_alert=True)
        return
    
    # Импортируем функцию из admin.py
    from handlers.admin.admin_menu import show_admin_menu
    await show_admin_menu(callback)

@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """Показать главное меню через callback"""
    await show_main_menu(callback.message)
    await callback.answer()
