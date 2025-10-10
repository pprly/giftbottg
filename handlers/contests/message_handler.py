"""
Единый обработчик сообщений в группе обсуждений
Решает конфликт между voting_contest и spam_contest
Маршрутизирует сообщения по типу и статусу конкурса
"""

import random
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message
import config
from database_postgres import db
from utils.filters import ParticipantFilter
from utils.messages import (
    format_rejection_message,
    get_not_subscribed_error,
    get_previous_winner_error
)

router = Router()


async def check_subscription(bot: Bot, user_id: int) -> bool:
    """Проверка подписки пользователя на канал"""
    try:
        member = await bot.get_chat_member(chat_id=config.CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"⚠️ Ошибка проверки подписки для {user_id}: {e}")
        return False


async def handle_participant_registration(message: Message, contest: dict):
    """
    Регистрация участника в конкурсе
    Используется для voting, random и spam (в статусе collecting)
    """
    print(f"\n      >>> НАЧАЛО РЕГИСТРАЦИИ УЧАСТНИКА <<<")
    print(f"      Конкурс ID: {contest['id']}")
    print(f"      Пользователь: @{message.from_user.username} (ID: {message.from_user.id})")
    
    # Игнорируем старые комментарии
    try:
        # Проверяем тип created_at
        contest_created = contest['created_at']
        
        # Если это строка - преобразуем в datetime
        if isinstance(contest_created, str):
            contest_created = datetime.fromisoformat(contest_created)
        
        # Если уже datetime - используем как есть
        message_date = message.date.replace(tzinfo=None)
        
        print(f"      Дата создания конкурса: {contest_created}")
        print(f"      Дата сообщения: {message_date}")
        
        if message_date < contest_created:
            print(f"      ⏭️ Пропускаю старый комментарий от @{message.from_user.username}")
            return
        
        print(f"      ✅ Сообщение новее конкурса - продолжаю")
    except Exception as e:
        print(f"      ⚠️ Ошибка проверки даты: {e}")
        # Продолжаем работу даже если есть проблемы с датой
    
    print(f"      💬 Комментарий: {message.text[:50] if message.text else 'нет текста'}...")
    
    # Проверяем подписку на канал
    print(f"      🔍 Проверяю подписку на канал...")
    is_subscribed = await check_subscription(message.bot, message.from_user.id)
    print(f"      {'✅' if is_subscribed else '❌'} Подписка: {is_subscribed}")
    
    if not is_subscribed:
        print(f"      ⚠️ Пользователь @{message.from_user.username} не подписан")
        try:
            await message.reply(
                f'⚠️ Вы не подписаны на канал!\n\n'
                f'👉 <a href="{config.CHANNEL_INVITE_LINK}">Подпишитесь на канал</a> для участия в конкурсе.',
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"      ⚠️ Не удалось отправить предупреждение: {e}")
        return
    
    # Проверяем условия участия (entry_conditions)
    print(f"      🔍 Проверяю условия участия...")
    entry_conditions = contest.get('entry_conditions', {})
    print(f"      Условия: {entry_conditions}")
    
    can_participate, error_data = await ParticipantFilter.check_conditions(
        message.from_user.id, 
        entry_conditions
    )
    
    print(f"      {'✅' if can_participate else '❌'} Может участвовать: {can_participate}")
    
    if not can_participate:
        error_type, required, current = error_data
        error_message = format_rejection_message(error_type, required, current)
        print(f"      ⚠️ Пользователь не прошёл фильтр: {error_type} (требуется: {required}, текущее: {current})")
        try:
            await message.reply(error_message, parse_mode="Markdown")
        except Exception as e:
            print(f"      ⚠️ Не удалось отправить предупреждение: {e}")
        return
    
    # Запрещаем участие победителям предыдущего конкурса этого типа
    print(f"      🔍 Проверяю победителей прошлых конкурсов...")
    last_winners = await db.get_last_winners_by_type(contest['contest_type'], limit=1)
    print(f"      Победители прошлых конкурсов: {last_winners}")
    
    if last_winners and message.from_user.id in last_winners:
        print(f"      ⛔ Пользователь @{message.from_user.username} был победителем в прошлом конкурсе")
        try:
            await message.reply(
                "⛔ Вы были победителем в прошлом конкурсе этого типа!\n\n"
                "Дайте шанс другим участникам. Вы сможете участвовать в следующем конкурсе. 😊"
            )
        except Exception as e:
            print(f"      ⚠️ Не удалось отправить предупреждение: {e}")
        return
    
    # Получаем уже использованные эмодзи
    print(f"      🔍 Получаю список участников...")
    existing_participants = await db.get_participants(contest['id'])
    print(f"      Текущих участников: {len(existing_participants)}")
    
    used_emojis = [p['comment_text'] for p in existing_participants]
    
    # Выбираем эмодзи, который ещё не использовался
    available_emojis = [e for e in config.PARTICIPANT_EMOJIS if e not in used_emojis]
    
    if not available_emojis:
        print(f"      ⚠️ Закончились уникальные эмодзи!")
        random_emoji = random.choice(config.PARTICIPANT_EMOJIS)
    else:
        random_emoji = random.choice(available_emojis)
    
    print(f"      🎲 Выбран эмодзи: {random_emoji}")
    
    # Добавляем участника (позиция определяется автоматически в БД)
    print(f"      💾 Добавляю участника в БД...")
    try:
        added = await db.add_participant(
            contest_id=contest['id'],
            user_id=message.from_user.id,
            username=message.from_user.username or "noname",
            full_name=message.from_user.full_name,
            emoji=random_emoji
        )
        
        print(f"      {'✅' if added else '⚠️'} Результат добавления: {added}")
        
        if added:
            count = await db.get_participants_count(contest['id'])
            print(f"      ✅ Добавлен! Эмодзи: {random_emoji} Всего: {count}/{contest['participants_count']}")
            
            # Увеличиваем счётчик участий в статистике
            print(f"      📊 Обновляю статистику...")
            await db.increment_user_contests(message.from_user.id)
            
            # Проверяем достижения за участие
            print(f"      🏆 Проверяю достижения...")
            from handlers.user.achievements import check_achievements
            await check_achievements(message.bot, message.from_user.id)
            
            # Если набрано нужное количество, сразу закрываем регистрацию
            if count >= contest['participants_count']:
                print(f"      🔒 Регистрация закрыта! Набрано {count} участников")
                await db.update_contest_status(contest['id'], 'voting')
        else:
            print(f"      ⚠️ Участник уже зарегистрирован")
            
    except Exception as e:
        print(f"      ❌ ОШИБКА при добавлении участника: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"      >>> КОНЕЦ РЕГИСТРАЦИИ УЧАСТНИКА <<<\n")


async def handle_spam_counting(message: Message, contest: dict):
    """
    Подсчёт спамов для участника спам-конкурса
    Используется только когда spam_contest в статусе 'running'
    """
    # Проверяем является ли этот юзер участником
    participants = await db.get_participants(contest['id'])
    participant_ids = [p['user_id'] for p in participants]
    
    if message.from_user.id in participant_ids:
        # Увеличиваем счётчик
        await db.increment_spam_count(contest['id'], message.from_user.id)
        print(f"💬 [{contest['id']}] +1 спам для @{message.from_user.username}")


@router.message(F.chat.id == config.DISCUSSION_GROUP_ID)
async def handle_discussion_message(message: Message):
    """
    ЕДИНЫЙ обработчик всех сообщений в группе обсуждений
    Маршрутизирует по типу и статусу конкурса
    """
    print("\n" + "="*60)
    print("📨 ПОЛУЧЕНО СООБЩЕНИЕ В ГРУППЕ ОБСУЖДЕНИЙ")
    print("="*60)
    print(f"   От: @{message.from_user.username} (ID: {message.from_user.id})")
    print(f"   Текст: {message.text[:50] if message.text else 'нет текста'}...")
    print(f"   Chat ID: {message.chat.id}")
    print(f"   Message ID: {message.message_id}")
    print(f"   Дата: {message.date}")
    print("="*60)
    
    # Игнорируем сообщения от бота
    if message.from_user.id == config.BOT_ID:
        print("   ⏭️ Игнорирую сообщение от бота")
        return

    # Игнорируем сообщения от других ботов
    if message.from_user.is_bot:
        print("   ⏭️ Игнорирую сообщение от другого бота")
        return
    
    # Получаем все активные конкурсы
    contests = await db.get_active_contests()
    
    print(f"   📋 Найдено активных конкурсов: {len(contests)}")
    
    if not contests:
        print("   ⏭️ Нет активных конкурсов")
        return
    
    # Обрабатываем каждый активный конкурс
    for contest in contests:
        contest_type = contest['contest_type']
        status = contest['status']
        
        print(f"\n   🔍 Проверяю конкурс #{contest['id']}")
        print(f"      Тип: {contest_type}")
        print(f"      Статус: {status}")
        print(f"      Создан: {contest['created_at']}")
        
        # ============================================================
        # РЕГИСТРАЦИЯ УЧАСТНИКОВ (для всех типов в статусе collecting)
        # ============================================================
        if status == 'collecting':
            print(f"      ✅ Конкурс в статусе 'collecting' - начинаю регистрацию")
            # Все типы конкурсов регистрируют участников через комментарии
            if contest_type in ['voting_contest', 'random_contest', 'spam_contest']:
                await handle_participant_registration(message, contest)
            else:
                print(f"      ⚠️ Неизвестный тип конкурса: {contest_type}")
        else:
            print(f"      ⏭️ Конкурс НЕ в статусе 'collecting' (текущий: {status})")
        
        # ============================================================
        # ПОДСЧЁТ СПАМОВ (только для spam_contest в статусе running)
        # ============================================================
        if contest_type == 'spam_contest' and status == 'running':
            print(f"      ✅ Спам-конкурс в режиме 'running' - подсчитываю спам")
            await handle_spam_counting(message, contest)
    
    print("="*60 + "\n")