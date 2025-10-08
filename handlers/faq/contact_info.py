"""
Контактная информация
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import config


router = Router()


@router.callback_query(F.data == "faq_contact")
async def show_contact_info(callback: CallbackQuery):
    """
    Контактная информация
    """
    admin_username = config.ADMIN_USERNAME
    
    text = (
        "📞 <b>СВЯЗЬ С АДМИНОМ</b>\n\n"
        
        f"<b>Администратор:</b> @{admin_username}\n\n"
        
        "<b>По каким вопросам писать:</b>\n"
        "• Проблемы с ботом\n"
        "• Вопросы о конкурсах\n"
        "• Предложения и идеи\n"
        "• Технические проблемы\n"
        "• Жалобы на нарушения\n\n"
        
        "<b>Официальные ресурсы:</b>\n"
        "• Канал: @tgstarsdrops\n"
        "• Бот: @Zazvezdilsya_bot\n\n"
        
        "⚠️ Админ отвечает в течение 24 часов"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад к FAQ", callback_data="how_to_participate")
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()
