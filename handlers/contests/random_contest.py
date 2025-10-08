"""
Рандомайзер конкурс (Random Contest)
Автоматический случайный выбор победителя
"""

import asyncio
import random
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message
import config
from database_postgres import db
from utils.filters import ParticipantFilter
from utils.formatters import format_participant_list


router = Router()

# Глобальный словарь для хранения активных задач (используем общий из voting_contest)
from handlers.contests.voting_contest import active_tasks


async def publish_random_contest_announcement(bot: Bot, contest_id: int):
    """Публикация анонса рандомайзера в канале"""
    contest = await db.get_contest_by_id(contest_id)
    if not contest:
        print("❌ Активный конкурс не найден")
        return
    
    # Форматируем условия участия
    entry_conditions = contest.get('entry_conditions', {})
    conditions_text = ParticipantFilter.format_conditions(entry_conditions)
    
    text = (
        f"🎰 **РАНДОМАЙЗЕР!**\n\n"
        f"🎁 Приз: {contest['prize']}\n\n"
        f"📝 **Условия участия:**\n"
        f"{contest['conditions']}\n\n"
        f"**Фильтры:**\n"
        f"{conditions_text}\n\n"
        f"⏰ Время сбора: {contest['timer_minutes']} мин\n"
        f"🎲 После набора — автоматический розыгрыш!"
    )
    
    try:
        message = await bot.send_message(
            chat_id=config.CHANNEL_ID,
            text=text,
            parse_mode="Markdown"
        )
        
        await db.set_announcement_message(contest_id, message.message_id)
        
        print(f"✅ [{contest_id}] Анонс рандомайзера опубликован! Message ID: {message.message_id}")
        
        # Запускаем сбор участников с сохранением задачи
        task = asyncio.create_task(collect_random_participants(bot, contest_id))
        active_tasks[f"collect_{contest_id}"] = task
        
    except Exception as e:
        print(f"❌ [{contest_id}] Ошибка публикации анонса: {e}")


async def collect_random_participants(bot: Bot, contest_id: int):
    """Фоновая задача сбора участников для рандомайзера"""
    task_key = f"collect_{contest_id}"
    
    try:
        contest = await db.get_contest_by_id(contest_id)
        if not contest:
            print(f"❌ [{contest_id}] Конкурс не найден при сборе участников")
            return
        
        print(f"🔄 [{contest_id}] Начат сбор участников для рандомайзера")
        
        # Ждём указанное время ИЛИ пока не наберём нужное количество
        start_time = datetime.now()
        timeout_minutes = contest['timer_minutes']
        
        while True:
            # Проверяем не отменена ли задача
            if task_key not in active_tasks:
                print(f"⛔ [{contest_id}] Задача сбора участников отменена")
                break
            
            try:
                current_count = await db.get_participants_count(contest_id)
                needed_count = contest['participants_count']
                
                # Проверяем набралось ли нужное количество
                if current_count >= needed_count:
                    print(f"✅ [{contest_id}] Собрано {current_count} участников!")
                    await db.update_contest_status(contest_id, 'voting')
                    
                    # Запускаем розыгрыш
                    await select_random_winner(bot, contest_id)
                    
                    # Удаляем задачу из активных
                    if task_key in active_tasks:
                        del active_tasks[task_key]
                    break
                
                # Проверяем не истекло ли время
                elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60
                if elapsed_minutes >= timeout_minutes:
                    print(f"⏰ [{contest_id}] Время вышло! Собрано {current_count} участников")
                    
                    if current_count > 0:
                        await db.update_contest_status(contest_id, 'voting')
                        await select_random_winner(bot, contest_id)
                    else:
                        print(f"❌ [{contest_id}] Нет участников, конкурс отменяется")
                        await db.update_contest_status(contest_id, 'ended')
                    
                    # Удаляем задачу из активных
                    if task_key in active_tasks:
                        del active_tasks[task_key]
                    break
                
                print(f"📊 [{contest_id}] Собрано {current_count}/{needed_count} участников (прошло {int(elapsed_minutes)} мин)")
                
                await asyncio.sleep(config.COMMENT_CHECK_INTERVAL)
                
            except Exception as e:
                print(f"❌ [{contest_id}] Ошибка при сборе участников: {e}")
                await asyncio.sleep(5)
    
    except asyncio.CancelledError:
        print(f"⛔ [{contest_id}] Задача сбора участников была отменена")
        if task_key in active_tasks:
            del active_tasks[task_key]
    except Exception as e:
        print(f"❌ [{contest_id}] Критическая ошибка в сборе участников: {e}")
        if task_key in active_tasks:
            del active_tasks[task_key]


