# Voice-to-Text Telegram Bot (VTT Bot)

[![License](https://img.shields.io/github/license/mrvi0/vtt-bot?style=flat-square)](https://github.com/mrvi0/vtt-bot/blob/main/LICENSE)
[![lint.yml](https://img.shields.io/github/actions/workflow/status/mrvi0/vtt-bot/lint.yml?branch=main&style=flat-square)](https://github.com/mrvi0/vtt-bot/actions/workflows/lint.yml) ![GitHub repo size](https://img.shields.io/github/repo-size/mrvi0/vtt-bot?style=flat-square) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

Телеграм-бот, который преобразует голосовые сообщения и видеосообщения ("кружочки") в текст. Полезен для тех, кто не может прослушать аудио в данный момент или предпочитает читать.

## ✨ Основные возможности

*   Преобразование голосовых сообщений в текст.
*   Преобразование видеосообщений ("кружочков") в текст.
*   Поддержка русского языка для распознавания.
*   Простая статистика использования.
*   Может работать как в личных сообщениях, так и в групповых чатах (требуются права администратора).

## 🚀 Установка

### Требования

*   Python 3.10+
*   Docker и Docker Compose (рекомендуется для запуска в контейнерах)
*   `ffmpeg` (должен быть установлен в системе или доступен в Docker-образе для обработки видеосообщений)

### Вариант 1: Запуск с Docker (Рекомендуется)

1.  **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/mrvi0/vtt-telegram-bot.git # Замените на ваш URL
    cd vtt-telegram-bot
    ```
2.  **Создайте файл `.env`:**
    Скопируйте `.env.example` в `.env` и заполните `VTT_BOT_TOKEN` и другие переменные при необходимости.
    ```bash
    cp .env.example .env
    nano .env # или ваш любимый редактор
    ```
3.  **Соберите и запустите контейнеры:**
    ```bash
    docker compose up --build -d
    ```
    * `-d` запускает контейнеры в фоновом режиме.
    * `--build` пересобирает образ, если Dockerfile или исходный код изменился.

    Чтобы посмотреть логи:
    ```bash
    docker compose logs -f vtt_bot 
    ```
    Чтобы остановить:
    ```bash
    docker compose down
    ```

### Вариант 2: Локальная установка (без Docker)

1.  **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/mrvi0/vtt-telegram-bot.git # Замените на ваш URL
    cd vtt-telegram-bot
    ```
2.  **Установите `ffmpeg`:**
    Убедитесь, что `ffmpeg` установлен в вашей системе и доступен в `PATH`.
    *   Для Debian/Ubuntu: `sudo apt update && sudo apt install ffmpeg`
3.  **Создайте и активируйте виртуальное окружение:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate # Linux/macOS
    # .\.venv\Scripts\activate # Windows
    ```
4.  **Установите зависимости:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Создайте файл `.env`:**
    Скопируйте `.env.example` в `.env` и заполните `VTT_BOT_TOKEN`.
    ```bash
    cp .env.example .env
    nano .env
    ```
6.  **Запустите приложение:**
    ```bash
    python -m src.bot
    ```

## ⚙️ Конфигурация

Приложение конфигурируется с помощью переменных окружения. Скопируйте файл `.env.example` в `.env` и укажите свои значения.

Основные переменные:

*   `VTT_BOT_TOKEN`: **Обязательно.** Токен вашего Telegram бота, полученный от @BotFather.
*   `INFO_JSON_URL`: URL к JSON-файлу с общей информацией о ботах. По умолчанию используется публичный файл проекта b4dcat.
*   `BOT_CODE_NAME_IN_INFO_JSON`: Идентификатор этого бота в `INFO_JSON_URL`. По умолчанию `vtt_bot`.
*   `DB_NAME`: Путь к файлу базы данных SQLite. По умолчанию `data/vtt_stats.db` (относительно директории, где запущен `docker-compose.yml` или `src/bot.py` при монтировании тома).

## ⚡ Использование

1.  **Запустите бота** одним из описанных выше способов.
2.  **Найдите бота в Telegram** по его имени пользователя (username).
3.  **Отправьте боту `/start`** для получения приветственного сообщения и инструкций.
4.  **Отправьте или перешлите боту голосовое сообщение или видеосообщение ("кружочек").** Бот ответит распознанным текстом.
5.  **Для работы в чатах:**
    *   Добавьте бота в ваш групповой чат.
    *   Назначьте бота администратором чата. Минимально необходимых прав нет, но для стабильной работы лучше дать права на чтение сообщений. Бот будет автоматически распознавать все голосовые и видеосообщения.

### Доступные команды:
*   `/start` - Приветствие и краткая инструкция.
*   `/help` - Подробная помощь и описание команд.
*   `/info` - Информация о боте, авторе и связанных ресурсах.
*   `/stats` - Показать статистику использования бота.

## 🧪 Тестирование

(На данный момент автоматические тесты не реализованы. Планируется добавление в будущем.)

```bash
# Пример для pytest (когда тесты будут добавлены)
# pytest tests/
```

## 🤝 Вклад в проект
Пока проект является персональным, но идеи и предложения приветствуются через Issues.
Если вы хотите внести вклад:
1. Сделайте форк репозитория.
2. Создайте новую ветку (`git checkout -b feature/ваша-фича`).
3. Внесите изменения.
4. Создайте Pull Request с описанием ваших изменений.
## 📜 Лицензия
Этот проект распространяется под лицензией MIT. Подробности смотрите в файле LICENSE. (LICENSE)
## 📞 Контакты
Создатель: Mr Vi - dev@b4dcat.ru\
Telelgram: [@B4DCAT](https://t.me/B4DCAT)\
Issues: https://github.com/mrvi0/vtt-telegram-bot/issues 