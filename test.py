import asyncio
import json
from typing import Any, Dict, List
import config.config as config
import websockets

target_qq = config.root_user
NAPCAT_HOST = config.napcat_host
NAPCAT_PORT = 3001
NAPCAT_TOKEN = config.napcat_token

def extract_image_urls(message: Any) -> List[str]:
    urls = []
    if isinstance(message, list):
        for seg in message:
            if isinstance(seg, dict) and seg.get("type") == "image":
                img_url = seg.get("data", {}).get("url")
                if img_url:
                    urls.append(img_url)
    return urls

async def handle_message(event: Dict[str, Any]):
    if event.get("post_type") != "message":
        return

    message_type = event.get("message_type")
    message = event.get("message")
    image_urls = extract_image_urls(message)
    if not image_urls:
        return

    if message_type == "private":
        user_id = event.get("user_id")
        print(f"收到私聊图片消息，QQ：{user_id}")
        for url in image_urls:
            print("图片url:", url)

    elif message_type == "group":
        group_id = event.get("group_id")
        user_id = event.get("user_id")
        print(f"收到群聊图片消息，群:{group_id} 发信人:{user_id}")
        for url in image_urls:
            print("图片url:", url)

async def listen_image_url():
    uri = f"ws://{NAPCAT_HOST}:{NAPCAT_PORT}/ws"
    headers = {"Authorization": f"Bearer {NAPCAT_TOKEN}"}
    print(f"测试监听Napcat服务器: {uri}")
    try:
        async with websockets.connect(uri, additional_headers=headers) as websocket:
            print("连接成功，等待图片消息...")
            while True:
                raw = await websocket.recv()
                try:
                    event = json.loads(raw)
                except Exception:
                    print(f"无法解析消息：{raw}")
                    continue
                await handle_message(event)
    except Exception as e:
        print(f"Websocket连接失败: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(listen_image_url())
    except KeyboardInterrupt:
        print("退出。")
