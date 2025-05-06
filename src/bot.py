import logging
import io
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Относительные импорты из текущего пакета src
from . import config 
from . import utils
from . import db_helpers
from . import media_processor

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=config.TGTOKEN)
dp = Dispatcher(bot)

# Инициализация БД
db_helpers.init_db()

# --- Обработчики Команд ---
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    logger.info(f"User {message.from_user.id} used /start")
    bot_info = await utils.get_bot_specific_info()
    
    welcome_text = "Привет! Я бот для перевода голосовых и видеосообщений в текст.\n"
    quick_start = ("Просто отправь или перешли мне голосовое или видеосообщение (кружочек).\n"
                   "Если хочешь, чтобы я работал в чате, добавь меня в чат и дай права администратора.")
    
    if bot_info:
        welcome_text = bot_info.get("description", welcome_text)
        # Можно добавить поле "greeting" или "welcome_message" в JSON
        quick_start_from_json = bot_info.get("quick_start_guide", quick_start)
        full_message = f"{welcome_text}\n\n{quick_start_from_json}"
    else:
        full_message = f"{welcome_text}\n\n{quick_start}"
    
    full_message += "\n\nИспользуй /help для дополнительной информации."
    await message.answer(full_message)

@dp.message_handler(commands=['help'])
async def show_help(message: types.Message):
    logger.info(f"User {message.from_user.id} used /help")
    bot_info = await utils.get_bot_specific_info()
    help_message_parts = ["Помощь по боту:"]
    default_help_items = [
        "- Отправь голосовое или видеосообщение для перевода в текст.",
        "- /start - Начальное приветствие и инструкция.",
        "- /info - Информация о боте.",
        "- /stats - Статистика использования."
    ]

    if bot_info and "help_text" in bot_info:
        # Если help_text это многострочный текст, его можно разбить
        help_items_from_json = bot_info["help_text"].split('\n')
        help_message_parts.extend(help_items_from_json)
    else:
        help_message_parts.extend(default_help_items)
        
    await message.answer("\n".join(help_message_parts))

@dp.message_handler(commands=['info'])
async def show_info(message: types.Message):
    logger.info(f"User {message.from_user.id} used /info")
    bot_info = await utils.get_bot_specific_info()
    info_text_parts = ["Информация о боте:"]
    
    if bot_info:
        name = bot_info.get("name", "VTT Бот")
        description = bot_info.get("description", "Перевод ГС и видео в текст.")
        repo = bot_info.get("repository")
        
        info_text_parts.append(f"Название: {name}")
        info_text_parts.append(f"Описание: {description}")
        if repo:
            info_text_parts.append(f"Репозиторий: {repo}")
        
        if bot_info.get("basic_info") and "community" in bot_info["basic_info"]:
            community_info = bot_info["basic_info"]["community"]
            channel_url = community_info.get("telegram_channel_url")
            forum_url = community_info.get("telegram_forum_url")
            if channel_url:
                info_text_parts.append(f"Основной канал: {channel_url}")
            if forum_url:
                info_text_parts.append(f"Чат/Форум: {forum_url}")
    else:
        info_text_parts.append("Не удалось загрузить подробную информацию. Попробуйте позже.")

    await message.answer("\n".join(info_text_parts))

@dp.message_handler(commands=['stats'])
async def show_stats_command(message: types.Message): # Переименовал, чтобы не конфликтовать с функцией
    logger.info(f"User {message.from_user.id} used /stats")
    stats_data = db_helpers.get_stats() # Пока синхронно
    # Если перейдешь на aiosqlite, здесь будет: stats_data = await db_helpers.get_stats_async()
    
    text = (f"📊 Статистика использования бота:\n"
            f" ├ Всего уникальных пользователей: {stats_data.get('total_users', 0)}\n"
            f" ├ Уникальных пользователей сегодня: {stats_data.get('today_users', 0)}\n"
            f" ├ Всего обработано сообщений: {stats_data.get('total_requests', 0)}\n"
            f" └ Обработано сообщений сегодня: {stats_data.get('today_requests', 0)}")
    await message.reply(text)

# --- Обработчики Сообщений ---
async def handle_audio_message(message: types.Message, audio_source, message_type: str):
    user_id = message.from_user.id
    audio_file_io = io.BytesIO()
    processed_audio_io = None
    
    try:
        await audio_source.download(destination_file=audio_file_io)
        audio_file_io.seek(0)

        if message_type == "voice":
            # Голосовые сообщения часто уже в хорошем формате, но лучше перекодировать
            # для консистентности и гарантии 16kHz mono WAV
            processed_audio_io = media_processor.process_audio_data(audio_file_io)
        elif message_type == "video_note":
            processed_audio_io = await media_processor.extract_audio_from_video_note(audio_file_io)
        
        if processed_audio_io:
            text = media_processor.recognize_speech_from_object(processed_audio_io)
            await message.reply(text)
            db_helpers.record_stat(user_id, message_type=message_type)
        else:
            if message_type == "video_note":
                await message.reply("Не удалось извлечь аудио из видеосообщения.")
            else: # Общая ошибка для голосового, если process_audio_data вернет None
                await message.reply("Не удалось обработать аудио.")
                
    except Exception as e:
        logger.error(f"Error processing {message_type} message from {user_id}: {e}", exc_info=True)
        await message.reply(f"Произошла ошибка при обработке вашего {message_type} сообщения.")
    finally:
        audio_file_io.close()
        if processed_audio_io:
            processed_audio_io.close()

@dp.message_handler(content_types=types.ContentType.VOICE)
async def process_voice_message_handler(message: types.Message):
    logger.info(f"Received voice message from {message.from_user.id}")
    await handle_audio_message(message, message.voice, "voice")

@dp.message_handler(content_types=types.ContentType.VIDEO_NOTE)
async def process_video_note_message_handler(message: types.Message):
    logger.info(f"Received video_note message from {message.from_user.id}")
    await handle_audio_message(message, message.video_note, "video_note")

async def on_startup(dispatcher):
    logger.info("VTT Bot started")
    # Можно добавить уведомление о запуске в Telegram/Gotify

async def on_shutdown(dispatcher):
    logger.info("VTT Bot shutting down")
    # Закрытие соединений с БД, если они глобальные (но мы их закрываем в функциях)

def main():
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)

if __name__ == '__main__':
    main()