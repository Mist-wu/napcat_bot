import asyncio
import requests
from src.tools.weather import get_weather, format_weather_info
from src.utils.extract import extract_qq_from_at
from src.tools.brawl import get_club_info, get_player_info
from src.utils.state_manager import state_manager
from src.utils.user_db import user_db
from src.tools.check_student import check_bupt_student
from src.tools.elec import BUPTElecQuerier

def is_command_message(message: str) -> bool:
    return message.startswith("/")

def long_img() -> str:
    url = "https://api.lolimi.cn/API/longt/l.php"
    return f"[CQ:image,url={url}]"

def cat_img() -> str:
    url = "https://edgecats.net/"
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

def pixiv_image() -> str:
    api_url = "https://api.lolicon.app/setu/v2"
    params = {"num": 1}

    resp = requests.get(api_url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if not data or "data" not in data or not data["data"]:
        raise Exception("没有获取到P站图片")
    item = data["data"][0]
    image_url = item["urls"]["original"]
    return image_url

def command_list() -> str:
    cmds = [
        "/指令",
        "/天气 [城市名]",
        "/龙",
        "/猫",
        "/二次元",
        "/咬 [@]",
        "/玩 [@]",
        "/丢 [@]",
        "/撕 [@]",
        "/查玩家 [tag]",
        "/查战队 [tag]",
        "/图",
        "/图图  👈千万别使用",
    ]
    return "可用指令列表：\n" + "\n".join(cmds)

async def handle_command_message(message: str, user_id: str = "", websocket=None) -> str:
    parts = message.strip().split(maxsplit=1)
    command = parts[0][1:].lower()
    args = parts[1].strip() if len(parts) > 1 else ""

    # 认证指令
    if command == "认证":
        state_manager.set_state(user_id, 'AUTH_AWAIT_STUID', {})
        return "请输入学号"

    # 查询电费
    if command == "查询电费":
        if args.strip() == "换宿舍":
            user_db.clear_dorm(user_id)
            # 重新走选宿舍流程
            querier = BUPTElecQuerier()
            await querier.query_electricity_dialog(websocket, user_id)
            return None
        # 检查认证
        auth = user_db.get_auth(user_id)
        if not auth:
            return "请先输入/认证进行身份认证"
        dorm = user_db.get_dorm(user_id)
        if dorm:
            # 先登录再查
            querier = BUPTElecQuerier()
            student_id, password = auth
            await querier.init_session()
            login_ok, login_msg = await querier.login(student_id, password)
            if not login_ok:
                await querier.close_session()
                return f"认证信息失效，请重新/认证。原因：{login_msg}"
            payload = {
                'partmentId': dorm[1],
                'floorId': dorm[2],
                'dromNumber': dorm[3],
                'areaid': dorm[0]
            }
            result = await querier.fetch_api_data("search", payload)
            await querier.close_session()
            if result.get('e') == 0:
                data_obj = result.get('d', {}).get('data', {})
                msg = f"位置：{data_obj.get('parName')} - {dorm[4]}\n剩余金额：{data_obj.get('surplus')} 元\n"
                try:
                    price = float(data_obj.get('price', 0.5))
                    surplus = float(data_obj.get('surplus', 0))
                    msg += f"剩余电量：{round(surplus / price, 2)} 度\n"
                except: pass
                msg += f"总用电量：{data_obj.get('vTotal')} 度\n更新时间：{data_obj.get('time')}"
                return msg
            else:
                return f"查询失败: {result.get('m')}"
        # 没有宿舍信息，走多轮
        querier = BUPTElecQuerier()
        await querier.query_electricity_dialog(websocket, user_id)
        return None

    # 其他原有指令...
    if command in ["指令", "help"]:
        return command_list()
    if command in ["天气", "weather"]:
        if not args:
            return "请在指令后输入城市名，例如：/天气 北京"
        data = await asyncio.to_thread(get_weather, args)
        return format_weather_info(data)
    if command == "龙":
        return long_img()
    if command == "猫":
        return cat_img()
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
    if command == "查玩家":
        if not args:
            return "请在指令后输入玩家tag，例如：/查玩家 2VQ8YQG0"
        data = await asyncio.to_thread(get_player_info, args)
        return data or "未找到玩家信息"
    if command == "查战队":
        if not args:
            return "请在指令后输入战队tag，例如：/查战队 Q2P"
        data = await asyncio.to_thread(get_club_info, args)
        return data or "未找到战队信息"
    if command == "图":
        try:
            img_url = await asyncio.to_thread(pixiv_image)
            return f"[CQ:image,url={img_url}]"
        except Exception as e:
            return f"获取P站图片失败：{e}"
    if command == "图图":
        return f"[CQ:image,url=https://i.pixiv.re/img-original/img/2024/01/08/01/02/08/114981714_p0.png]"

    return "未识别的指令"
