"""
Спам-конкурс (Spam Contest)
Два таймера: регистрация + конкурс активности
Победитель = кто больше всех написал сообщений
"""

import asyncio
import random
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message
import config
from database_postgres import db
from utils.filters import ParticipantFilter


router = Router()

# Глобальный словарь для хранения активных задач
from handlers.contests.voting_contest import active_tasks


async def publish_spam_contest_announcement(bot: Bot, contest_id: int):
    """Публикация анонса спам-конкурса в канале"""
    contest = await db.get_contest_by_id(contest_id)
    if not contest:
        print("❌ Активный конкурс не найден")
        return
    
    # Форматируем условия участия
    entry_conditions = contest.get('entry_conditions', {})
    conditions_text = ParticipantFilter.format_conditions(entry_conditions)
    
    # Нам нужны ДВА таймера - они сохранены в БД как:
    # participants_count - количество участников
    # timer_minutes - время регистрации (первый таймер)
    # Второй таймер мы запросим отдельно или передадим через contest
    
    text = (
        f"⚡ **СПАМ-КОНКУРС!**\n\n"
        f"🎁 Приз: {contest['prize']}\n\n"
        f"📝 **Условия:**\n"
        f"{contest['conditions']}\n\n"
        f"**Фильтры:**\n"
        f"{conditions_text}\n\n"
        f"💬 1 сообщение = 1 балл\n\n"
        f"⏰ Регистрация: {contest['timer_minutes']} мин\n"
        f"Поторопитесь!"
    )
    
    try:
        message = await bot.send_message(
            chat_id=config.CHANNEL_ID,
            text=text,
            parse_mode="Markdown"
        )
        
        await db.set_announcement_message(contest_id, message.message_id)
        
        print(f"✅ [{contest_id}] Анонс спам-конкурса опубликован! Message ID: {message.message_id}")
        
        # Запускаем сбор участников с сохранением задачи
        task = asyncio.create_task(collect_spam_participants(bot, contest_id))
        active_tasks[f"collect_{contest_id}"] = task
        
    except Exception as e:
        print(f"❌ [{contest_id}] Ошибка публикации анонса: {e}")


async def collect_spam_participants(bot: Bot, contest_id: int):
    """Фоновая задача сбора участников для спам-конкурса (ТАЙМЕР 1)"""
    task_key = f"collect_{contest_id}"
    
    try:
        contest = await db.get_contest_by_id(contest_id)
        if not contest:
            print(f"❌ [{contest_id}] Конкурс не найден при сборе участников")
            return
        
        print(f"🔄 [{contest_id}] Начат сбор участников для спам-конкурса")
        
        # Ждём указанное время ИЛИ пока не наберём нужное количество
        start_time = datetime.now()
        timeout_minutes = contest['timer_minutes']  # ТАЙМЕР 1: время регистрации
        
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
                    
                    # Меняем статус на 'running' (идёт конкурс)
                    await db.update_contest_status(contest_id, 'running')
                    
                    # Удаляем задачу сбора из активных
                    if task_key in active_tasks:
                        del active_tasks[task_key]
                    
                    # Запускаем сам спам-конкурс (ТАЙМЕР 2)
                    await start_spam_contest(bot, contest_id)
                    break
                
                # Проверяем не истекло ли время регистрации
                elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60
                if elapsed_minutes >= timeout_minutes:
                    print(f"⏰ [{contest_id}] Время регистрации вышло! Собрано {current_count} участников")
                    
                    if current_count > 0:
                        await db.update_contest_status(contest_id, 'running')
                        
                        # Удаляем задачу сбора
                        if task_key in active_tasks:
                            del active_tasks[task_key]
                        
                        # Запускаем конкурс
                        await start_spam_contest(bot, contest_id)
                    else:
                        print(f"❌ [{contest_id}] Нет участников, конкурс отменяется")
                        await db.update_contest_status(contest_id, 'ended')
                        
                        # Удаляем анонс
                        old_announcement_id = contest.get('announcement_message_id')
                        if old_announcement_id:
                            try:
                                await bot.delete_message(
                                    chat_id=config.CHANNEL_ID,
                                    message_id=old_announcement_id
                                )
                            except:
                                pass
                    
                    # Удаляем задачу
                    if task_key in active_tasks:
                        del active_tasks[task_key]
                    break
                
                print(f"📊 [{contest_id}] Регистрация: {current_count}/{needed_count} участников (прошло {int(elapsed_minutes)} мин)")
                
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


