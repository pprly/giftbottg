"""
Автоматическое принятие заявок на вступление в канал и группу
"""

from aiogram import Router, F
from aiogram.types import ChatJoinRequest
import config


router = Router()


@router.chat_join_request(F.chat.id == config.CHANNEL_ID)
async def approve_channel_request(join_request: ChatJoinRequest):
    """
    Автоматическое принятие заявок в канал
    """
    if not config.AUTO_APPROVE_ENABLED:
        return
    
    try:
        # Принимаем заявку
        await join_request.approve()
        
        print(f"✅ Принята заявка в КАНАЛ от @{join_request.from_user.username} "
              f"(ID: {join_request.from_user.id})")
        
    except Exception as e:
        print(f"❌ Ошибка принятия заявки в канал от {join_request.from_user.id}: {e}")


@router.chat_join_request(F.chat.id == config.DISCUSSION_GROUP_ID)
async def approve_group_request(join_request: ChatJoinRequest):
    """
    Автоматическое принятие заявок в группу обсуждений
    """
    if not config.AUTO_APPROVE_ENABLED:
        return
    
    try:
        # Принимаем заявку
        await join_request.approve()
        
        print(f"✅ Принята заявка в ГРУППУ от @{join_request.from_user.username} "
              f"(ID: {join_request.from_user.id})")
        
    except Exception as e:
        print(f"❌ Ошибка принятия заявки в группу от {join_request.from_user.id}: {e}")
