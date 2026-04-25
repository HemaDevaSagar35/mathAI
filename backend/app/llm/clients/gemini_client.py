import google.generativeai as genai

from app.core.config import settings
from app.llm.clients.base import BaseLLMClient, LLMResponse


class GeminiClient(BaseLLMClient):
    provider_name = "gemini"

    def __init__(self, model: str = "gemini-2.0-flash", api_key: str | None = None):
        key = api_key or settings.GEMINI_API_KEY
        if not key:
            raise ValueError("GEMINI_API_KEY is not set. Add it to your .env file.")
        genai.configure(api_key=key)
        self.model_name = model
        self.model = model

    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        gen_model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system if system else None,
        )

        config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        if kwargs.get("json_mode"):
            config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                response_mime_type="application/json",
            )

        response = await gen_model.generate_content_async(
            prompt,
            generation_config=config,
        )

        meta = response.usage_metadata
        return LLMResponse(
            text=response.text or "",
            parsed_json=None,
            input_tokens=meta.prompt_token_count if meta else 0,
            output_tokens=meta.candidates_token_count if meta else 0,
            model=self.model_name,
            provider="gemini",
        )

    async def generate_json(self, prompt, schema=None, system="", temperature=0.1,
                            max_tokens=4096, retries=2, task="unknown", **kwargs):
        kwargs["json_mode"] = True
        return await super().generate_json(
            prompt, schema=schema, system=system, temperature=temperature,
            max_tokens=max_tokens, retries=retries, task=task, **kwargs,
        )
