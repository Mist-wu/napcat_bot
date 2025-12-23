import aiohttp
import re
import json
import asyncio

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

    async def run_interactive(self):
        print("=== 北邮电费查询系统 ===")
        acc = input("请输入学号: ")
        pwd = input("请输入密码: ")

        await self.init_session()
        
        try:
            success, msg = await self.login(acc, pwd)
            if not success:
                print(f"错误: {msg}")
                return

            # 1. 选择校区
            print("\n[1] 选择校区:\n1. 西土城校区\n2. 沙河校区")
            area_id = input("请选择 (1/2): ")

            # 2. 获取公寓楼
            res = await self.fetch_api_data("part", {"areaid": area_id})
            b_list = res.get('d', {}).get('data', [])
            if not b_list:
                print(f"获取楼栋失败: {res.get('m', '未知错误')}")
                return

            print("\n[2] 请选择公寓楼:")
            for i, b in enumerate(b_list):
                print(f"{i+1}. {b.get('partmentName')}")
            b_idx = int(input("请输入编号: ")) - 1
            selected_partment_id = b_list[b_idx]['partmentId']

            # 3. 获取楼层
            res = await self.fetch_api_data("floor", {"areaid": area_id, "partmentId": selected_partment_id})
            f_list = res.get('d', {}).get('data', [])
            if not f_list:
                print(f"获取楼层失败: {res.get('m', '未知错误')}")
                return

            print("\n[3] 请选择楼层:")
            for i, f in enumerate(f_list):
                print(f"{i+1}. {f.get('floorName')}")
            f_idx = int(input("请输入编号: ")) - 1
            selected_floor_id = f_list[f_idx]['floorId']

            # 4. 获取宿舍
            res = await self.fetch_api_data("drom", {
                "areaid": area_id, 
                "partmentId": selected_partment_id, 
                "floorId": selected_floor_id
            })
            
            # 关键防御：确保 res 是字典
            if not isinstance(res, dict):
                print("错误：宿舍接口返回数据格式异常")
                return

            d_list = res.get('d', {}).get('data', [])
            if not d_list:
                print(f"该楼层没有宿舍数据或接口报错: {res.get('m')}")
                return

            print("\n[4] 请选择宿舍:")
            for i, d in enumerate(d_list):
                print(f"{i+1}. {d.get('dromName')}")
            
            d_idx = int(input("请输入编号: ")) - 1
            selected_dorm = d_list[d_idx]
            
            # 5. 查询结果
            print("\n正在查询电费详情...")
            search_payload = {
                'partmentId': selected_partment_id,
                'floorId': selected_floor_id,
                'dromNumber': selected_dorm.get('dromNum'),
                'areaid': area_id
            }
            
            result = await self.fetch_api_data("search", search_payload)
            
            if result.get('e') == 0:
                data_obj = result.get('d', {}).get('data', {})
                print("\n" + "★"*20)
                print(f"位置：{data_obj.get('parName')} - {data_obj.get('dromName')}")
                print(f"剩余金额：{data_obj.get('surplus')} 元")
                try:
                    price = float(data_obj.get('price', 0.5))
                    surplus = float(data_obj.get('surplus', 0))
                    print(f"剩余电量：{round(surplus / price, 2)} 度")
                except: pass
                print(f"总用电量：{data_obj.get('vTotal')} 度")
                print(f"更新时间：{data_obj.get('time')}")
                print("★"*20)
            else:
                print(f"\n查询失败: {result.get('m')}")

        finally:
            await self.close_session()

if __name__ == "__main__":
    querier = BUPTElecQuerier()
    try:
        asyncio.run(querier.run_interactive())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n[运行异常]: {e}")