import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from pydantic import BaseModel

from app.llm.usage_tracker import UsageRecord, tracker
from app.llm.validators.json_validator import extract_json
from app.llm.validators.schema_validator import (
    format_validation_error,
    validate_against_schema,
)

logger = logging.getLogger(__name__)

JSON_SYSTEM_SUFFIX = "\n\nRespond ONLY with valid JSON. No markdown, no explanation, no extra text."


class LLMJsonError(Exception):
    pass


@dataclass
class LLMResponse:
    text: str
    parsed_json: dict | None
    input_tokens: int
    output_tokens: int
    model: str
    provider: str


class BaseLLMClient(ABC):
    provider_name: str = ""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        ...

    async def generate_json(
        self,
        prompt: str,
        schema: dict | type[BaseModel] | None = None,
        system: str = "",
        temperature: float = 0.1,
        max_tokens: int = 4096,
        retries: int = 2,
        task: str = "unknown",
        **kwargs,
    ) -> dict:
        """Generate and validate JSON, retrying on parse/validation failure."""
        full_system = (system or "") + JSON_SYSTEM_SUFFIX
        last_error = ""

        for attempt in range(1 + retries):
            current_prompt = prompt
            if attempt > 0 and last_error:
                current_prompt = (
                    f"{prompt}\n\n--- PREVIOUS ATTEMPT FAILED ---\n{last_error}\n"
                    "Please fix the issues and return valid JSON."
                )

            t0 = time.monotonic()
            try:
                response = await self.generate(
                    current_prompt,
                    system=full_system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                latency = (time.monotonic() - t0) * 1000

                data = extract_json(response.text)

                if schema is not None:
                    data = validate_against_schema(data, schema)

                tracker.log(UsageRecord(
                    provider=self.provider_name,
                    model=response.model,
                    task=task,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    success=True,
                    latency_ms=latency,
                ))
                return data

            except Exception as e:
                latency = (time.monotonic() - t0) * 1000
                last_error = format_validation_error(e) if hasattr(e, "errors") else str(e)
                logger.warning(
                    "LLM JSON attempt %d/%d failed: %s",
                    attempt + 1,
                    1 + retries,
                    last_error[:200],
                )
                tracker.log(UsageRecord(
                    provider=self.provider_name,
                    model=getattr(self, "model", "unknown"),
                    task=task,
                    input_tokens=getattr(getattr(locals().get("response"), "input_tokens", None), "__self__", 0) if False else 0,
                    output_tokens=0,
                    success=False,
                    latency_ms=latency,
                ))

        raise LLMJsonError(
            f"Failed to get valid JSON after {1 + retries} attempts. Last error: {last_error}"
        )
