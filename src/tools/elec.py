import aiohttp
import re
import json
import asyncio

from src.utils.user_db import user_db
from src.utils.state_manager import state_manager
from src.utils.output import send_private_text

class BUPTElecQuerier:
    def __init__(self):
        self.base_url = "https://app.bupt.edu.cn/buptdf/wap/default/chong"
        self.session = None

    async def init_session(self):
        self.session = aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar())

    async def close_session(self):
        if self.session:
            await self.session.close()

    async def extract_execution(self, html):
        match = re.search(r'<input\s+name="execution"\s+value="([^"]+)"', html)
        return match.group(1) if match else None

    async def login(self, username, password):
        try:
            async with self.session.get(self.base_url, allow_redirects=True) as resp:
                page_text = await resp.text()
                exe = await self.extract_execution(page_text)
                
            if not exe:
                return False, "无法获取登录执行令牌"

            data = {
                'username': username,
                'password': password,
                'submit': '登录',
                'type': 'username_password',
                'execution': exe,
                '_eventId': 'submit',
            }
            
            async with self.session.post(resp.url, data=data, allow_redirects=True) as login_resp:
                final_text = await login_resp.text()
                if "CAS Login" in final_text or "账号或密码错误" in final_text:
                    return False, "登录认证失败"
                return True, "认证成功"
        except Exception as e:
            return False, f"网络错误: {str(e)}"

    async def fetch_api_data(self, endpoint, payload):
        api_url = f"https://app.bupt.edu.cn/buptdf/wap/default/{endpoint}"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': self.base_url,
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        try:
            async with self.session.post(api_url, data=payload, headers=headers) as resp:
                # 检查是否被重定向到登录页（通常意味着 Session 失效）
                if "cas/login" in str(resp.url).lower():
                    return {"e": -2, "m": "Session已过期，请重新登录", "d": {}}
                
                content_type = resp.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    return await resp.json()
                else:
                    # 如果不是 JSON，尝试强行解析，失败则返回错误字典
                    text = await resp.text()
                    try:
                        return json.loads(text)
                    except:
                        return {"e": -1, "m": "服务器返回非JSON格式数据", "d": {"raw": text}}
        except Exception as e:
            return {"e": -1, "m": f"请求异常: {str(e)}", "d": {}}


    async def query_electricity_dialog(self, websocket, user_id, step=None, temp_data=None):
        # step: None/area/part/floor/dorm/search
        # temp_data: dict, 用于存储 area_id, partmentId, floorId
        if temp_data is None:
            temp_data = {}
        # 获取学号密码
        auth = user_db.get_auth(user_id)
        if not auth:
            await send_private_text(websocket, user_id, "请先输入/认证进行身份认证")
            state_manager.clear_state(user_id)
            return
        student_id, password = auth
        await self.init_session()
        login_ok, login_msg = await self.login(student_id, password)
        if not login_ok:
            await send_private_text(websocket, user_id, f"认证信息失效，请重新/认证。原因：{login_msg}")
            await self.close_session()
            state_manager.clear_state(user_id)
            return
        if step is None:
            # 1. 校区选择
            await send_private_text(websocket, user_id, "请选择校区:\n1. 西土城校区\n2. 沙河校区\n请回复数字(1/2)")
            state_manager.set_state(user_id, 'ELEC_AWAIT_AREA', temp_data)
            await self.close_session()
            return
        if step == 'area':
            area_id = temp_data.get('area_id')
            res = await self.fetch_api_data("part", {"areaid": area_id})
            b_list = res.get('d', {}).get('data', [])
            if not b_list:
                await send_private_text(websocket, user_id, f"获取楼栋失败: {res.get('m', '未知错误')}")
                await self.close_session()
                state_manager.clear_state(user_id)
                return
            temp_data['b_list'] = b_list
            msg = "请选择公寓楼:\n" + "\n".join([f"{i+1}. {b.get('partmentName')}" for i, b in enumerate(b_list)])
            await send_private_text(websocket, user_id, msg + "\n请回复编号")
            state_manager.set_state(user_id, 'ELEC_AWAIT_PART', temp_data)
            await self.close_session()
            return
        if step == 'part':
            b_list = temp_data['b_list']
            b_idx = temp_data.get('b_idx')
            selected_partment_id = b_list[b_idx]['partmentId']
            temp_data['partmentId'] = selected_partment_id
            res = await self.fetch_api_data("floor", {"areaid": temp_data['area_id'], "partmentId": selected_partment_id})
            f_list = res.get('d', {}).get('data', [])
            if not f_list:
                await send_private_text(websocket, user_id, f"获取楼层失败: {res.get('m', '未知错误')}")
                await self.close_session()
                state_manager.clear_state(user_id)
                return
            temp_data['f_list'] = f_list
            msg = "请选择楼层:\n" + "\n".join([f"{i+1}. {f.get('floorName')}" for i, f in enumerate(f_list)])
            await send_private_text(websocket, user_id, msg + "\n请回复编号")
            state_manager.set_state(user_id, 'ELEC_AWAIT_FLOOR', temp_data)
            await self.close_session()
            return
        if step == 'floor':
            f_list = temp_data['f_list']
            f_idx = temp_data.get('f_idx')
            selected_floor_id = f_list[f_idx]['floorId']
            temp_data['floorId'] = selected_floor_id
            res = await self.fetch_api_data("drom", {
                "areaid": temp_data['area_id'],
                "partmentId": temp_data['partmentId'],
                "floorId": selected_floor_id
            })
            if not isinstance(res, dict):
                await send_private_text(websocket, user_id, "错误：宿舍接口返回数据格式异常")
                await self.close_session()
                state_manager.clear_state(user_id)
                return
            d_list = res.get('d', {}).get('data', [])
            if not d_list:
                await send_private_text(websocket, user_id, f"该楼层没有宿舍数据或接口报错: {res.get('m')}")
                await self.close_session()
                state_manager.clear_state(user_id)
                return
            temp_data['d_list'] = d_list
            msg = "请选择宿舍:\n" + "\n".join([f"{i+1}. {d.get('dromName')}" for i, d in enumerate(d_list)])
            await send_private_text(websocket, user_id, msg + "\n请回复编号")
            state_manager.set_state(user_id, 'ELEC_AWAIT_DORM', temp_data)
            await self.close_session()
            return
        if step == 'dorm':
            d_list = temp_data['d_list']
            d_idx = temp_data.get('d_idx')
            selected_dorm = d_list[d_idx]
            # 查询电费
            search_payload = {
                'partmentId': temp_data['partmentId'],
                'floorId': temp_data['floorId'],
                'dromNumber': selected_dorm.get('dromNum'),
                'areaid': temp_data['area_id']
            }
            result = await self.fetch_api_data("search", search_payload)
            await self.close_session()
            if result.get('e') == 0:
                data_obj = result.get('d', {}).get('data', {})
                msg = f"位置：{data_obj.get('parName')} - {data_obj.get('dromName')}\n剩余金额：{data_obj.get('surplus')} 元\n"
                try:
                    price = float(data_obj.get('price', 0.5))
                    surplus = float(data_obj.get('surplus', 0))
                    msg += f"剩余电量：{round(surplus / price, 2)} 度\n"
                except: pass
                msg += f"总用电量：{data_obj.get('vTotal')} 度\n更新时间：{data_obj.get('time')}"
                await send_private_text(websocket, user_id, msg)
                # 存储宿舍信息
                user_db.set_dorm(user_id, temp_data['area_id'], temp_data['partmentId'], temp_data['floorId'], selected_dorm.get('dromNum'), selected_dorm.get('dromName'))
                state_manager.clear_state(user_id)
            else:
                await send_private_text(websocket, user_id, f"查询失败: {result.get('m')}")
                state_manager.clear_state(user_id)
            return

if __name__ == "__main__":
    querier = BUPTElecQuerier()
    try:
        asyncio.run(querier.run_interactive())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n[运行异常]: {e}")