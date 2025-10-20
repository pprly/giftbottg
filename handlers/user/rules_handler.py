from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command
from aiogram.filters.command import CommandObject

router = Router()

@router.message(Command("start"))
async def start_with_rules(message: Message, command: CommandObject):
    """Обработка deep link с правилами"""
    
    # Получаем аргументы
    args = command.args
    
    # Если пришли с параметром rules
    if args == "rules":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="📖 Открыть полные правила",
                web_app=WebAppInfo(url="https://pprly.github.io/giftbottg/rules.html")
            )],
            [InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )]
        ])
        
        await message.answer(
            "👋 **Добро пожаловать!**\n\n"
            "Нажмите кнопку ниже, чтобы открыть полные правила конкурсов.\n\n"
            "📊 В будущем здесь появится:\n"
            "• Статистика конкурсов\n"
            "• Турнирная сетка\n"
            "• Личный кабинет",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        return
    
    # Если НЕ rules - передаём в main_menu
    from handlers.user.main_menu import cmd_start
    await cmd_start(message, command)