import asyncio
from src.tools.weather import get_weather, format_weather_info

def is_command_message(message: str) -> bool:
    return message.startswith("/")

async def handle_command_message(message: str) -> str:
    parts = message.strip().split(maxsplit=1)
    command = parts[0][1:].lower()
    args = parts[1].strip() if len(parts) > 1 else ""
    if command in ["天气", "weather"]:
        if not args:
            return "请在指令后输入城市名，例如：/天气 北京"
        data = await asyncio.to_thread(get_weather, args)
        return format_weather_info(data)
    return "未识别的指令"

async def process_private_text(message: str, ai_client) -> str:
    if is_command_message(message):
        return await handle_command_message(message)
    return await ai_client.call(message)