import asyncio
from src.tools.weather import get_weather, format_weather_info
from src.utils.extract import extract_qq_from_at
from src.tools.brawl import get_club_info, get_player_info

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

def ecy_img() -> str:
    url = "https://api.seaya.link/random?type=file"
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
    if command == "二次元":
        return ecy_img()
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