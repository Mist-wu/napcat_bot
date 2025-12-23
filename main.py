import asyncio
import json
from typing import Any, Dict
import config.config as config
from src.utils.extract import extract_text_from_message, extract_image_urls
from src.utils.output import send_private_text, send_group_text
from src.tools.command import handle_command_message
from src.ai.state_manager import state_manager
from src.ai.user_db import user_db
from src.tools.check_student import check_bupt_student
from src.ai.ai_deepseek import DeepSeekClient
from src.ai.img_recog import process_image_message
from src.ai.context_memory import ContextMemory

target_qq = config.root_user
NAPCAT_HOST = config.napcat_host
NAPCAT_PORT = 3001
NAPCAT_TOKEN = config.napcat_token

ai_client = DeepSeekClient(
    api_key=config.deepseek_api_key,
    api_base="https://api.deepseek.com",
    model="deepseek-chat"
)
context_memory = ContextMemory()

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
    return data.get("card") or data.get("nickname") or str(user_id)

async def handle_private_message(websocket, event, text, image_urls, user_id):
    if config.is_user_blacklisted(user_id):
        return
    if not config.is_user_allowed(user_id):
        return
    # 状态机多轮认证/电费流程
    state, temp_data = state_manager.get_state(user_id)
    if state == 'AUTH_AWAIT_STUID':
        temp_data['student_id'] = text.strip()
        state_manager.set_state(user_id, 'AUTH_AWAIT_PWD', temp_data)
        await send_private_text(websocket, user_id, "请输入密码")
        return
    if state == 'AUTH_AWAIT_PWD':
        temp_data['password'] = text.strip()
        # 校验
        ok, msg = await asyncio.to_thread(check_bupt_student, temp_data['student_id'], temp_data['password'])
        if ok:
            user_db.set_auth(user_id, temp_data['student_id'], temp_data['password'])
            await send_private_text(websocket, user_id, "认证成功")
        else:
            await send_private_text(websocket, user_id, f"认证失败：{msg}")
        state_manager.clear_state(user_id)
        return
    if state.startswith('ELEC_AWAIT_'):
        from src.tools.elec import BUPTElecQuerier
        querier = BUPTElecQuerier()
        # 解析用户输入
        if state == 'ELEC_AWAIT_AREA':
            if text.strip() not in ['1', '2']:
                await send_private_text(websocket, user_id, "请输入1或2")
                return
            temp_data['area_id'] = text.strip()
            await querier.query_electricity_dialog(websocket, user_id, step='area', temp_data=temp_data)
            return
        if state == 'ELEC_AWAIT_PART':
            try:
                idx = int(text.strip()) - 1
                if idx < 0 or idx >= len(temp_data['b_list']):
                    raise Exception()
            except:
                await send_private_text(websocket, user_id, "编号无效，请重新输入")
                return
            temp_data['b_idx'] = idx
            await querier.query_electricity_dialog(websocket, user_id, step='part', temp_data=temp_data)
            return
        if state == 'ELEC_AWAIT_FLOOR':
            try:
                idx = int(text.strip()) - 1
                if idx < 0 or idx >= len(temp_data['f_list']):
                    raise Exception()
            except:
                await send_private_text(websocket, user_id, "编号无效，请重新输入")
                return
            temp_data['f_idx'] = idx
            await querier.query_electricity_dialog(websocket, user_id, step='floor', temp_data=temp_data)
            return
        if state == 'ELEC_AWAIT_DORM':
            try:
                idx = int(text.strip()) - 1
                if idx < 0 or idx >= len(temp_data['d_list']):
                    raise Exception()
            except:
                await send_private_text(websocket, user_id, "编号无效，请重新输入")
                return
            temp_data['d_idx'] = idx
            await querier.query_electricity_dialog(websocket, user_id, step='dorm', temp_data=temp_data)
            return

    # 原有AI/指令逻辑
    await context_memory.add_message('private', user_id, user_id, text)
    n_ctx = await context_memory.count_context('private', user_id)
    if n_ctx > 30:
        await context_memory.summarize_and_shrink('private', user_id, ai_client)
    context_lines = await context_memory.get_context('private', user_id)
    if image_urls:
        reply = await process_image_message(image_urls, ai_client, user_id)
        await context_memory.add_message('private', user_id, "bot", reply)
    elif text.startswith("/"):
        reply = await handle_command_message(text, user_id, websocket)
    elif text:
        ai_input = "\n".join(context_lines + [text])
        reply = await ai_client.call(ai_input)
        await context_memory.add_message('private', user_id, "bot", reply)
    else:
        return
    if reply:
        await send_private_text(websocket, user_id, reply)

