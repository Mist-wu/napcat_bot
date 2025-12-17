import json

async def send_private_text(websocket, user_id, text: str) -> None:
    payload = {
        "action": "send_private_msg",
        "params": {
            "user_id": int(user_id),
            "message": text,
        },
    }
    await websocket.send(json.dumps(payload))

async def send_group_text(websocket, group_id, text: str) -> None:
    payload = {
        "action": "send_group_msg",
        "params": {
            "group_id": int(group_id),
            "message": text,
        },
    }
    await websocket.send(json.dumps(payload))