FROM python:3.13-slim

WORKDIR /usr/src/app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем основные файлы
COPY main.py .
COPY config.py .
COPY database_postgres.py .
COPY api_server.py .
COPY test_debug.py .

# Копируем директории
ADD utils /usr/src/app/utils
ADD handlers /usr/src/app/handlers

# Создаём непривилегированного пользователя для безопасности
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /usr/src/app

USER botuser

# Запускаем main.py (бот + API сервер)
CMD ["python", "./main.py"]