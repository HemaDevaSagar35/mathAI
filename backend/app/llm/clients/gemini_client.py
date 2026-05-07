from google import genai
from google.genai import types

from app.core.config import settings
from app.llm.clients.base import BaseLLMClient, LLMResponse


class GeminiClient(BaseLLMClient):
    provider_name = "gemini"

    def __init__(self, model: str, api_key: str | None = None):
        key = api_key or settings.GEMINI_API_KEY
        if not key:
            raise ValueError("GEMINI_API_KEY is not set. Add it to your .env file.")
        self.client = genai.Client(api_key=key)
        self.model_name = model
        self.model = model

    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        images: list[bytes] | None = None,
        **kwargs,
    ) -> LLMResponse:
        config_kwargs: dict = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if system:
            config_kwargs["system_instruction"] = system
        if kwargs.get("json_mode"):
            config_kwargs["response_mime_type"] = "application/json"
        config = types.GenerateContentConfig(**config_kwargs)

        if images:
            parts: list = [
                types.Part.from_bytes(data=img, mime_type="image/png")
                for img in images
            ]
            parts.append(prompt)
            contents: object = parts
        else:
            contents = prompt

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config,
        )

        meta = getattr(response, "usage_metadata", None)
        input_tokens = getattr(meta, "prompt_token_count", 0) if meta else 0
        output_tokens = getattr(meta, "candidates_token_count", 0) if meta else 0

        return LLMResponse(
            text=response.text or "",
            parsed_json=None,
            input_tokens=input_tokens or 0,
            output_tokens=output_tokens or 0,
            model=self.model_name,
            provider="gemini",
        )

    async def generate_json(self, prompt, schema=None, system="", temperature=0.1,
                            max_tokens=4096, retries=2, task="unknown",
                            images=None, **kwargs):
        kwargs["json_mode"] = True
        return await super().generate_json(
            prompt, schema=schema, system=system, temperature=temperature,
            max_tokens=max_tokens, retries=retries, task=task,
            images=images, **kwargs,
        )
