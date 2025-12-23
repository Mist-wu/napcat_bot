import aiohttp
import re
import json
import asyncio
import urllib.parse
from yarl import URL

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

    async def fetch_api_data(self, endpoint, payload):
        api_url = f"https://app.bupt.edu.cn/buptdf/wap/default/{endpoint}"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': self.base_url,
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        async with self.session.post(api_url, data=payload, headers=headers) as resp:
            # 增加对非 JSON 响应的处理，防止崩溃
            content_type = resp.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                return await resp.json()
            else:
                raw_text = await resp.text()
                print(f"调试：服务器返回了非JSON内容 (Status: {resp.status})")
                return {"e": -1, "m": "服务器响应格式错误", "d": raw_text}

    async def run_interactive(self):
        print("=== 北邮电费查询系统 (Terminal 版) ===")
        acc = input("请输入学号: ")
        pwd = input("请输入密码: ")

        await self.init_session()
        
        success, msg = await self.login(acc, pwd)
        if not success:
            print(f"错误: {msg}")
            await self.close_session()
            return

        # 1. 选择校区
        print("\n[1] 选择校区:\n1. 西土城校区\n2. 沙河校区")
        area_id = input("请选择 (1/2): ")

        # 2. 获取并选择公寓楼
        buildings = await self.fetch_api_data("part", {"areaid": area_id})
        b_list = buildings['d']['data']
        print("\n[2] 请选择公寓楼:")
        for i, b in enumerate(b_list):
            print(f"{i+1}. {b['partmentName']}")
        b_idx = int(input("请输入编号: ")) - 1
        selected_partment_id = b_list[b_idx]['partmentId']

        # 3. 获取并选择楼层
        floors = await self.fetch_api_data("floor", {"areaid": area_id, "partmentId": selected_partment_id})
        f_list = floors['d']['data']
        print("\n[3] 请选择楼层:")
        for i, f in enumerate(f_list):
            print(f"{i+1}. {f['floorName']}")
        f_idx = int(input("请输入编号: ")) - 1
        selected_floor_id = f_list[f_idx]['floorId']

        # 4. 获取并选择宿舍
        dorms = await self.fetch_api_data("drom", {
            "areaid": area_id, 
            "partmentId": selected_partment_id, 
            "floorId": selected_floor_id
        })
        d_list = dorms['d']['data']
        print("\n[4] 请选择宿舍:")
        for i, d in enumerate(d_list):
            print(f"{i+1}. {d['dromName']}")
        d_idx = int(input("请输入编号: ")) - 1
        selected_drom_num = d_list[d_idx]['dromNum'] # 这里从 API 获取的是 dromNum

        # 5. 查询结果 - 严格匹配你补充的负载信息
        print("\n正在查询电费详情...")
        search_payload = {
            'partmentId': selected_partment_id, # 改为 partmentId
            'floorId': selected_floor_id,
            'dromNumber': selected_drom_num,    # 改为 dromNumber
            'areaid': area_id                  # 增加 areaid
        }
        
        result = await self.fetch_api_data("search", search_payload)
        
        if result.get('e') == 0:
            data_obj = result['d']['data']
            print("\n" + "★"*15)
            print(f"位置：{data_obj.get('parName')} {data_obj.get('floorName')}")
            print(f"剩余金额：{data_obj.get('surplus')} 元")
            print(f"剩余电量：{round(float(data_obj.get('surplus', 0)) / float(data_obj.get('price', 1)), 2)} 度")
            print(f"总用电量：{data_obj.get('vTotal')} 度")
            print(f"更新时间：{data_obj.get('time')}")
            print("★"*15)
        else:
            print(f"\n查询失败")
            print(f"状态码: {result.get('e')}")
            print(f"消息: {result.get('m')}")

        await self.close_session()

if __name__ == "__main__":
    querier = BUPTElecQuerier()
    try:
        asyncio.run(querier.run_interactive())
    except KeyboardInterrupt:
        pass