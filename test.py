import asyncio
import json
from typing import Any, Dict, List
import config.config as config

import websockets
from openai import OpenAI

# --- 配置信息 ---
target_qq = config.root_user  # 仅响应此 QQ 的私聊消息
print(f"目标 QQ：{target_qq}")
NAPCAT_HOST = "localhost"
NAPCAT_PORT = 3001
NAPCAT_TOKEN = ""  # 您的 NapCat 访问令牌

# DeepSeek / OpenAI SDK 设置（需提前在环境变量中配置 DEEPSEEK_API_KEY）
DEEPSEEK_API_KEY = config.deepseek_api_key
DEEPSEEK_API_BASE = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"
# -----------------


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


def _call_deepseek_sync(user_text: str) -> str:
    """
    同步调用 DeepSeek（OpenAI SDK 兼容），不保留上下文。
    注意：该函数为同步方法，外部通过 asyncio.to_thread 调用。
    """
    if not DEEPSEEK_API_KEY:
        return "（未配置 DEEPSEEK_API_KEY，无法生成回复）"

    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_API_BASE,
    )

    try:
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是一个友好的 QQ 聊天机器人。"},
                {"role": "user", "content": user_text},
            ],
            stream=False,
            temperature=0.7,
        )
        content = (
            resp.choices[0].message.content
            if resp.choices and resp.choices[0].message
            else ""
        )
        return content.strip() if content else "（AI 无回复内容）"
    except Exception as e:
        return f"（AI 调用失败：{e}）"


async def call_ai(user_text: str) -> str:
    """
    异步封装，在线程池中调用同步 DeepSeek SDK，避免阻塞事件循环。
    """
    return await asyncio.to_thread(_call_deepseek_sync, user_text)


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

    ai_reply = await call_ai(text)
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