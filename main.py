import asyncio
import json
from typing import Any, Dict, List
import config.config as config
import websockets
from src.ai.ai_module import DeepSeekClient
from src.utils import handler, out
import aiohttp

target_qq = config.root_user
NAPCAT_HOST = config.napcat_host
NAPCAT_PORT = 3001
NAPCAT_TOKEN = config.napcat_token

DEEPSEEK_API_KEY = config.deepseek_api_key
DEEPSEEK_API_BASE = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

ai_client = DeepSeekClient(
    api_key=DEEPSEEK_API_KEY,
    api_base=DEEPSEEK_API_BASE,
    model=DEEPSEEK_MODEL
)

def extract_text_from_message(message: Any) -> str:
    if isinstance(message, str):
        return message
    if isinstance(message, list):
        parts: List[str] = []
        for seg in message:
            if isinstance(seg, dict) and seg.get("type") == "text":
                parts.append(str(seg.get("data", {}).get("text", "")))
        return "".join(parts)
    return ""

def extract_image_urls(message: Any) -> List[str]:
    urls = []
    if isinstance(message, list):
        for seg in message:
            if isinstance(seg, dict) and seg.get("type") in ["image", "face"]:
                img_url = seg.get("data", {}).get("url")
                if img_url:
                    urls.append(img_url)
    print(urls)
    return urls

async def get_group_member_nickname(websocket, group_id: int, user_id: int) -> str:
    payload = {
        "action": "get_group_member_info",
        "params": {"group_id": group_id, "user_id": user_id},
    }
    await websocket.send(json.dumps(payload))
    resp_raw = await websocket.recv()
    try:
        resp = json.loads(resp_raw)
    except Exception:
        print(f"获取群成员昵称失败，无法解析响应: {resp_raw}")
        return str(user_id)
    data = resp.get("data", {})
    nickname = data.get("card") or data.get("nickname") or str(user_id)
    print(f"获取群成员昵称: {nickname}")
    return nickname

async def handle_message(websocket, event: Dict[str, Any]) -> None:
    if event.get("post_type") == "message":
        msg_type = event.get("message_type")
        if msg_type not in ["private", "group"]:
            return
        user_id = str(event.get("user_id", ""))
        if user_id != str(target_qq):
            return
        message = event.get("message")
        text = (
            event.get("raw_message")
            or extract_text_from_message(message)
            or ""
        ).strip()
        image_urls = extract_image_urls(message)

        if image_urls:
            reply = await handler.process_image_message(image_urls, ai_client, user_id)
        else:
            if not text:
                return
            reply = await handler.process_private_text(text, ai_client, user_id)
        if not reply:
            return
        if msg_type == "private":
            await out.send_private_text(websocket, target_qq, reply)
        elif msg_type == "group":
            group_id = event.get("group_id")
            if group_id:
                await out.send_group_text(websocket, group_id, reply)
        return

    # 群成员变动事件（加群/退群）
    if event.get("post_type") == "notice":
        notice_type = event.get("notice_type")
        group_id = event.get("group_id")
        user_id = event.get("user_id")
        if notice_type == "group_increase":  # 新成员加群)
            nickname = await get_group_member_nickname(websocket, group_id, user_id)
            welcome_text = f"欢迎 {nickname}（{user_id}）加入本群！"
            await out.send_group_text(websocket, group_id, welcome_text)
        elif notice_type == "group_decrease":  # 成员退群
            leave_text = f"成员 {user_id} 已离开本群，祝一路顺风！"
            await out.send_group_text(websocket, group_id, leave_text)
        return

async def listen_and_respond():
    uri = f"ws://{NAPCAT_HOST}:{NAPCAT_PORT}/ws"
    headers = {"Authorization": f"Bearer {NAPCAT_TOKEN}"}
    print(f"正在连接到 NapCatQQ 服务器: {uri}")
    try:
        async with websockets.connect(uri, additional_headers=headers) as websocket:
            print("连接成功，开始监听消息")
            await out.send_private_text(websocket, target_qq, "Bot成功启动")
            try:
                while True:
                    raw = await websocket.recv()
                    try:
                        event = json.loads(raw)
                    except json.JSONDecodeError:
                        print(f"[警告] 无法解析的消息: {raw}")
                        continue
                    await handle_message(websocket, event)
            except asyncio.CancelledError:
                print("接收到退出信号，安全关闭中...")
    except websockets.InvalidStatusCode as e:
        print(f"连接失败，状态码: {e.status_code}")
    except ConnectionRefusedError:
        print(f"连接被拒绝，请检查 {NAPCAT_HOST}:{NAPCAT_PORT} 是否可用")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(listen_and_respond())
    except KeyboardInterrupt:
        print("主程序接收到Ctrl+C，安全退出。")