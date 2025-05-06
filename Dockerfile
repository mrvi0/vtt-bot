# Используем базовый образ Python
FROM python:3.10-slim

# Устанавливаем системные зависимости, включая ffmpeg
# ca-certificates нужен для HTTPS запросов (к GitHub, Telegram API)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    # Дополнительные зависимости для librosa или speech_recognition, если нужны
    # Например, libsndfile1
    libsndfile1 \
 && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY src/ ./src/
COPY .env ./.env 
# Копируем .env файл, если он нужен при сборке (обычно нет, лучше через Docker Compose volumes или secrets)
# Либо рассчитываем на переменные окружения, заданные при запуске контейнера

# Создаем директорию для данных, если будем хранить БД внутри контейнера (не рекомендуется для prod)
# Лучше монтировать data как том
RUN mkdir -p /app/data 

# Команда для запуска приложения
# Запускаем напрямую через python -m src.bot, так как __main__ в bot.py
CMD ["python", "-m", "src.bot"]