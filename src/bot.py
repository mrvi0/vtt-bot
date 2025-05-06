import logging
import io
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import random

# Относительные импорты из текущего пакета src
from . import config 
from . import utils
from . import db_helpers
from . import media_processor
from aiogram.types import ParseMode
# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=config.TGTOKEN)
dp = Dispatcher(bot)

# Инициализация БД
db_helpers.init_db()

message_counter_for_ads = 0

# --- Вспомогательная функция для получения рекламного текста ---
async def get_ad_text() -> str | None:
    shared_data = await utils.get_shared_info_async()
    if not shared_data or "ads" not in shared_data:
        return None

    ads_config = shared_data["ads"]
    default_ad = ads_config.get("default_ad_text")
    additional_ads = ads_config.get("additional_ads", [])

    if additional_ads:
        # Если есть дополнительные объявления, выбираем случайно одно из них
        # Можно усложнить логику выбора, если есть "weights"
        selected_ad_obj = random.choice(additional_ads)
        return selected_ad_obj.get("text")
    elif default_ad:
        # Если дополнительных нет, но есть дефолтное
        return default_ad
    
    return None # Если вообще ничего нет

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
    stats_data = await db_helpers.get_stats() # Пока синхронно
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
    chat_id = message.chat.id # Получаем chat_id
    audio_file_io = io.BytesIO()
    processed_audio_io = None
    
    try:
        await audio_source.download(destination_file=audio_file_io)
        audio_file_io.seek(0)

        if message_type == "voice":
            processed_audio_io = media_processor.process_audio_data(audio_file_io)
        elif message_type == "video_note":
            processed_audio_io = await media_processor.extract_audio_from_video_note(audio_file_io)
        
        if processed_audio_io:
            recognized_text = media_processor.recognize_speech_from_object(processed_audio_io)
            
            ad_text_to_append = None
            if config.AD_SHOW_INTERVAL > 0:
                current_chat_ad_count = await db_helpers.increment_chat_ad_counter(chat_id)
                logger.info(f"Chat {chat_id} ad counter: {current_chat_ad_count}")
                
                if current_chat_ad_count >= config.AD_SHOW_INTERVAL: # Используем >= для надежности
                    ad_text_to_append = await get_ad_text()
                    await db_helpers.reset_chat_ad_counter(chat_id)
                    logger.info(f"Showing ad in chat {chat_id}, counter reset.")
            
            final_reply_text = recognized_text
            if ad_text_to_append:
                final_reply_text += f"\n\n---\n{ad_text_to_append}" 
            
            # Для отключения превью ссылок, если ссылка одна:
            # await message.reply(final_reply_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
            # Если ссылок может быть несколько и нужно отключить превью для всех,
            # то нужно убедиться, что бот имеет права отправлять сообщения без web page preview
            # или использовать HTML-разметку и тег <a href='...'>text</a> без превью по умолчанию.
            # Для Markdown, если ссылка просто в тексте (не как [текст](url)), превью часто не бывает.
            # Если ссылка в формате [текст](url), то для отключения превью нужен disable_web_page_preview.
            # Проще всего для рекламного текста избегать формата [текст](url), а писать "Канал: t.me/канал"
            # Но если хочешь кликабельные, то disable_web_page_preview=True
            await message.reply(final_reply_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

            await db_helpers.record_stat(user_id, message_type=message_type) # Используем асинхронную версию
        else:
            # ... (обработка ошибок как ранее) ...
            error_msg = "Не удалось обработать аудио."
            if message_type == "video_note":
                error_msg = "Не удалось извлечь аудио из видеосообщения."
            await message.reply(error_msg)
            
    except Exception as e:
        logger.error(f"Error processing {message_type} message from {user_id} in chat {chat_id}: {e}", exc_info=True)
        await message.reply(f"Произошла ошибка при обработке вашего сообщения.")
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
    await db_helpers.init_db()
    logger.info("VTT Bot started and DB initialized.")
    # Можно добавить уведомление о запуске в Telegram/Gotify

async def on_shutdown(dispatcher):
    logger.info("VTT Bot shutting down...")
    # Закрытие соединений с БД, если они глобальные (но мы их закрываем в функциях)

def main():
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)

if __name__ == '__main__':
    main()