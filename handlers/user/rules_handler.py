from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def start_with_rules(message: Message):
    """Обработка deep link с правилами"""
    
    # Проверяем есть ли параметр
    args = message.text.split(maxsplit=1)
    
    if len(args) > 1 and args[1] == "rules":
        # Пользователь пришёл из канала
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
    
    # Обычный /start - передаём дальше в main_menu
    # (не обрабатываем здесь)