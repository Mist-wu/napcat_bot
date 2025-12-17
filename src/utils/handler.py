from src.utils.extract import extract_image_urls, extract_text_from_message
from src.tools.command import handle_image_api
from src.tools.weather import get_weather, format_weather_info
from src.ai.img_recog import recognize_image

async def handle_command(msg: str, user_id: str, weather_api_key: str):
    parts = msg.lstrip("/").split(maxsplit=1)
    command, *args = parts if parts else (msg, [])
    args = args[0] if args else ""
    # 指令优先匹配图片API
    img_result = handle_image_api(command, user_id, args)
    if img_result:
        return img_result
    if command in {"天气", "weather"}:
        if not args:
            return "请在指令后输入城市名，例如：/天气 北京"
        data = await asyncio.to_thread(get_weather, args, weather_api_key)
        return format_weather_info(data)
    return "未识别的指令"

async def process_private_text(msg, ai_client, user_id, weather_api_key):
    if msg.startswith("/"):
        return await handle_command(msg, user_id, weather_api_key)
    return await ai_client.call(msg)

async def process_image_message(image_urls, ai_client, user_id):
    recog_tasks = [recognize_image(url) for url in image_urls]
    recog_results = await asyncio.gather(*recog_tasks)
    prompt = f"用户发送了一张图片，图片内容识别为：{'；'.join(recog_results)}"
    return await ai_client.call(prompt)