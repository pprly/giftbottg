FROM python:3.13-slim
WORKDIR /usr/src/app 
COPY bot.py .
COPY config.py .
COPY database_postgres.py .
COPY requirements.txt . 
COPY test_debug.py .
ADD utils /usr/src/app/utils
ADD handlers /usr/src/app/handlers
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "./bot.py"]