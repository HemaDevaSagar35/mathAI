from openai import AsyncOpenAI

from app.core.config import settings
from app.llm.clients.base import BaseLLMClient, LLMResponse


class OpenAIClient(BaseLLMClient):
    provider_name = "openai"

    def __init__(self, model: str = "gpt-4o", api_key: str | None = None):
        key = api_key or settings.OPENAI_API_KEY
        if not key:
            raise ValueError("OPENAI_API_KEY is not set. Add it to your .env file.")
        self.client = AsyncOpenAI(api_key=key)
        self.model = model

    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        extra = {}
        if kwargs.get("json_mode"):
            extra["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **extra,
        )

        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            text=choice.message.content or "",
            parsed_json=None,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            model=self.model,
            provider="openai",
        )

    async def generate_json(self, prompt, schema=None, system="", temperature=0.1,
                            max_tokens=4096, retries=2, task="unknown", **kwargs):
        kwargs["json_mode"] = True
        return await super().generate_json(
            prompt, schema=schema, system=system, temperature=temperature,
            max_tokens=max_tokens, retries=retries, task=task, **kwargs,
        )
