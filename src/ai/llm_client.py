import asyncio

class LLMClient:
    def __init__(self, api_key: str, api_base: str, model: str, prompt: str = ""):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.prompt = prompt

    def _call_sync(self, user_text: str) -> str:
        raise NotImplementedError

    async def call(self, user_text: str) -> str:
        return await asyncio.to_thread(self._call_sync, user_text)