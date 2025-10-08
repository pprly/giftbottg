"""
Выбор победителя конкурса
Команда /win {номер}
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
import config
from database_postgres import db


router = Router()


def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id == config.ADMIN_ID


@router.message(Command("win"))
async def select_winner(message: Message):
    """Команда выбора победителя: /win 5"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.answer(
                "❌ Неверный формат! Используйте: `/win {номер_участника}`\n"
                "Например: `/win 3`",
                parse_mode="Markdown"
            )
            return
        
        position = int(parts[1])
        
        # Получаем последний завершённый конкурс
        contest = await db.get_last_ended_contest()
        
        if not contest:
            await message.answer("❌ Нет завершённых конкурсов!")
            return
        
        # Получаем победителя по номеру
        winner = await db.get_participant_by_position(contest['id'], position)
        
        if not winner:
            await message.answer(f"❌ Участник под номером {position} не найден!")
            return
        
        # Сохраняем победителя в БД
        await db.set_contest_winner(contest['id'], winner['user_id'])
        print(f"💾 Победитель сохранён: user_id={winner['user_id']}")
        
        # Увеличиваем счётчик побед в статистике
        await db.increment_user_wins(winner['user_id'], contest['contest_type'])
        
        # Проверяем достижения за победу
        from handlers.user.achievements import check_achievements
        await check_achievements(message.bot, winner['user_id'])
        
        # Публикуем пост с победителем
        emoji = winner['comment_text']
        text = "🏆 **КОНКУРС ЗАВЕРШЁН!**\n\n"
        text += f"🎊 **Победитель:** {position} {emoji} [{winner['full_name']}](tg://user?id={winner['user_id']})\n\n"
        text += f"🎁 **Приз:** {contest['prize']}\n\n"
        text += "Поздравляем победителя! 🎉"
        
        await message.bot.send_message(
            chat_id=config.CHANNEL_ID,
            text=text,
            parse_mode="Markdown"
        )
        
        await message.answer("✅ Пост с победителем опубликован!")
        
    except ValueError:
        await message.answer("❌ Введите число! Например: `/win 3`", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        print(f"❌ Ошибка выбора победителя: {e}")
