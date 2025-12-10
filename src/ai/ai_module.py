import asyncio
from openai import OpenAI

class DeepSeekClient:
    """
    封装 DeepSeek（兼容 OpenAI SDK）的调用逻辑。
    - 同步方法：_call_sync（内部使用）
    - 异步方法：call（外部调用）
    """

    def __init__(self, api_key: str, api_base: str, model: str):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self._client = None

    def _ensure_client(self) -> None:
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key, base_url=self.api_base)

    def _call_sync(self, user_text: str) -> str:
        """
        同步调用。供异步封装通过线程调用。
        """
        if not self.api_key:
            return "（未配置 DEEPSEEK_API_KEY，无法生成回复）"

        self._ensure_client()

        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个名叫走不完的路的QQ用户，语言风格模仿贴吧。不要出现叼烟等不文明语言"},
                    {"role": "user", "content": user_text},
                ],
                stream=False,
                temperature=0.7,
            )
            content = (
                resp.choices[0].message.content
                if resp.choices and resp.choices[0].message
                else ""
            )
            return content.strip() if content else "（AI 无回复内容）"
        except Exception as e:
            return f"（AI 调用失败：{e}）"

    async def call(self, user_text: str) -> str:
        """
        异步封装，在线程池中调用同步方法，避免阻塞事件循环。
        """
        return await asyncio.to_thread(self._call_sync, user_text)