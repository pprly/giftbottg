"""
Голосовательный конкурс (Voting Contest)
Обработка комментариев, таймер, завершение
ИСПРАВЛЕНО: отмена фоновых задач при принудительном запуске
"""

import asyncio
import random
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message
import config
from database_postgres import db
from utils.filters import ParticipantFilter
from utils.formatters import format_time_left, format_participant_list


router = Router()

# Глобальный словарь для хранения активных задач
active_tasks = {}


def escape_markdown(text: str) -> str:
    """Экранирует спецсимволы Markdown"""
    if not text:
        return text
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in chars:
        text = text.replace(char, '\\' + char)
    return text


async def publish_contest_announcement(bot: Bot, contest_id: int):
    """Публикация анонса конкурса в канале"""
    contest = await db.get_contest_by_id(contest_id)
    if not contest:
        print("❌ Активный конкурс не найден")
        return
    
    # Форматируем условия участия
    entry_conditions = contest.get('entry_conditions', {})
    conditions_text = ParticipantFilter.format_conditions(entry_conditions)
    
    text = (
        f"🎉 **НАЧИНАЕМ КОНКУРС!**\n\n"
        f"🎁 Приз: {contest['prize']}\n\n"
        f"📝 **Условия участия:**\n"
        f"{contest['conditions']}\n\n"
        f"**Фильтры:**\n"
        f"{conditions_text}\n\n"
        f"⏰ Поторопитесь!"
    )
    
    try:
        message = await bot.send_message(
            chat_id=config.CHANNEL_ID,
            text=text,
            parse_mode="Markdown"
        )
        
        await db.set_announcement_message(contest_id, message.message_id)
        
        print(f"✅ Анонс опубликован! Message ID: {message.message_id}")
        
        # Запускаем сбор комментариев с сохранением задачи
        task = asyncio.create_task(collect_comments(bot, contest_id))
        active_tasks[f"collect_{contest_id}"] = task
        
    except Exception as e:
        print(f"❌ Ошибка публикации анонса: {e}")


async def collect_comments(bot: Bot, contest_id: int):
    """Фоновая задача сбора комментариев"""
    task_key = f"collect_{contest_id}"
    
    try:
        contest = await db.get_contest_by_id(contest_id)
        if not contest:
            print("❌ Активный конкурс не найден при сборе комментариев")
            return
        
        print(f"🔄 Начат сбор комментариев для конкурса {contest_id}")
        
        while True:
            # Проверяем не отменена ли задача
            if task_key not in active_tasks:
                print(f"⛔ Задача сбора комментариев для конкурса {contest_id} отменена")
                break
            
            try:
                current_count = await db.get_participants_count(contest_id)
                needed_count = contest['participants_count']
                
                print(f"📊 [{contest_id}] Собрано {current_count}/{needed_count} участников")
                
                if current_count >= needed_count:
                    print(f"✅ [{contest_id}] Собрано {current_count} участников!")
                    
                    # Меняем статус на 'voting'
                    await db.update_contest_status(contest_id, 'voting')
                    print(f"🔄 [{contest_id}] Статус конкурса изменён на 'voting'")
                    
                    await publish_participants_list(bot, contest_id)
                    
                    # Запускаем таймер с сохранением задачи
                    timer_task = asyncio.create_task(start_timer(bot, contest_id, contest['timer_minutes']))
                    active_tasks[f"timer_{contest_id}"] = timer_task
                    
                    # Удаляем задачу из активных
                    if task_key in active_tasks:
                        del active_tasks[task_key]
                    break
                
                await asyncio.sleep(config.COMMENT_CHECK_INTERVAL)
                
            except Exception as e:
                print(f"❌ [{contest_id}] Ошибка при сборе комментариев: {e}")
                await asyncio.sleep(5)
    
    except asyncio.CancelledError:
        print(f"⛔ Задача сбора комментариев для конкурса {contest_id} была отменена")
        if task_key in active_tasks:
            del active_tasks[task_key]
    except Exception as e:
        print(f"❌ Критическая ошибка в сборе комментариев: {e}")
        if task_key in active_tasks:
            del active_tasks[task_key]


