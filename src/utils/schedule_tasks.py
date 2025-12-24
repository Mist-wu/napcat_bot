import asyncio
import aiosqlite
from datetime import datetime
from src.utils.user_db import user_db
from src.tools.weather import get_weather, format_weather_info
from src.tools.elec import BUPTElecQuerier
from src.utils.output import send_private_text

# 需传入websocket对象
async def send_weather_reports(websocket):
    async with aiosqlite.connect(user_db.db_path) as db:
        async with db.execute("SELECT user_id, weather_report_location FROM user_configs WHERE weather_report_enabled=1 AND weather_report_location IS NOT NULL") as cursor:
            async for row in cursor:
                user_id, location = row
                data = await asyncio.to_thread(get_weather, location)
                msg = format_weather_info(data)
                await send_private_text(websocket, user_id, f"【每日天气播报】\n{msg}")

async def send_elec_alerts(websocket):
    async with aiosqlite.connect(user_db.db_path) as db:
        async with db.execute("SELECT user_id FROM user_configs WHERE elec_alert_enabled=1") as cursor:
            async for row in cursor:
                user_id = row[0]
                dorm = user_db.get_dorm(user_id)
                auth = user_db.get_auth(user_id)
                if not dorm or not auth:
                    continue
                querier = BUPTElecQuerier()
                await querier.init_session()
                login_ok, _ = await querier.login(auth[0], auth[1])
                if not login_ok:
                    await querier.close_session()
                    continue
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
                    try:
                        surplus = float(data_obj.get('surplus', 0))
                    except:
                        continue
                    if surplus < 10:
                        await send_private_text(websocket, user_id, f"宿舍电费余额：{data_obj.get('surplus')}，请及时充值")

# 定时调度主入口（需在主程序中集成websocket对象）
async def schedule_loop(websocket):
    while True:
        now = datetime.now()
        # 6点整电费预警
        if now.hour == 6 and now.minute == 0:
            await send_elec_alerts(websocket)
        # 7点整天气播报
        if now.hour == 7 and now.minute == 0:
            await send_weather_reports(websocket)
        await asyncio.sleep(60)
