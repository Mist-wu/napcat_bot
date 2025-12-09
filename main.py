import asyncio
import json
from typing import Any, Dict, List
import config.config as config
import websockets
from src.ai.ai_module import DeepSeekClient
from src.utils import handler, out

target_qq = config.root_user
NAPCAT_HOST = "178.128.61.90"
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

async def handle_message(websocket, event: Dict[str, Any]) -> None:
    if event.get("post_type") != "message":
        return
    if event.get("message_type") != "private":
        return
    user_id = str(event.get("user_id", ""))
    if user_id != str(target_qq):
        return
    text = (
        event.get("raw_message")
        or extract_text_from_message(event.get("message"))
        or ""
    ).strip()
    if not text:
        return
    reply = await handler.process_private_text(text, ai_client)
    if reply:
        await out.send_private_text(websocket, target_qq, reply)

async def listen_and_respond():
    uri = f"ws://{NAPCAT_HOST}:{NAPCAT_PORT}/ws"
    headers = {"Authorization": f"Bearer {NAPCAT_TOKEN}"}
    print(f"正在连接到 NapCatQQ 服务器: {uri}")
    try:
        async with websockets.connect(uri, additional_headers=headers) as websocket:
            print("连接成功，开始监听消息")
            while True:
                raw = await websocket.recv()
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    print(f"[警告] 无法解析的消息: {raw}")
                    continue
                await handle_message(websocket, event)
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"连接失败，状态码: {e.status_code}")
    except ConnectionRefusedError:
        print(f"连接被拒绝，请检查 {NAPCAT_HOST}:{NAPCAT_PORT} 是否可用")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(listen_and_respond())