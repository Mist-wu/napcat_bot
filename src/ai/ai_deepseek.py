from openai import OpenAI
from src.ai.llm_client import LLMClient

class DeepSeekClient(LLMClient):
    def __init__(self, api_key: str, api_base: str, model: str):
        super().__init__(api_key, api_base, model)
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key, base_url=self.api_base)

    def _call_sync(self, user_text: str) -> str:
        if not self.api_key:
            return "（未配置 DEEPSEEK_API_KEY，无法生成回复）"
        self._ensure_client()
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "作为聊天伙伴与用户交流。"
                            "答案应简明、有条理，不要使用markdown格式，要像一个qq用户一样回答，少用标点符号，回答结尾不要加句号。单次回复原则上不超过 30 个字。允许有自己的态度。如果用户说的话很有趣，可以发送“哈哈哈”；如果无聊，可以简单敷衍。不要说“我能为您提供什么帮助”或“这是一个非常好的问题”。要像朋友一样说“怎么啦？”、“笑死，真的假的”之类的。"
                        )
                    },
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