async def cancel_collect_task(contest_id: int):
    """Отменить задачу сбора комментариев для конкурса"""
    task_key = f"collect_{contest_id}"
    
    if task_key in active_tasks:
        task = active_tasks[task_key]
        task.cancel()
        del active_tasks[task_key]
        print(f"✅ Задача сбора комментариев для конкурса {contest_id} отменена")
        
        # Даём время на завершение
        try:
            await task
        except asyncio.CancelledError:
            pass


async def cancel_timer_task(contest_id: int):
    """Отменить задачу таймера для конкурса"""
    task_key = f"timer_{contest_id}"
    
    if task_key in active_tasks:
        task = active_tasks[task_key]
        task.cancel()
        del active_tasks[task_key]
        print(f"✅ Задача таймера для конкурса {contest_id} отменена")
        
        # Даём время на завершение
        try:
            await task
        except asyncio.CancelledError:
            pass


async def check_subscription(bot: Bot, user_id: int) -> bool:
    """Проверка подписки пользователя на канал"""
    try:
        member = await bot.get_chat_member(chat_id=config.CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"⚠️ Ошибка проверки подписки для {user_id}: {e}")
        return False



async def publish_participants_list(bot: Bot, contest_id: int):
    """Публикация списка участников с эмодзи"""
    contest = await db.get_contest_by_id(contest_id)
    participants = await db.get_participants(contest_id)
    
    if not participants:
        print(f"❌ [{contest_id}] Нет участников для публикации")
        return
    
    print(f"📊 [{contest_id}] Публикация списка участников")
    
    # 🗑️ УДАЛЯЕМ СТАРОЕ СООБЩЕНИЕ-АНОНС
    old_announcement_id = contest.get('announcement_message_id')
    if old_announcement_id:
        try:
            await bot.delete_message(
                chat_id=config.CHANNEL_ID,
                message_id=old_announcement_id
            )
            print(f"🗑️ [{contest_id}] Старый анонс удалён (ID: {old_announcement_id})")
        except Exception as e:
            print(f"⚠️ [{contest_id}] Не удалось удалить анонс: {e}")
    
    # Публикуем новое сообщение со списком
    text = f"🎁 Приз: {contest['prize']}\n"
    text += "\n👥 Список участников:"
    text += format_participant_list(participants, include_blockquote=True)
    text += f"\n\n⏰ Осталось {contest['timer_minutes']} минут"
    text += f'\n\n💡 Голосуем Реакциями в <a href="{config.CHANNEL_INVITE_LINK}">Зазвездился</a>'
    text += f'\n📱<a href="{config.BOT_INVITE_LINK}"> Открыть Бота</a>'

    try:
        message = await bot.send_message(
            chat_id=config.CHANNEL_ID,
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        # Обновляем ID сообщения в БД (теперь это список участников)
        await db.set_announcement_message(contest_id, message.message_id)
        print(f"✅ [{contest_id}] Список участников опубликован. Message ID: {message.message_id}")
        return message.message_id
    except Exception as e:
        print(f"❌ [{contest_id}] Ошибка публикации списка: {e}")
        return None

async def start_timer(bot: Bot, contest_id: int, minutes: int):
    """Запуск таймера конкурса с обновлением каждую минуту"""
    task_key = f"timer_{contest_id}"
    
    try:
        print(f"⏰ [{contest_id}] Таймер запущен на {minutes} минут")
        
        contest = await db.get_contest_by_id(contest_id)
        message_id = contest['announcement_message_id']
        participants = await db.get_participants(contest_id)
        
        # Обновляем сообщение каждую минуту
        for remaining in range(minutes, -1, -1):  # minutes, minutes-1, ..., 1, 0
            # Проверяем не отменена ли задача
            if task_key not in active_tasks:
                print(f"⛔ [{contest_id}] Таймер отменён")
                break
            
            # Формируем текст в зависимости от оставшегося времени
            if remaining > 0:
                # Ещё есть время
                text = f"🎁 Приз: {contest['prize']}\n"
                text += "\n👥 Список участников:"
                text += format_participant_list(participants, include_blockquote=True)
                text += f"\n\n⏰ Осталось {format_time_left(remaining)}"
                text += f'\n\n💡 Голосуем Реакциями в <a href="{config.CHANNEL_INVITE_LINK}">Зазвездился</a>'
                text += f'\n📱<a href="{config.BOT_INVITE_LINK}"> Открыть Бота</a>'
            else:
                # Время вышло (remaining = 0)
                text = f"🎁 Приз: {contest['prize']}\n"
                text += "\n👥 Список участников:"
                text += format_participant_list(participants, include_blockquote=True)
                text += "\n\n⏳ Время вышло, ждём результатов!"
                text += f'\n\n💡 Голосуем Реакциями в <a href="{config.CHANNEL_INVITE_LINK}">Зазвездился</a>'
                text += f'\n📱<a href="{config.BOT_INVITE_LINK}"> Открыть Бота</a>'
            try:
                await bot.edit_message_text(
                    chat_id=config.CHANNEL_ID,
                    message_id=message_id,
                    text=text,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
                
                if remaining > 0:
                    print(f"⏰ [{contest_id}] Обновлён таймер: осталось {format_time_left(remaining)}")
                else:
                    print(f"⏳ [{contest_id}] Финальное обновление: Время вышло!")
            except Exception as e:
                print(f"❌ [{contest_id}] Ошибка обновления таймера: {e}")
            
            # Если время ещё не вышло - ждём минуту
            if remaining > 0:
                await asyncio.sleep(60)
        
        # Завершаем конкурс
        await end_contest(bot, contest_id)
        
        # Удаляем задачу из активных
        if task_key in active_tasks:
            del active_tasks[task_key]
    
    except asyncio.CancelledError:
        print(f"⛔ [{contest_id}] Таймер был отменён")
        if task_key in active_tasks:
            del active_tasks[task_key]
    except Exception as e:
        print(f"❌ [{contest_id}] Критическая ошибка в таймере: {e}")
        if task_key in active_tasks:
            del active_tasks[task_key]


async def end_contest(bot: Bot, contest_id: int):
    """Завершение конкурса - отправка результатов админу"""
    await db.update_contest_status(contest_id, 'ended')
    
    participants = await db.get_participants(contest_id)
    contest = await db.get_contest_by_id(contest_id)
    
    print(f"🏁 [{contest_id}] Конкурс завершён")
    
    if not participants:
        await bot.send_message(
            chat_id=config.ADMIN_ID,
            text=f"⚠️ Конкурс #{contest_id} завершён, но нет участников."
        )
        return
    
    # Формируем список участников для админа
    text = f"🏁 **Конкурс #{contest_id} завершён!**\n"
    text += f"🎁 Приз: {escape_markdown(contest['prize'])}\n"
    text += "👥 **Участники:**\n"
    
    for p in participants:
        emoji = p['comment_text']
        username = f"@{p['username']}" if p['username'] != "noname" else p['full_name']
        # ЭКРАНИРУЕМ ИМЯ
        safe_username = escape_markdown(username)
        text += f"{p['position']} {emoji} — {safe_username}\n"
    
    text += "\n\n**Выберите победителя:**\n"
    text += "Отправьте команду: `/win {номер}`\n\n"
    text += "Например: `/win 3` (если победил участник №3)"
    
    try:
        await bot.send_message(
            chat_id=config.ADMIN_ID,
            text=text,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        print(f"✅ [{contest_id}] Результаты отправлены админу")
    except Exception as e:
        print(f"❌ [{contest_id}] Ошибка отправки результатов: {e}")

        