import aiohttp
import asyncio

async def recognize_image(url: str) -> str:
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
                return "是动图，暂不支持识别"
            else:
                return f"图片识别失败：{data.get('msg', '未知错误')}"

async def process_image_message(image_urls, ai_client, user_id: str = "") -> str:
    recog_results = await asyncio.gather(*(recognize_image(url) for url in image_urls))
    recog = "\n".join(recog_results)
    prompt = f"用户发送了一张图片，图片内容识别为：{recog}"
    reply = await ai_client.call(prompt)
    return reply