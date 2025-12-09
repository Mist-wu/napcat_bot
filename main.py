import asyncio
import json
from typing import Any, Dict, List
import config.config as config
import websockets
from src.ai.ai_module import DeepSeekClient as DeepSeekClient  # 引入分离的 AI 模块

# --- 配置信息 ---
target_qq = config.root_user  # 仅响应此 QQ 的私聊消息
NAPCAT_HOST = "178.128.61.90"
NAPCAT_PORT = 3001
NAPCAT_TOKEN = config.napcat_token

DEEPSEEK_API_KEY = config.deepseek_api_key
DEEPSEEK_API_BASE = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# 初始化 AI 客户端
ai_client = DeepSeekClient(
    api_key=DEEPSEEK_API_KEY,
    api_base=DEEPSEEK_API_BASE,
    model=DEEPSEEK_MODEL
)

def extract_text_from_message(message: Any) -> str:
    """
    从 NapCat (OneBot) 消息结构中提取纯文本：
    - 字符串直接返回
    - 段列表拼接 text 字段
    """
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
    """
    处理来自 NapCat 的事件，仅响应来自 target_qq 的私聊文本消息。
    """
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

    print(f"[收到] 来自 {user_id} 的消息: {text}")

    ai_reply = await ai_client.call(text)
    print(f"[AI 回复] {ai_reply}")

    reply_payload = {
        "action": "send_private_msg",
        "params": {
            "user_id": int(target_qq),
            "message": ai_reply,
        },
    }
    await websocket.send(json.dumps(reply_payload))


async def listen_and_respond():
    """
    连接 NapCatQQ WebSocket，监听消息并基于 DeepSeek 回复指定 QQ 用户。
    """
    uri = f"ws://{NAPCAT_HOST}:{NAPCAT_PORT}/ws"
    headers = {"Authorization": f"Bearer {NAPCAT_TOKEN}"}

    print(f"正在连接到 NapCatQQ 服务器: {uri}")
    if NAPCAT_TOKEN:
        print("已配置访问令牌 (Token)。")
    else:
        print("未配置访问令牌 (Token)，若服务器启用鉴权请先填入。")

    try:
        async with websockets.connect(uri, additional_headers=headers) as websocket:
            print("连接成功！开始监听来自指定 QQ 的消息……")

            while True:
                raw = await websocket.recv()
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    print(f"[警告] 无法解析的消息: {raw}")
                    continue

                await handle_message(websocket, event)

    except websockets.exceptions.InvalidStatusCode as e:
        if e.status_code == 401:
            print(
                f"连接失败：身份验证错误 (Unauthorized)。"
                f"请检查 Token (当前为: '{NAPCAT_TOKEN}') 是否正确。"
            )
        else:
            print(f"连接失败，服务器返回 HTTP 状态码: {e.status_code}")
    except ConnectionRefusedError:
        print(f"连接被拒绝。请确保 NapCatQQ 正在 {NAPCAT_HOST}:{NAPCAT_PORT} 上运行。")
    except Exception as e:
        print(f"发生未知错误: {e}")


if __name__ == "__main__":
    asyncio.run(listen_and_respond())