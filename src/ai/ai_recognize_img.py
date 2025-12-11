import aiohttp

async def recognize_image(url: str) -> str:
    """
    使用 pearktrue.cn 图片识别 API，对指定图片 URL 进行识别。
    正确使用 POST，JSON 方式传入 {"file": 图片链接}
    """
    api_url = "https://api.pearktrue.cn/api/airecognizeimg/"
    payload = {"file": url}
    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, json=payload) as resp:
            try:
                data = await resp.json()
            except Exception as e:
                return f"图片识别失败：接口返回异常 {e}"
            if data.get("code") == 200:
                return data.get("result", "")
            if data.get("code") == 203:
                print('不支持识别动图')
                return "是动图，暂不支持识别"
            else:
                return f"图片识别失败：{data.get('msg', '未知错误')}"
            
if __name__ == "__main__":
    import asyncio

    test_url = "https://th.bing.com/th/id/OSK.HERO8XH_s8vodPa3VIQliZrFNwgvD9pQ3xob2vslQY6YQrM?w=296&h=176&c=1&rs=2&o=6&cb=ucfimg1&dpr=2&pid=SANGAM&ucfimg=1"
    result = asyncio.run(recognize_image(test_url))
    print("识别结果：", result)