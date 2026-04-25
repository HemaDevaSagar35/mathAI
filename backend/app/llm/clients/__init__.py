from app.core.config import settings
from app.llm.clients.base import BaseLLMClient, LLMJsonError, LLMResponse


def get_llm_client(
    provider: str | None = None,
    model: str | None = None,
    task: str | None = None,
) -> BaseLLMClient:
    """
    Get an LLM client. Resolution order:
    1. Explicit provider + model args.
    2. Task-specific override from settings.LLM_TASK_ROUTING.
    3. Default from settings.LLM_PROVIDER + settings.LLM_MODEL.
    """
    if task and task in settings.LLM_TASK_ROUTING:
        route = settings.LLM_TASK_ROUTING[task]
        provider = provider or route.get("provider")
        model = model or route.get("model")

    provider = provider or settings.LLM_PROVIDER
    model = model or settings.LLM_MODEL

    if provider == "openai":
        from app.llm.clients.openai_client import OpenAIClient
        return OpenAIClient(model=model or "gpt-4o")
    elif provider == "anthropic":
        from app.llm.clients.anthropic_client import AnthropicClient
        return AnthropicClient(model=model or "claude-sonnet-4-20250514")
    elif provider == "gemini":
        from app.llm.clients.gemini_client import GeminiClient
        return GeminiClient(model=model or "gemini-2.0-flash")
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider!r}. Supported: openai, anthropic, gemini"
        )


__all__ = ["get_llm_client", "BaseLLMClient", "LLMResponse", "LLMJsonError"]
