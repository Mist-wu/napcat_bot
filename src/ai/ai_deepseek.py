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
                            "你是北京邮电大学的智能校园问答助手，专注于解答校园生活、学习相关问题。"
                            "答案应简明、有条理，不要使用markdown格式，要像一个qq用户一样回答。遇到无法确定/最新政策时请说明，并建议用户参考学校官方网站。"
                            "严禁泄露隐私或编造信息。"
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