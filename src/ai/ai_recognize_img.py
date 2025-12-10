import aiohttp

async def recognize_image(url: str) -> str:
    api_url = f"https://api.pearktrue.cn/api/airecognizeimg?file={url}"
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as resp:
            data = await resp.json()
            if data.get("code") == 200:
                return data.get("result", "")
            else:
                return f"图片识别失败：{data.get('msg', '未知错误')}"