async def start_spam_contest(bot: Bot, contest_id: int):
    """Начало спам-конкурса (ТАЙМЕР 2) - подсчёт сообщений"""
    contest = await db.get_contest_by_id(contest_id)
    participants = await db.get_participants(contest_id)
    
    if not participants:
        print(f"❌ [{contest_id}] Нет участников для спам-конкурса")
        await db.update_contest_status(contest_id, 'ended')
        return
    
    print(f"⚡ [{contest_id}] СПАМ-КОНКУРС НАЧАЛСЯ! Участников: {len(participants)}")
    
    # Инициализируем всех участников в таблице spam_messages
    for participant in participants:
        await db.init_spam_participant(contest_id, participant['user_id'])
    
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
    
    # Публикуем live-таблицу
    leaderboard_text = await format_spam_leaderboard(contest, participants, contest['timer_minutes'])
    
    try:
        message = await bot.send_message(
            chat_id=config.CHANNEL_ID,
            text=leaderboard_text,
            mode="Markdown"
        )
        
        await db.set_announcement_message(contest_id, message.message_id)
        print(f"✅ [{contest_id}] Live-таблица опубликована")
        
        # Запускаем таймер конкурса с обновлениями
        task = asyncio.create_task(run_spam_timer(bot, contest_id, contest['timer_minutes']))
        active_tasks[f"spam_timer_{contest_id}"] = task
        
    except Exception as e:
        print(f"❌ [{contest_id}] Ошибка публикации таблицы: {e}")


async def format_spam_leaderboard(contest: dict, participants: list, minutes_left: int) -> str:
    """Форматирование таблицы лидеров"""
    contest_id = contest['id']
    
    # Получаем актуальную таблицу лидеров
    leaderboard = await db.get_spam_leaderboard(contest_id)
    
    text = (
        f"⚡ **СПАМ-КОНКУРС ИДЁТ!**\n\n"
        f"🎁 Приз: {contest['prize']}\n\n"
        f"🏆 **ТАБЛИЦА ЛИДЕРОВ:**\n\n"
    )
    
    # Показываем топ-10 (или всех если меньше)
    for idx, leader in enumerate(leaderboard[:10], 1):
        emoji = leader.get('comment_text', '❓')
        username = f"@{leader['username']}" if leader['username'] != "noname" else leader['full_name']
        count = leader['spam_count']
        
        # Эмодзи для топ-3
        if idx == 1 and count > 0:
            medal = "🔥🔥🔥"
        elif idx == 2 and count > 0:
            medal = "🔥🔥"
        elif idx == 3 and count > 0:
            medal = "🔥"
        else:
            medal = ""
        
        text += f"{idx} {emoji} {username} — {count} {medal}\n"
    
    # Если участников больше 10, показываем троеточие
    if len(leaderboard) > 10:
        text += f"...\n"
    
    text += f"\n\n⏰ Осталось {minutes_left} мин\n"
    text += f"💬 Пишите больше!\n\n"
    text += f"🔄 Обновление каждые 30 секунд"
    
    return text


async def run_spam_timer(bot: Bot, contest_id: int, duration_minutes: int):
    """Таймер спам-конкурса с обновлением таблицы каждые 30 секунд"""
    task_key = f"spam_timer_{contest_id}"
    
    try:
        contest = await db.get_contest_by_id(contest_id)
        message_id = contest['announcement_message_id']
        participants = await db.get_participants(contest_id)
        
        print(f"⏰ [{contest_id}] Таймер спам-конкурса запущен на {duration_minutes} минут")
        
        # Общее количество итераций (каждые 30 сек)
        total_iterations = duration_minutes * 2  # 2 итерации в минуту
        
        for iteration in range(total_iterations, -1, -1):
            # Проверяем не отменена ли задача
            if task_key not in active_tasks:
                print(f"⛔ [{contest_id}] Таймер спам-конкурса отменён")
                break
            
            # Сколько минут осталось
            minutes_left = iteration // 2
            
            # Обновляем таблицу
            leaderboard_text = await format_spam_leaderboard(contest, participants, minutes_left)
            
            try:
                await bot.edit_message_text(
                    chat_id=config.CHANNEL_ID,
                    message_id=message_id,
                    text=leaderboard_text,
                    parse_mode="Markdown"
                )
                print(f"🔄 [{contest_id}] Таблица обновлена, осталось {minutes_left} мин")
            except Exception as e:
                # Иногда Telegram не даёт обновлять если текст не изменился
                pass
            
            # Если ещё не конец - ждём 30 секунд
            if iteration > 0:
                await asyncio.sleep(30)
        
        # Конкурс завершён
        await finish_spam_contest(bot, contest_id)
        
        # Удаляем задачу из активных
        if task_key in active_tasks:
            del active_tasks[task_key]
    
    except asyncio.CancelledError:
        print(f"⛔ [{contest_id}] Таймер спам-конкурса был отменён")
        if task_key in active_tasks:
            del active_tasks[task_key]
    except Exception as e:
        print(f"❌ [{contest_id}] Критическая ошибка в таймере: {e}")
        if task_key in active_tasks:
            del active_tasks[task_key]


