import asyncio
from src.tools.weather import get_weather, format_weather_info
from src.ai.ai_recognize_img import recognize_image

def is_command_message(message: str) -> bool:
    return message.startswith("/")

def long_img() -> str:
    url = "https://api.lolimi.cn/API/longt/l.php"
    return f"[CQ:image,url={url}]"

def cat_img() -> str:
    url = "https://edgecats.net/"
    return f"[CQ:image,url={url}]"

def baisi_img() -> str:
    url = "https://v2.xxapi.cn/api/baisi?return=302"
    return f"[CQ:image,url={url}]"

def bite_img(id: str) -> str:
    url = f"https://api.lolimi.cn/API/face_suck/api.php?QQ={id}"
    return f"[CQ:image,url={url}]"

def play_img(id: str) -> str:
    url = f"https://api.lolimi.cn/API/face_play/api.php?QQ={id}"
    return f"[CQ:image,url={url}]"

def diu_img(id: str) -> str:
    url = f"https://api.lolimi.cn/API/diu/api.php?QQ={id}"
    return f"[CQ:image,url={url}]"

def si_img(id: str) -> str:
    url = f"https://api.lolimi.cn/API/si/api.php?QQ={id}"
    return f"[CQ:image,url={url}]"

def extract_qq_from_at(text: str) -> str:
    import re
    m = re.search(r"\[CQ:at,qq=(\d+)\]", text)
    if m:
        return m.group(1)
    m = re.search(r"@(\d{5,12})", text)
    if m:
        return m.group(1)
    return None

def extract_image_urls(message):
    urls = []
    if isinstance(message, list):
        for seg in message:
            if isinstance(seg, dict) and seg.get("type") in ["image", "face"]:
                img_url = seg.get("data", {}).get("url")
                if img_url:
                    urls.append(img_url)
    return urls

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
    if command == "猫":
        return cat_img()
    if command == "白丝":
        return baisi_img()
    if command == "咬":
        qq = extract_qq_from_at(args) if args else None
        if not qq:
            qq = user_id
        return bite_img(qq)
    if command == "玩":
        qq = extract_qq_from_at(args) if args else None
        if not qq:
            qq = user_id
        return play_img(qq)
    if command == "丢":
        qq = extract_qq_from_at(args) if args else None
        if not qq:
            qq = user_id
        return diu_img(qq)
    if command == "撕":
        qq = extract_qq_from_at(args) if args else None
        if not qq:
            qq = user_id
        return si_img(qq)
    return "未识别的指令"

async def process_private_text(message, ai_client, user_id: str = "") -> str:
    if is_command_message(message):
        return await handle_command_message(message, user_id)
    return await ai_client.call(message)

async def process_image_message(image_urls, ai_client, user_id: str = "") -> str:
    print(f"[图片识别] 收到图片url列表: {image_urls}")
    result_list = []
    for url in image_urls:
        print(f"[图片识别] 开始识别: {url}")
        result = await recognize_image(url)
        print(f"[图片识别] 单张识别结果: {result}")
        result_list.append(result)
    recog = "\n".join(result_list)
    print(f"[图片识别] 全部识别结果拼接: {recog}")
    prompt = f"用户发送了一张图片，图片内容识别为：{recog}"
    print(f"[图片识别] 送入AI生成的消息内容: {prompt}")
    reply = await ai_client.call(prompt)
    print(f"[图片识别] AI最终回复: {reply}")
    return reply