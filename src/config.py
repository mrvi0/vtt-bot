import os
from dotenv import load_dotenv

load_dotenv() # Загружает переменные из .env файла в окружение

TGTOKEN = os.getenv("VTT_BOT_TOKEN")
if not TGTOKEN:
    raise ValueError("Необходимо установить переменную окружения VTT_BOT_TOKEN")

# URL для получения общей информации о ботах
INFO_JSON_URL = os.getenv("INFO_JSON_URL", "https://raw.githubusercontent.com/mrvi0/b4dcat-infra-public-info/main/bots_info.json")
# Уникальный идентификатор этого бота в общем JSON файле
BOT_CODE_NAME_IN_INFO_JSON = os.getenv("BOT_CODE_NAME_IN_INFO_JSON", "vtt_bot")

DB_NAME = os.getenv("DB_NAME", "vtt_stats.db") # Имя файла БД