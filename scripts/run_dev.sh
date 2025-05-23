#!/bin/bash

# Скрипт для запуска приложения в режиме разработки (локально, без Docker)

# Переходим в директорию скрипта, затем в корень проекта
cd "$(dirname "$0")"/..

# Проверяем наличие .env файла
if [ ! -f ".env" ]; then
    echo "Ошибка: Файл .env не найден. Скопируйте .env.example в .env и заполните его."
    exit 1
fi

# Активируем виртуальное окружение (Python)
# source .venv/bin/activate
# Или устанавливаем переменные Node.js (если нужно)
# export NODE_ENV=development

echo "Запуск приложения в режиме разработки..."

# --- Выберите команду для вашего приложения ---

# Python (Пример)
# Используем python -m для правильного импорта из src
# python -m src.main
# Или напрямую, если настроен PYTHONPATH
# PYTHONPATH=src python src/main.py

# Node.js (Пример)
# node src/index.js
# Или с помощью nodemon для перезапуска при изменениях
# npx nodemon src/index.js

# --- Замените на вашу реальную команду запуска ---
echo "Замените эту строку на вашу команду запуска в scripts/run_dev.sh"
# Пример для Python:
# python src/main.py

# Если скрипт завершился успешно
echo "Приложение (вероятно) запущено. Нажмите Ctrl+C для остановки."

# Можно добавить команду ожидания или оставить как есть
# wait