async def handle_group_message(websocket, event, text, image_urls, user_id, group_id):
    if config.is_user_blacklisted(user_id):
        return
    if text.startswith("/"):
        if not config.is_group_cmd_allowed(group_id):
            return
        reply = await handle_command_message(text, user_id)
    elif image_urls:
        if not config.is_group_ai_allowed(group_id):
            return
        await context_memory.add_message('group', group_id, user_id, "[图片] " + ' '.join(image_urls))
        n_ctx = await context_memory.count_context('group', group_id)
        if n_ctx > 30:
            await context_memory.summarize_and_shrink('group', group_id, ai_client)
        context_lines = await context_memory.get_context('group', group_id, user_id=user_id, mode="mix")
        reply = await process_image_message(image_urls, ai_client, user_id)
        await context_memory.add_message('group', group_id, "bot", reply)
    elif text:
        if not config.is_group_ai_allowed(group_id):
            return
        await context_memory.add_message('group', group_id, user_id, text)
        n_ctx = await context_memory.count_context('group', group_id)
        if n_ctx > 30:
            await context_memory.summarize_and_shrink('group', group_id, ai_client)
        context_lines = await context_memory.get_context('group', group_id, user_id=user_id, mode="mix")
        ai_input = "\n".join(context_lines + [text])
        reply = await ai_client.call(ai_input)
        await context_memory.add_message('group', group_id, "bot", reply)
    else:
        return
    if reply:
        await send_group_text(websocket, group_id, reply)

async def handle_notice(websocket, event):
    typ = event.get("notice_type")
    group_id = event.get("group_id")
    user_id = event.get("user_id")
    if typ == "group_increase":
        nickname = await get_group_member_nickname(websocket, group_id, user_id)
        welcome_text = f"欢迎 {nickname}（{user_id}）加入本群！"
        await send_group_text(websocket, group_id, welcome_text)
    elif typ == "group_decrease":
        leave_text = f"成员 {user_id} 已离开本群，祝一路顺风！"
        await send_group_text(websocket, group_id, leave_text)

async def handle_event(websocket, event: Dict[str, Any]):
    post_type = event.get("post_type")
    if post_type == "message":
        msg_type = event.get("message_type")
        user_id = str(event.get("user_id", ""))
        group_id = event.get("group_id")
        message = event.get("message")
        text = (event.get("raw_message") or extract_text_from_message(message) or "").strip()
        image_urls = extract_image_urls(message)
        if msg_type == "private":
            await handle_private_message(websocket, event, text, image_urls, user_id)
        elif msg_type == "group":
            await handle_group_message(websocket, event, text, image_urls, user_id, group_id)
    elif post_type == "notice":
        await handle_notice(websocket, event)

async def listen_and_respond():
    await context_memory.initialize()
    uri = f"ws://{NAPCAT_HOST}:{NAPCAT_PORT}/ws"
    headers = {"Authorization": f"Bearer {NAPCAT_TOKEN}"}
    print(f"正在连接到 NapCatQQ 服务器: {uri}")
    try:
        async with __import__("websockets").connect(uri, additional_headers=headers) as websocket:
            print("连接成功，开始监听消息")
            await send_private_text(websocket, target_qq, "Bot成功启动")
            try:
                while True:
                    raw = await websocket.recv()
                    try:
                        event = json.loads(raw)
                    except json.JSONDecodeError:
                        print(f"[警告] 无法解析的消息: {raw}")
                        continue
                    await handle_event(websocket, event)
            except asyncio.CancelledError:
                print("接收到退出信号，安全关闭中...")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(listen_and_respond())
    except KeyboardInterrupt:
        print("主程序接收到Ctrl+C，安全退出。")