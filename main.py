"""
Contest Bot v2.5 - Точка входа с API сервером
Обновлено: PostgreSQL + API для Telegram Mini App + Traefik SSL
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher

import config
from database_postgres import DatabasePostgres
import database_postgres


async def restore_active_contests(bot: Bot):
    """Восстановить активные конкурсы после рестарта"""
    from handlers.contests.voting_contest import active_tasks
    from database_postgres import db
    
    print("\n🔄 Восстановление активных конкурсов...")
    
    contests = await db.get_active_contests()
    
    if not contests:
        print("   ℹ️  Нет активных конкурсов для восстановления")
        return
    
    for contest in contests:
        contest_id = contest['id']
        contest_type = contest['contest_type']
        status = contest['status']
        
        print(f"   🔄 Конкурс #{contest_id} ({contest_type}, {status})")
        
        try:
            # Восстанавливаем задачи в зависимости от статуса
            if status == 'collecting':
                # Восстановить сбор участников
                if contest_type == 'voting_contest':
                    from handlers.contests.voting_contest import collect_comments
                    task = asyncio.create_task(collect_comments(bot, contest_id))
                    active_tasks[f"collect_{contest_id}"] = task
                    print(f"      ✅ Восстановлен сбор (voting)")
                    
                elif contest_type == 'random_contest':
                    from handlers.contests.random_contest import collect_random_participants
                    task = asyncio.create_task(collect_random_participants(bot, contest_id))
                    active_tasks[f"collect_{contest_id}"] = task
                    print(f"      ✅ Восстановлен сбор (random)")
                    
                elif contest_type == 'spam_contest':
                    from handlers.contests.spam_contest import collect_spam_participants
                    task = asyncio.create_task(collect_spam_participants(bot, contest_id))
                    active_tasks[f"collect_{contest_id}"] = task
                    print(f"      ✅ Восстановлен сбор (spam)")
            
            elif status == 'voting':
                # Восстановить таймер голосования
                from handlers.contests.voting_contest import start_timer
                task = asyncio.create_task(start_timer(bot, contest_id, contest['timer_minutes']))
                active_tasks[f"timer_{contest_id}"] = task
                print(f"      ✅ Восстановлен таймер голосования")
            
            elif status == 'running' and contest_type == 'spam_contest':
                # Восстановить спам-конкурс
                from handlers.contests.spam_contest import run_spam_timer
                entry_conditions = contest.get('entry_conditions', {})
                duration = entry_conditions.get('contest_duration', 10)
                task = asyncio.create_task(run_spam_timer(bot, contest_id, duration))
                active_tasks[f"spam_timer_{contest_id}"] = task
                print(f"      ✅ Восстановлен спам-конкурс")
            
            elif status == 'ready_to_start':
                print(f"      ℹ️  Ожидает запуска админом")
                
        except Exception as e:
            print(f"      ❌ Ошибка восстановления: {e}")
    
    print(f"✅ Восстановлено конкурсов: {len(contests)}\n")


async def shutdown(bot: Bot, db: DatabasePostgres, api_runner=None):
    """Корректное завершение работы бота и API"""
    from handlers.contests.voting_contest import active_tasks
    
    print("\n🛑 Завершение работы...")
    
    # Останавливаем API сервер
    if api_runner:
        try:
            print("   ⏳ Остановка API сервера...")
            await api_runner.cleanup()
            print("   ✅ API сервер остановлен")
        except Exception as e:
            print(f"   ⚠️ Ошибка остановки API: {e}")
    
    # Отменяем все активные задачи конкурсов
    if active_tasks:
        print(f"   ⏳ Отмена {len(active_tasks)} активных задач...")
        for task_name, task in list(active_tasks.items()):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        active_tasks.clear()
        print("   ✅ Все задачи отменены")
    
    # Закрываем пул соединений БД
    try:
        await db.close_pool()
        print("   ✅ База данных отключена")
    except Exception as e:
        print(f"   ⚠️ Ошибка закрытия БД: {e}")
    
    print("👋 Бот остановлен корректно")


async def main():
    """Главная функция запуска бота"""
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    api_runner = None
    
    try:
        # Инициализация PostgreSQL
        print("🔌 Подключение к базе данных...")
        db = DatabasePostgres(config.POSTGRES_DSN)
        await db.init_pool()
        await db.init_db()
        print("✅ База данных подключена")
        
        # Установить глобальный экземпляр для других модулей
        database_postgres.db = db
        
        # Создание бота
        print("🤖 Инициализация бота...")
        bot = Bot(token=config.BOT_TOKEN)
        dp = Dispatcher()
        
        # Подключение роутеров
        from handlers import router
        dp.include_router(router)
        print("✅ Роутеры подключены")
        
        # ✅ ВОССТАНОВЛЕНИЕ АКТИВНЫХ КОНКУРСОВ
        await restore_active_contests(bot)
        
        # 🆕 ЗАПУСК API СЕРВЕРА ДЛЯ TELEGRAM MINI APP
        try:
            from api_server import start_api_server
            print("📡 Запуск API сервера для Mini App...")
            api_runner = await start_api_server()
            print("✅ API сервер запущен на порту 8000")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска API сервера: {e}")
            import traceback
            traceback.print_exc()
            api_runner = None
        
        # Запуск бота
        print("🚀 Бот запущен и готов к работе!\n")
        await dp.start_polling(bot)
        
    except (KeyboardInterrupt, SystemExit):
        print("\n⚠️  Получен сигнал остановки...")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Корректное завершение работы
        await shutdown(bot, db, api_runner)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")

        