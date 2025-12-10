import asyncio
from src.tools.weather import get_weather, format_weather_info

def is_command_message(message: str) -> bool:
    return message.startswith("/")

def long_img() -> str:
    # 返回CQ码图片
    url = "https://api.lolimi.cn/API/longt/l.php"
    return f"[CQ:image,url={url}]"

def bite_img(id: str) -> str:
    url = f"https://api.lolimi.cn/API/face_suck/api.php?QQ={id}"
    return f"[CQ:image,url={url}]"

def extract_qq_from_at(text: str) -> str:
    # [CQ:at,qq=xxx] 或 @xxx
    import re
    m = re.search(r"\[CQ:at,qq=(\d+)\]", text)
    if m:
        return m.group(1)
    m = re.search(r"@(\d{5,12})", text)
    if m:
        return m.group(1)
    return None

async def handle_command_message(message: str, user_id: str = "") -> str:
    parts = message.strip().split(maxsplit=1)
    command = parts[0][1:].lower()
    args = parts[1].strip() if len(parts) > 1 else ""
    if command in ["天气", "weather"]:
        if not args:
            return "请在指令后输入城市名，例如：/天气 北京"
        data = await asyncio.to_thread(get_weather, args)
        return format_weather_info(data)
    if command == "龙图":
        return long_img()
    if command == "咬":
        qq = extract_qq_from_at(args) if args else None
        if not qq:
            qq = user_id
        return bite_img(qq)
    return "未识别的指令"

async def process_private_text(message: str, ai_client, user_id: str = "") -> str:
    if is_command_message(message):
        return await handle_command_message(message, user_id)
    return await ai_client.call(message)