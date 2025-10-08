"""
Гибкая система фильтрации участников конкурсов
Поддержка множественных условий участия + диапазон участий (min/max)
"""

from database_postgres import db
from typing import Dict, Any


class ParticipantFilter:
    """
    Класс для проверки условий участия в конкурсах
    """
    
    @staticmethod
    async def check_min_referrals(user_id: int, min_count: int) -> bool:
        """
        Проверка минимального количества рефералов
        
        Args:
            user_id: ID пользователя
            min_count: Минимальное количество рефералов
            
        Returns:
            True если у пользователя >= min_count рефералов
        """
        count = await db.get_referral_count(user_id)
        return count >= min_count
    
    @staticmethod
    async def check_min_contests(user_id: int, min_count: int) -> bool:
        """
        Проверка минимального количества участий в конкурсах
        
        Args:
            user_id: ID пользователя
            min_count: Минимальное количество участий
            
        Returns:
            True если пользователь участвовал >= min_count раз
        """
        stats = await db.get_user_stats(user_id)
        return stats['total_contests'] >= min_count
    
    @staticmethod
    async def check_max_contests(user_id: int, max_count: int) -> bool:
        """
        Проверка максимального количества участий в конкурсах
        
        Args:
            user_id: ID пользователя
            max_count: Максимальное количество участий
            
        Returns:
            True если пользователь участвовал <= max_count раз
        """
        stats = await db.get_user_stats(user_id)
        return stats['total_contests'] <= max_count
    
    @staticmethod
    async def check_conditions(user_id: int, conditions: Dict[str, Any]) -> tuple[bool, tuple]:
        """
        Проверка комбинации условий участия
        
        Args:
            user_id: ID пользователя
            conditions: Словарь с условиями, например:
                {
                    'first_n': 10,
                    'min_referrals': 5,
                    'min_contests': 3,
                    'max_contests': 10
                }
        
        Returns:
            tuple (bool, tuple): (успех, (тип_ошибки, требуемое, текущее) если неуспех)
        """
        # Получаем статистику один раз для оптимизации
        stats = await db.get_user_stats(user_id)
        user_contests = stats['total_contests']
        
        # Проверка минимального количества рефералов
        if 'min_referrals' in conditions:
            min_refs = conditions['min_referrals']
            if not await ParticipantFilter.check_min_referrals(user_id, min_refs):
                current = await db.get_referral_count(user_id)
                return False, ("min_referrals", min_refs, current)
        
        # Проверка минимального количества участий
        if 'min_contests' in conditions:
            min_contests = conditions['min_contests']
            if user_contests < min_contests:
                return False, ("min_contests", min_contests, user_contests)
        
        # Проверка максимального количества участий
        if 'max_contests' in conditions:
            max_contests = conditions['max_contests']
            if user_contests > max_contests:
                return False, ("max_contests", max_contests, user_contests)
        
        # Все условия выполнены
        return True, ()
    
    @staticmethod
    def format_conditions(conditions: Dict[str, Any]) -> str:
        """
        Форматирование условий для отображения в анонсе
        
        Args:
            conditions: Словарь с условиями
            
        Returns:
            Отформатированная строка с условиями
        """
        parts = []
        
        if 'first_n' in conditions:
            parts.append(f"👥 Первые {conditions['first_n']} человек")
        
        if 'min_referrals' in conditions:
            parts.append(f"🔗 Минимум {conditions['min_referrals']} рефералов")
        
        # Умное форматирование диапазона участий
        has_min = 'min_contests' in conditions
        has_max = 'max_contests' in conditions
        
        if has_min and has_max:
            # Диапазон: от X до Y
            min_c = conditions['min_contests']
            max_c = conditions['max_contests']
            parts.append(f"🎯 От {min_c} до {max_c} участий")
        elif has_min:
            # Только минимум
            parts.append(f"🎯 Минимум {conditions['min_contests']} участий")
        elif has_max:
            # Только максимум (новички!)
            max_c = conditions['max_contests']
            if max_c == 0:
                parts.append(f"🆕 Только новички (0 участий)")
            elif max_c == 1:
                parts.append(f"🆕 Только новички (0-1 участие)")
            else:
                parts.append(f"🎯 Максимум {max_c} участий")
        
        if conditions.get('all_subscribers', False):
            parts.append("📢 Все подписчики канала")
        
        return "\n".join(f"• {part}" for part in parts) if parts else "• Написать комментарий"