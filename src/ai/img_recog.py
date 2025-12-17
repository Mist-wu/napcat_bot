import aiohttp

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
    result_list = []
    for url in image_urls:
        result = await recognize_image(url)
        result_list.append(result)
    recog = "\n".join(result_list)
    prompt = f"用户发送了一张图片，图片内容识别为：{recog}"
    reply = await ai_client.call(prompt)
    return reply