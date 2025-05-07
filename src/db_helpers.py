# src/db_helpers.py
import aiosqlite
from . import config
import os
import logging

logger = logging.getLogger(__name__)

# Глобальная переменная для хранения соединения
_db_connection = None

async def get_db_connection():
    global _db_connection
    if _db_connection is None: # Создаем соединение только если его нет
        db_path = config.DB_NAME
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        try:
            _db_connection = await aiosqlite.connect(db_path)
            logger.info(f"Database connection to {db_path} established.")
        except Exception as e:
            logger.error(f"Failed to establish database connection: {e}", exc_info=True)
            # Можно здесь возбудить исключение, чтобы бот не стартовал без БД
            raise
    return _db_connection

async def close_db_connection():
    global _db_connection
    if _db_connection:
        try:
            await _db_connection.close()
            _db_connection = None
            logger.info("Database connection closed.")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}", exc_info=True)


async def init_db():
    try:
        db = await get_db_connection() # Получаем или создаем соединение
        async with db.executescript('''
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message_type TEXT, 
                date DATE
            );
            CREATE TABLE IF NOT EXISTS chat_ad_counters (
                chat_id INTEGER PRIMARY KEY,
                messages_since_last_ad INTEGER DEFAULT 0 NOT NULL
            );
        ''') as cursor: # executescript для нескольких выражений
            pass # Можно было бы проверить результат, но для CREATE IF NOT EXISTS не критично
        await db.commit() # Важно сделать commit
        logger.info("Database initialized (stats & chat_ad_counters tables).")
    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)


async def record_stat(user_id: int, message_type: str = "voice"):
    try:
        db = await get_db_connection()
        await db.execute("INSERT INTO stats (user_id, message_type, date) VALUES (?, ?, DATE('now'))", 
                       (user_id, message_type))
        await db.commit()
    except Exception as e:
        logger.error(f"SQLite error in record_stat for user {user_id}: {e}", exc_info=True)

async def get_stats():
    stats_data = {"total_users": 0, "today_users": 0, "total_requests": 0, "today_requests": 0}
    try:
        db = await get_db_connection()
        # 1. Всего уникальных пользователей
        async with db.execute("SELECT COUNT(DISTINCT user_id) FROM stats") as cursor:
            row = await cursor.fetchone()
            stats_data["total_users"] = row[0] if row else 0
        # 2. Уникальных пользователей сегодня
        async with db.execute("SELECT COUNT(DISTINCT user_id) FROM stats WHERE date = DATE('now')") as cursor: # <--- ВОЗМОЖНАЯ ПРОБЛЕМА ЗДЕСЬ
            row = await cursor.fetchone()
            stats_data["today_users"] = row[0] if row else 0
        # 3. Всего обработано сообщений
        async with db.execute("SELECT COUNT(*) FROM stats") as cursor:
            row = await cursor.fetchone()
            stats_data["total_requests"] = row[0] if row else 0
        # 4. Обработано сообщений сегодня
        async with db.execute("SELECT COUNT(*) FROM stats WHERE date = DATE('now')") as cursor: # <--- И ЗДЕСЬ
            row = await cursor.fetchone()
            stats_data["today_requests"] = row[0] if row else 0
    except Exception as e:
        logger.error(f"SQLite error in get_stats: {e}", exc_info=True)
    return stats_data

async def increment_chat_ad_counter(chat_id: int) -> int:
    new_count = 0
    try:
        db = await get_db_connection()
        await db.execute(
            "INSERT INTO chat_ad_counters (chat_id, messages_since_last_ad) VALUES (?, 1) "
            "ON CONFLICT(chat_id) DO UPDATE SET messages_since_last_ad = messages_since_last_ad + 1",
            (chat_id,)
        )
        await db.commit()
        async with db.execute("SELECT messages_since_last_ad FROM chat_ad_counters WHERE chat_id = ?", (chat_id,)) as cursor:
            row = await cursor.fetchone()
            new_count = row[0] if row else 1 # Если записи не было (INSERT сработал), то count = 1
    except Exception as e:
        logger.error(f"Error incrementing ad counter for chat {chat_id}: {e}", exc_info=True)
    return new_count

async def reset_chat_ad_counter(chat_id: int):
    try:
        db = await get_db_connection()
        await db.execute("UPDATE chat_ad_counters SET messages_since_last_ad = 0 WHERE chat_id = ?", (chat_id,))
        await db.commit()
    except Exception as e:
        logger.error(f"Error resetting ad counter for chat {chat_id}: {e}", exc_info=True)