async def select_random_winner(bot: Bot, contest_id: int):
    """Выбор случайного победителя"""
    contest = await db.get_contest_by_id(contest_id)
    participants = await db.get_participants(contest_id)
    
    if not participants:
        print(f"❌ [{contest_id}] Нет участников для розыгрыша")
        await db.update_contest_status(contest_id, 'ended')
        return
    
    print(f"🎲 [{contest_id}] Выбираем случайного победителя из {len(participants)} участников")
    
    # 🎰 СЛУЧАЙНЫЙ ВЫБОР
    winner = random.choice(participants)
    
    print(f"🏆 [{contest_id}] Победитель: {winner['position']} {winner['comment_text']} — @{winner['username']}")
    
    # Удаляем старый анонс
    old_announcement_id = contest.get('announcement_message_id')
    if old_announcement_id:
        try:
            await bot.delete_message(
                chat_id=config.CHANNEL_ID,
                message_id=old_announcement_id
            )
            print(f"🗑️ [{contest_id}] Старый анонс удалён")
        except Exception as e:
            print(f"⚠️ [{contest_id}] Не удалось удалить анонс: {e}")
    
    # Публикуем результат в канале
    winner_name = f"@{winner['username']}" if winner['username'] != "noname" else winner['full_name']
    
    text = (
        f"🎰 **РОЗЫГРЫШ ЗАВЕРШЁН!**\n\n"
        f"👥 Участников: {len(participants)}\n\n"
        f"🎉 **ПОБЕДИТЕЛЬ:**\n"
        f"{winner['position']} {winner['comment_text']} — [{winner_name}](tg://user?id={winner['user_id']})\n\n"
        f"🎁 **Приз:** {contest['prize']}\n\n"
        f"Поздравляем! 🎊"
    )
    
    try:
        await bot.send_message(
            chat_id=config.CHANNEL_ID,
            text=text,
            parse_mode="Markdown"
        )
        print(f"✅ [{contest_id}] Результат опубликован в канале")
    except Exception as e:
        print(f"❌ [{contest_id}] Ошибка публикации результата: {e}")
    
    # Сохраняем победителя в БД
    await db.set_contest_winner(contest_id, winner['user_id'])
    await db.increment_user_wins(winner['user_id'], contest['contest_type'])
    
    # Проверяем достижения победителя
    from handlers.user.achievements import check_achievements
    await check_achievements(bot, winner['user_id'])
    
    # Завершаем конкурс
    await db.update_contest_status(contest_id, 'ended')
    
    # Уведомляем админа
    admin_text = (
        f"🎰 **Рандомайзер #{contest_id} завершён!**\n\n"
        f"🎁 Приз: {contest['prize']}\n"
        f"👥 Участников: {len(participants)}\n\n"
        f"🏆 **ПОБЕДИТЕЛЬ:**\n"
        f"{winner['position']} {winner['comment_text']} — {winner_name} (ID: {winner['user_id']})\n\n"
        f"✅ Результат уже опубликован в канале"
    )
    
    try:
        await bot.send_message(
            chat_id=config.ADMIN_ID,
            text=admin_text,
            parse_mode="Markdown"
        )
        print(f"✅ [{contest_id}] Уведомление отправлено админу")
    except Exception as e:
        print(f"❌ [{contest_id}] Ошибка отправки уведомления админу: {e}")
