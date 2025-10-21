"""
Rate Limiter для защиты от превышения лимитов Telegram API
"""

import time
from typing import Dict
import asyncio
from aiogram import Bot


class RateLimiter:
    """Ограничитель частоты запросов к Telegram API"""
    
    def __init__(self):
        self.last_action: Dict[str, float] = {}
        self.intervals = {
            'message_edit': 60,    # 1 минута между редактированиями
            'message_send': 0.05,  # 50мс между отправками
        }
    
    async def wait_if_needed(self, action_type: str, key: str):
        """Подождать если нужно перед действием"""
        full_key = f"{action_type}_{key}"
        now = time.time()
        
        if full_key in self.last_action:
            elapsed = now - self.last_action[full_key]
            min_interval = self.intervals.get(action_type, 1)
            
            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                await asyncio.sleep(wait_time)
        
        self.last_action[full_key] = time.time()
    
    async def safe_edit_message(self, bot: Bot, chat_id: int, message_id: int, text: str, **kwargs):
        """Безопасное редактирование с rate limiting"""
        key = f"{chat_id}_{message_id}"
        await self.wait_if_needed('message_edit', key)
        
        try:
            return await bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=message_id,
                **kwargs
            )
        except Exception as e:
            print(f"❌ Ошибка редактирования: {e}")
            return None


# Глобальный экземпляр
rate_limiter = RateLimiter()

