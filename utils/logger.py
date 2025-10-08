"""
Система логирования для Contest Bot
Ежедневные логи с автоматическим удалением через 5 дней
"""

import logging
from logging.handlers import TimedRotatingFileHandler
import os
from datetime import datetime


def setup_logger():
    """
    Настройка логирования:
    - Логи в файл logs/bot_YYYY-MM-DD.log
    - Новый файл каждый день в полночь
    - Хранятся последние 5 дней
    - Дублирование в консоль
    """
    
    # Создаём папку для логов если её нет
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print(f"✅ Создана папка для логов: {log_dir}/")
    
    # Формат логов: [Дата Время] [Уровень] [Файл:Строка] Сообщение
    log_format = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Создаём главный логгер
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Логируем всё начиная с INFO
    
    # Удаляем старые обработчики если есть (чтобы не дублировались)
    logger.handlers.clear()
    
    # ============================================
    # ОБРАБОТЧИК 1: Файл с ежедневной ротацией
    # ============================================
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, "bot.log"),
        when='midnight',        # Новый файл каждую полночь
        interval=1,             # Каждый 1 день
        backupCount=5,          # Хранить последние 5 дней
        encoding='utf-8'
    )
    
    # Добавляем дату в название файла при ротации
    file_handler.suffix = "%Y-%m-%d"
    
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    
    # ============================================
    # ОБРАБОТЧИК 2: Консоль (дублируем в терминал)
    # ============================================
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # Логируем старт
    logger.info("=" * 60)
    logger.info(f"🚀 Contest Bot запущен")
    logger.info(f"📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"📁 Логи сохраняются в: {log_dir}/")
    logger.info("=" * 60)
    
    return logger


def get_logger():
    """
    Получить настроенный логгер
    Использовать в других файлах: logger = get_logger()
    """
    return logging.getLogger()


# Примеры использования в коде:
# 
# from utils.logger import get_logger
# logger = get_logger()
# 
# logger.info("✅ Конкурс создан")
# logger.warning("⚠️ Участник уже зарегистрирован")
# logger.error("❌ Ошибка подключения к БД")
# logger.debug("🔍 Отладочная информация")  # Не будет логироваться (уровень ниже INFO)
