import sqlite3
from . import config
import os

def get_db_connection():
    # Создаем директорию для БД, если ее нет
    db_path = config.DB_NAME
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS stats
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       user_id INTEGER,
                       message_type TEXT, 
                       date DATE)''')
    conn.commit()
    conn.close()

def record_stat(user_id: int, message_type: str = "voice"):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO stats (user_id, message_type, date) VALUES (?, ?, DATE('now'))", 
                       (user_id, message_type))
        conn.commit()
    except sqlite3.Error as e:
        print(f"SQLite error in record_stat: {e}")
    finally:
        conn.close()

def get_stats(): # Эта функция должна быть async, если перейдем на aiosqlite
    conn = get_db_connection()
    cursor = conn.cursor()
    stats_data = {}
    try:
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM stats")
        stats_data["total_users"] = (cursor.fetchone() or (0,))[0]
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM stats WHERE date = DATE('now')")
        stats_data["today_users"] = (cursor.fetchone() or (0,))[0]
        cursor.execute("SELECT COUNT(*) FROM stats")
        stats_data["total_requests"] = (cursor.fetchone() or (0,))[0]
        cursor.execute("SELECT COUNT(*) FROM stats WHERE date = DATE('now')")
        stats_data["today_requests"] = (cursor.fetchone() or (0,))[0]
    except sqlite3.Error as e:
        print(f"SQLite error in get_stats: {e}")
        # Возвращаем нули в случае ошибки, чтобы бот не падал
        return {"total_users": 0, "today_users": 0, "total_requests": 0, "today_requests": 0}
    finally:
        conn.close()
    return stats_data