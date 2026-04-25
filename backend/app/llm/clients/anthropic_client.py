from anthropic import AsyncAnthropic

from app.core.config import settings
from app.llm.clients.base import BaseLLMClient, LLMResponse


class AnthropicClient(BaseLLMClient):
    provider_name = "anthropic"

    def __init__(self, model: str = "claude-sonnet-4-20250514", api_key: str | None = None):
        key = api_key or settings.ANTHROPIC_API_KEY
        if not key:
            raise ValueError("ANTHROPIC_API_KEY is not set. Add it to your .env file.")
        self.client = AsyncAnthropic(api_key=key)
        self.model = model

    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system or "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )

        text = response.content[0].text if response.content else ""
        usage = response.usage

        return LLMResponse(
            text=text,
            parsed_json=None,
            input_tokens=usage.input_tokens if usage else 0,
            output_tokens=usage.output_tokens if usage else 0,
            model=self.model,
            provider="anthropic",
        )

    async def generate_json(self, prompt, schema=None, system="", temperature=0.1,
                            max_tokens=4096, retries=2, task="unknown", **kwargs):
        # Anthropic trick: prefill assistant with "{" to force JSON output
        kwargs["_anthropic_prefill"] = True
        return await super().generate_json(
            prompt, schema=schema, system=system, temperature=temperature,
            max_tokens=max_tokens, retries=retries, task=task, **kwargs,
        )