async def finish_spam_contest(bot: Bot, contest_id: int):
    """Завершение спам-конкурса и публикация результатов"""
    contest = await db.get_contest_by_id(contest_id)
    winner = await db.get_spam_winner(contest_id)
    leaderboard = await db.get_spam_leaderboard(contest_id)
    
    if not winner:
        print(f"❌ [{contest_id}] Нет победителя")
        await db.update_contest_status(contest_id, 'ended')
        return
    
    print(f"🏆 [{contest_id}] Победитель: {winner['username']} с {winner['spam_count']} спамами")
    
    # Удаляем live-таблицу
    old_message_id = contest.get('announcement_message_id')
    if old_message_id:
        try:
            await bot.delete_message(
                chat_id=config.CHANNEL_ID,
                message_id=old_message_id
            )
        except:
            pass
    
    # Форматируем финальный результат
    winner_name = f"@{winner['username']}" if winner['username'] != "noname" else winner['full_name']
    
    # Правильное склонение спамов
    spam_count = winner['spam_count']
    if spam_count % 10 == 1 and spam_count % 100 != 11:
        spam_word = "спам"
    elif spam_count % 10 in [2, 3, 4] and spam_count % 100 not in [12, 13, 14]:
        spam_word = "спама"
    else:
        spam_word = "спамов"
    
    text = (
        f"⚡ **СПАМ-КОНКУРС ЗАВЕРШЁН!**\n\n"
        f"👥 Участников: {len(leaderboard)}\n\n"
        f"🏆 **ИТОГОВАЯ ТАБЛИЦА:**\n\n"
    )
    
    # Топ-10
    for idx, leader in enumerate(leaderboard[:10], 1):
        emoji = leader['comment_text']
        username = f"@{leader['username']}" if leader['username'] != "noname" else leader['full_name']
        count = leader['spam_count']
        
        # Склонение для каждого
        if count % 10 == 1 and count % 100 != 11:
            word = "спам"
        elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
            word = "спама"
        else:
            word = "спамов"
        
        if idx == 1:
            text += f"{idx} {emoji} {username} — {count} {word} 👑\n"
        elif idx == 2:
            text += f"{idx} {emoji} {username} — {count} {word} 🥈\n"
        elif idx == 3:
            text += f"{idx} {emoji} {username} — {count} {word} 🥉\n"
        else:
            text += f"{idx} {emoji} {username} — {count} {word}\n"
    
    text += (
        f"\n🎉 **ПОБЕДИТЕЛЬ:** {winner_name}\n"
        f"🎁 **Приз:** {contest['prize']}\n\n"
        f"Поздравляем короля спама! 🎊"
    )
    
    # Публикуем результат
    try:
        await bot.send_message(
            chat_id=config.CHANNEL_ID,
            text=text,
            parse_mode="Markdown"
        )
        print(f"✅ [{contest_id}] Результат опубликован")
    except Exception as e:
        print(f"❌ [{contest_id}] Ошибка публикации результата: {e}")
    
    # Сохраняем победителя
    await db.set_contest_winner(contest_id, winner['user_id'])
    await db.increment_user_wins(winner['user_id'], 'spam_contest')
    
    # Проверяем достижения
    from handlers.user.achievements import check_achievements
    await check_achievements(bot, winner['user_id'])
    
    # Завершаем конкурс
    await db.update_contest_status(contest_id, 'ended')
    
    # Уведомляем админа
    admin_text = (
        f"⚡ **Спам-конкурс #{contest_id} завершён!**\n\n"
        f"🎁 Приз: {contest['prize']}\n"
        f"👥 Участников: {len(leaderboard)}\n\n"
        f"🏆 **ПОБЕДИТЕЛЬ:**\n"
        f"{winner['comment_text']} {winner_name} — {spam_count} {spam_word}\n"
        f"(ID: {winner['user_id']})\n\n"
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


