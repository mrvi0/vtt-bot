import httpx
from . import config # Относительный импорт из текущего пакета

async def get_shared_info_async():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(config.INFO_JSON_URL, timeout=10)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        print(f"Error fetching shared info from GitHub: {e}")
    except Exception as e: # Ловим ошибки парсинга JSON и др.
        print(f"Error processing shared info: {e}")
    return None

async def get_bot_specific_info() -> dict | None:
    shared_data = await get_shared_info_async()
    bot_code_name = config.BOT_CODE_NAME_IN_INFO_JSON
    
    bot_specifics = {}
    if shared_data:
        if "bot_info" in shared_data and bot_code_name in shared_data["bot_info"]:
            bot_specifics.update(shared_data["bot_info"][bot_code_name])
        # Добавляем basic_info для общего доступа
        if "basic_info" in shared_data:
            bot_specifics["basic_info"] = shared_data["basic_info"]
    
    return bot_specifics if bot_specifics else None