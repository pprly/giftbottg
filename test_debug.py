"""
Временный файл для отладки - показывает ВСЕ сообщения
"""

from aiogram import Router
from aiogram.types import Message

router = Router()

@router.message()
async def debug_all_messages(message: Message):
    """Показывает информацию о ВСЕХ сообщениях"""
    print("\n" + "="*60)
    print("🔍 DEBUG: ПОЛУЧЕНО СООБЩЕНИЕ")
    print("="*60)
    print(f"Chat ID: {message.chat.id}")
    print(f"Chat Type: {message.chat.type}")
    print(f"Chat Title: {message.chat.title}")
    print(f"From: @{message.from_user.username} (ID: {message.from_user.id})")
    print(f"Text: {message.text}")
    print(f"Message ID: {message.message_id}")
    print(f"Date: {message.date}")
    print("="*60 + "\n")