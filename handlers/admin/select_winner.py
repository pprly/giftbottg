"""
Выбор победителя конкурса
Команда /win {номер} или /win {номер1} {номер2} ...
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
import config
from database_postgres import db


router = Router()


def escape_markdown(text: str) -> str:
    """Экранирует спецсимволы Markdown"""
    if not text:
        return text
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in chars:
        text = text.replace(char, '\\' + char)
    return text


def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id == config.ADMIN_ID


@router.message(Command("win"))
async def select_winner(message: Message):
    """Команда выбора победителя: /win 5 или /win 3 5 7"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer(
                "❌ Неверный формат! Используйте:\n"
                "`/win {номер}` — один победитель\n"
                "`/win {номер1} {номер2}` — несколько победителей\n\n"
                "Например: `/win 3` или `/win 3 5`",
                parse_mode="Markdown"
            )
            return
        
        # Парсим все номера позиций
        positions = []
        for part in parts[1:]:
            try:
                pos = int(part)
                if pos not in positions:  # Избегаем дубликатов
                    positions.append(pos)
            except ValueError:
                await message.answer(f"❌ '{part}' не является числом!")
                return
        
        if not positions:
            await message.answer("❌ Не указаны номера участников!")
            return
        
        # Получаем последний завершённый конкурс
        contest = await db.get_last_ended_contest()
        
        if not contest:
            await message.answer("❌ Нет завершённых конкурсов!")
            return
        
        # Собираем всех победителей
        winners = []
        for position in positions:
            winner = await db.get_participant_by_position(contest['id'], position)
            
            if not winner:
                await message.answer(f"❌ Участник под номером {position} не найден!")
                return
            
            winners.append(winner)
        
        # Сохраняем всех победителей в БД
        for winner in winners:
            await db.set_contest_winner(contest['id'], winner['user_id'])
            print(f"💾 Победитель сохранён: user_id={winner['user_id']}")
            
            # Увеличиваем счётчик побед
            await db.increment_user_wins(winner['user_id'], contest['contest_type'])
            
            # Проверяем достижения
            from handlers.user.achievements import check_achievements
            await check_achievements(message.bot, winner['user_id'])
        
        # Формируем пост с победителем/победителями
        if len(winners) == 1:
            # Один победитель
            winner = winners[0]
            emoji = winner['comment_text']
            position = positions[0]
            
            text = "🏆 **КОНКУРС ЗАВЕРШЁН!**\n\n"
            text += f"🎊 **Победитель:** {position} {emoji} [{escape_markdown(winner['full_name'])}](tg://user?id={winner['user_id']})\n\n"
            text += f"🎁 **Приз:** {escape_markdown(contest['prize'])}\n\n"
            text += "Поздравляем победителя! 🎉"
        else:
            # Несколько победителей
            text = "🏆 **КОНКУРС ЗАВЕРШЁН!**\n\n"
            text += f"🎁 **Приз:** {escape_markdown(contest['prize'])}\n\n"
            text += "🎊 **Победители:**\n"
            
            for i, winner in enumerate(winners):
                emoji = winner['comment_text']
                position = positions[i]
                text += f"{position} {emoji} [{escape_markdown(winner['full_name'])}](tg://user?id={winner['user_id']})\n"
            
            text += "\nПоздравляем победителей! 🎉"
        
        # Публикуем в канал
        await message.bot.send_message(
            chat_id=config.CHANNEL_ID,
            text=text,
            parse_mode="Markdown"
        )
        
        if len(winners) == 1:
            await message.answer("✅ Пост с победителем опубликован!")
        else:
            await message.answer(f"✅ Пост с {len(winners)} победителями опубликован!")
        
    except ValueError:
        await message.answer("❌ Введите число! Например: `/win 3` или `/win 3 5`", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        print(f"❌ Ошибка выбора победителя: {e}")
        import traceback
        traceback.print_exc()