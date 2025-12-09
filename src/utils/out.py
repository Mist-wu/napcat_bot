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