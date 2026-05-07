import logging

from app.core.config import LLM_TASKS, settings
from app.llm.clients.base import BaseLLMClient, LLMJsonError, LLMResponse

logger = logging.getLogger(__name__)


_PROVIDER_KEY_FIELD = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}

_SUPPORTED_PROVIDERS = tuple(_PROVIDER_KEY_FIELD.keys())


def _build(provider: str, model: str) -> BaseLLMClient:
    if provider == "openai":
        from app.llm.clients.openai_client import OpenAIClient
        return OpenAIClient(model=model)
    if provider == "anthropic":
        from app.llm.clients.anthropic_client import AnthropicClient
        return AnthropicClient(model=model)
    if provider == "gemini":
        from app.llm.clients.gemini_client import GeminiClient
        return GeminiClient(model=model)
    raise ValueError(
        f"Unknown LLM provider: {provider!r}. Supported: {', '.join(_SUPPORTED_PROVIDERS)}."
    )


def _task_pair(task: str) -> tuple[str | None, str | None]:
    upper = task.upper()
    return (
        getattr(settings, f"LLM_{upper}_PROVIDER", None),
        getattr(settings, f"LLM_{upper}_MODEL", None),
    )


def _missing_config_error(task: str | None) -> ValueError:
    upper = (task or "TASK").upper()
    lines = [
        f"No LLM is configured for task {task!r}.",
        "",
        "Set ONE of the following in your .env:",
        "",
        "  Option A — use one model for everything:",
        "    LLM_ALL_PROVIDER=<openai|anthropic|gemini>",
        "    LLM_ALL_MODEL=<model-id>",
        "",
        f"  Option B — configure just this task:",
        f"    LLM_{upper}_PROVIDER=<openai|anthropic|gemini>",
        f"    LLM_{upper}_MODEL=<model-id>",
        "",
        "Then make sure the matching API key is set "
        "(OPENAI_API_KEY / ANTHROPIC_API_KEY / GEMINI_API_KEY).",
    ]
    return ValueError("\n".join(lines))


def get_llm_client(
    provider: str | None = None,
    model: str | None = None,
    task: str | None = None,
) -> BaseLLMClient:
    """
    Resolve and build the LLM client for a given task.

    Resolution order (highest priority first):

      1. Explicit `provider` + `model` arguments. Both must be passed together
         (or neither). Useful for CLI overrides like `--provider --model`.

      2. LLM_ALL_PROVIDER + LLM_ALL_MODEL from settings. When both are set,
         every task uses this pair — per-task settings are ignored. This is
         the "one model for everything" mode.

      3. Per-task pair `LLM_<TASK>_PROVIDER` + `LLM_<TASK>_MODEL`. Each task
         that you actually call must have its own pair when LLM_ALL_* is not
         configured. There are no hardcoded defaults.

    Raises:
        ValueError: If neither (1), (2), nor (3) yields a complete pair, with
            a copy-paste-able message naming the exact env vars to set.
    """
    if provider is not None or model is not None:
        if not (provider and model):
            raise ValueError(
                "When passing explicit args to get_llm_client(), both `provider` "
                "and `model` are required. Pass both, or pass neither and rely on "
                "LLM_ALL_* / per-task settings from .env."
            )
        return _build(provider, model)

    if settings.LLM_ALL_PROVIDER and settings.LLM_ALL_MODEL:
        return _build(settings.LLM_ALL_PROVIDER, settings.LLM_ALL_MODEL)

    if task and task in LLM_TASKS:
        task_provider, task_model = _task_pair(task)
        if task_provider and task_model:
            return _build(task_provider, task_model)
        if task_provider or task_model:
            upper = task.upper()
            raise ValueError(
                f"Incomplete LLM config for task {task!r}: "
                f"only one of LLM_{upper}_PROVIDER / LLM_{upper}_MODEL is set. "
                f"Set both, or set LLM_ALL_PROVIDER + LLM_ALL_MODEL to cover every task."
            )

    if task and task not in LLM_TASKS:
        logger.warning(
            "get_llm_client() called with unknown task %r; "
            "no per-task config will be looked up. Known tasks: %s",
            task,
            ", ".join(LLM_TASKS),
        )

    raise _missing_config_error(task)


__all__ = ["get_llm_client", "BaseLLMClient", "LLMResponse", "LLMJsonError"]
