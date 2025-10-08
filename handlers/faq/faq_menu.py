"""
Главное меню FAQ
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


router = Router()


@router.callback_query(F.data == "how_to_participate")
async def show_faq_menu(callback: CallbackQuery):
    """
    Главное меню FAQ
    """
    text = (
        "❓ **КАК УЧАСТВОВАТЬ**\n\n"
        "Выберите интересующий раздел:"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Виды конкурсов", callback_data="faq_contest_types")
    builder.button(text="👥 Реферальная программа", callback_data="faq_referral")
    builder.button(text="📞 Связь с админом", callback_data="faq_contact")
    builder.button(text="🔙 Назад в меню", callback_data="back_to_menu")
    builder.adjust(2, 1, 1)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()
