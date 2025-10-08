"""
Реферальная система
Обработка переходов по реферальным ссылкам
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import config
from database_postgres import db


router = Router()


async def handle_referral_link(message: Message, ref_code: str):
    """
    Обработка перехода по реферальной ссылке
    
    Args:
        message: Сообщение от пользователя
        ref_code: Код вида "ref_123456"
    """
    try:
        # Извлекаем ID пригласившего из ref_123456
        referrer_id = int(ref_code.split("_")[1])
        referred_id = message.from_user.id
        
        # Нельзя пригласить самого себя
        if referrer_id == referred_id:
            await message.answer(
                "⚠️ Вы не можете использовать свою собственную реферальную ссылку!"
            )
            from handlers.user.main_menu import show_main_menu
            await show_main_menu(message)
            return
        
        # Проверяем был ли уже приглашён кем-то
        existing_referrer = await db.check_referral_exists(referred_id)
        if existing_referrer:
            await message.answer(
                "ℹ️ Вы уже зарегистрированы в системе!"
            )
            from handlers.user.main_menu import show_main_menu
            await show_main_menu(message)
            return
        
        # Добавляем реферала
        added = await db.add_referral(referrer_id, referred_id)
        
        if added:
            # Получаем информацию о пригласившем
            try:
                referrer_info = await message.bot.get_chat(referrer_id)
                referrer_name = referrer_info.first_name
            except:
                referrer_name = "пользователь"
            
            builder = InlineKeyboardBuilder()
            builder.button(text="📢 Подписаться на канал", url=config.CHANNEL_INVITE_LINK)
            builder.button(text="✅ Я подписался", callback_data=f"check_subscription_{referrer_id}")
            builder.adjust(1)
            
            await message.answer(
                config.MESSAGES["referral_welcome"].format(referrer_name=referrer_name),
                reply_markup=builder.as_markup()
            )
        else:
            from handlers.user.main_menu import show_main_menu
            await show_main_menu(message)
            
    except Exception as e:
        print(f"❌ Ошибка обработки реферальной ссылки: {e}")
        await message.answer("⚠️ Неверная реферальная ссылка")
        from handlers.user.main_menu import show_main_menu
        await show_main_menu(message)


@router.callback_query(F.data.startswith("check_subscription_"))
async def check_subscription(callback: CallbackQuery):
    """
    Проверить подписку после реферального перехода
    """
    # Извлекаем ID пригласившего
    referrer_id = int(callback.data.split("_")[2])
    referred_id = callback.from_user.id
    
    # Проверяем подписку
    try:
        member = await callback.bot.get_chat_member(
            chat_id=config.CHANNEL_ID, 
            user_id=referred_id
        )
        is_subscribed = member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"❌ Ошибка проверки подписки: {e}")
        is_subscribed = False
    
    if is_subscribed:
        # Начисляем очко рефереру
        await db.mark_referral_subscribed(referrer_id, referred_id)
        
        # Проверяем достижения рефера
        from handlers.user.achievements import check_achievements
        await check_achievements(callback.bot, referrer_id)
        
        # Уведомляем реферера
        try:
            await callback.bot.send_message(
                referrer_id,
                config.MESSAGES["new_referral"].format(
                    name=callback.from_user.first_name
                )
            )
        except:
            pass
        
        # Показываем главное меню
        from handlers.user.main_menu import get_main_menu_keyboard
        
        await callback.message.edit_text(
            config.MESSAGES["referral_success"],
            reply_markup=get_main_menu_keyboard(referred_id)
        )
    else:
        await callback.answer(
            "⚠️ Вы ещё не подписались на канал! Подпишитесь и попробуйте снова.",
            show_alert=True
        )
    
    await callback.answer()
