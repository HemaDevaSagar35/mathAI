# B04 — LLM Client Abstraction (OpenAI + Anthropic + Gemini)

> **Objective:** Create a provider-agnostic LLM layer with implementations for **OpenAI**, **Anthropic (Claude)**, and **Google Gemini**. Any service calls `llm.generate_json(prompt, schema=...)` without knowing which provider is behind it. Includes retry logic, JSON parsing, schema validation, token usage logging, and per-task provider routing.

**Depends on:** B01 (skeleton)

> ⚠️ **Update — config model replaced.** The `LLM_PROVIDER` / `LLM_MODEL` / `LLM_TASK_ROUTING` JSON-dict scheme described below has been removed. There are now **no hardcoded defaults** anywhere (no `gpt-4o`, no `claude-sonnet-4-…`, no `gemini-2.0-flash` fallbacks in clients or factory). The current model:
>
> - **`LLM_ALL_PROVIDER` + `LLM_ALL_MODEL`** — if both set, used for every task.
> - **Per-task pair** `LLM_<TASK>_PROVIDER` + `LLM_<TASK>_MODEL` — used when `LLM_ALL_*` is not set. Each task you actually call must have its own pair.
> - `get_llm_client(task=...)` raises an explicit, copy-paste-able error if neither is configured for a called task. Explicit `provider`+`model` args still win when both are passed.
>
> Tasks today: `page_extraction`, `book_profiling`, `concept_extraction`, `concept_dedup`, `concept_graph`, `tidbit_planning`, `lesson_generation`, `proof_ladder`, `quiz_generation`, `answer_grading`. See `.env.example` and `app/llm/clients/__init__.py` for the canonical resolution code. The factory and `Settings` snippets later in this doc reflect the **historical** B04 design, kept for reference; everything else (provider clients, retry, JSON validation, vision/`images=` support) is unchanged.

---

## Architecture

```text
Service code
    │
    ▼
BaseLLMClient.generate_json(prompt, schema)
    │
    ├── OpenAIClient     (gpt-4o, gpt-4o-mini)
    ├── AnthropicClient  (claude-sonnet-4-20250514, claude-3.5-haiku)
    └── GeminiClient     (gemini-2.0-flash, gemini-2.5-pro)
    │
    ▼
JSON extraction → Schema validation → Retry on failure
    │
    ▼
Token usage logged
```

---

## Tasks

### 1. Base client interface — `app/llm/clients/base.py`

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel

class LLMResponse:
    """Standardized response from any provider."""
    text: str
    parsed_json: dict | None
    input_tokens: int
    output_tokens: int
    model: str
    provider: str

class BaseLLMClient(ABC):
    provider_name: str

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        """Return raw text completion with token usage."""

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        schema: dict | type[BaseModel] | None = None,
        system: str = "",
        temperature: float = 0.1,
        max_tokens: int = 4096,
        retries: int = 2,
        **kwargs,
    ) -> dict:
        """
        Return parsed + validated JSON.
        Retry on parse/validation failure with error feedback.
        """

    async def _generate_json_with_retries(
        self, prompt, schema, system, temperature, max_tokens, retries, **kwargs
    ) -> dict:
        """
        Shared retry logic (lives in base class):
        1. Call self.generate() with JSON instruction appended to system.
        2. Extract JSON from response.
        3. Validate against schema.
        4. On failure: append error to prompt, retry.
        5. After all retries exhausted, raise LLMJsonError.
        """
```

The retry logic lives in the base class so all providers share it. Subclasses only implement the raw `generate()` call.

### 2. OpenAI implementation — `app/llm/clients/openai_client.py`

```python
from openai import AsyncOpenAI

class OpenAIClient(BaseLLMClient):
    provider_name = "openai"

    def __init__(self, model: str = "gpt-4o", api_key: str | None = None):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate(self, prompt, system="", temperature=0.2, max_tokens=4096, **kwargs) -> LLMResponse:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system} if system else None,
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return LLMResponse(
            text=response.choices[0].message.content,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            model=self.model,
            provider="openai",
        )

    async def generate_json(self, prompt, schema=None, **kwargs) -> dict:
        # OpenAI supports response_format={"type": "json_object"}
        # Use it for more reliable JSON output, then validate with shared logic
        ...
```

**OpenAI-specific advantage:** Use `response_format={"type": "json_object"}` for reliable JSON.

### 3. Anthropic implementation — `app/llm/clients/anthropic_client.py`

```python
from anthropic import AsyncAnthropic

class AnthropicClient(BaseLLMClient):
    provider_name = "anthropic"

    def __init__(self, model: str = "claude-sonnet-4-20250514", api_key: str | None = None):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def generate(self, prompt, system="", temperature=0.2, max_tokens=4096, **kwargs) -> LLMResponse:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system if system else "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        text = response.content[0].text
        return LLMResponse(
            text=text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=self.model,
            provider="anthropic",
        )

    async def generate_json(self, prompt, schema=None, **kwargs) -> dict:
        # Anthropic: prefill assistant response with "{" for reliable JSON start
        # Then use shared retry logic
        ...
```

**Anthropic-specific advantage:** Prefill the assistant turn with `{` to force JSON output.

### 4. Gemini implementation — `app/llm/clients/gemini_client.py`

```python
import google.generativeai as genai

class GeminiClient(BaseLLMClient):
    provider_name = "gemini"

    def __init__(self, model: str = "gemini-2.0-flash", api_key: str | None = None):
        genai.configure(api_key=api_key)
        self.model_name = model

    async def generate(self, prompt, system="", temperature=0.2, max_tokens=4096, **kwargs) -> LLMResponse:
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system if system else None,
        )
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return LLMResponse(
            text=response.text,
            input_tokens=response.usage_metadata.prompt_token_count,
            output_tokens=response.usage_metadata.candidates_token_count,
            model=self.model_name,
            provider="gemini",
        )

    async def generate_json(self, prompt, schema=None, **kwargs) -> dict:
        # Gemini supports response_mime_type="application/json"
        # Use it when available, fall back to shared retry logic
        ...
```

**Gemini-specific advantage:** Use `response_mime_type="application/json"` for native JSON output.

### 5. JSON response parser — `app/llm/validators/json_validator.py`

```python
import json
import re

def extract_json(text: str) -> dict:
    """
    Try to parse JSON from LLM response. Handles:
    1. Clean JSON string.
    2. ```json ... ``` fenced blocks.
    3. ``` ... ``` fenced blocks without language tag.
    4. JSON embedded in prose (find first { and last }).
    5. Trailing commas (common LLM mistake).
    Raise ValueError if no valid JSON found.
    """
    # Try raw parse first
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try fenced block extraction
    fenced = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    # Try brace extraction
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    # Try fixing trailing commas
    cleaned = re.sub(r",\s*([}\]])", r"\1", text[start:end + 1] if start != -1 else text)
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        pass

    raise ValueError(f"Could not extract valid JSON from LLM response ({len(text)} chars)")
```

### 6. Schema validator — `app/llm/validators/schema_validator.py`

```python
from pydantic import BaseModel, ValidationError

def validate_against_schema(data: dict, schema: dict | type[BaseModel]) -> dict:
    """
    Validate parsed JSON against Pydantic model or JSON Schema dict.
    Returns validated data.
    Raises ValidationError with actionable details for retry prompt.
    """
    if isinstance(schema, type) and issubclass(schema, BaseModel):
        validated = schema.model_validate(data)
        return validated.model_dump()
    elif isinstance(schema, dict):
        # Use jsonschema for raw dict schemas
        import jsonschema
        jsonschema.validate(data, schema)
        return data
    return data

def format_validation_error(error: ValidationError | Exception) -> str:
    """Format error into a string that can be appended to retry prompt."""
    if isinstance(error, ValidationError):
        issues = []
        for e in error.errors():
            loc = " → ".join(str(l) for l in e["loc"])
            issues.append(f"  - {loc}: {e['msg']}")
        return "Validation errors:\n" + "\n".join(issues)
    return str(error)
```

### 7. Client factory with per-task routing — `app/llm/clients/__init__.py`

```python
from app.core.config import settings

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
    # Check task-specific routing first
    if task and task in settings.LLM_TASK_ROUTING:
        route = settings.LLM_TASK_ROUTING[task]
        provider = provider or route.get("provider")
        model = model or route.get("model")

    provider = provider or settings.LLM_PROVIDER
    model = model or settings.LLM_MODEL

    if provider == "openai":
        return OpenAIClient(model=model or "gpt-4o", api_key=settings.OPENAI_API_KEY)
    elif provider == "anthropic":
        return AnthropicClient(model=model or "claude-sonnet-4-20250514", api_key=settings.ANTHROPIC_API_KEY)
    elif provider == "gemini":
        return GeminiClient(model=model or "gemini-2.0-flash", api_key=settings.GEMINI_API_KEY)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Supported: openai, anthropic, gemini")
```

### 8. Settings additions — `app/core/config.py`

```python
# LLM — Default provider
LLM_PROVIDER: str = "openai"                  # openai | anthropic | gemini
LLM_MODEL: str = "gpt-4o"                     # default model for chosen provider

# API keys (set whichever providers you use)
OPENAI_API_KEY: str = ""
ANTHROPIC_API_KEY: str = ""
GEMINI_API_KEY: str = ""

# Per-task routing (optional overrides)
# Example: use Claude for grading, Gemini for profiling, OpenAI for everything else
LLM_TASK_ROUTING: dict = {
    # "book_profiling": {"provider": "gemini", "model": "gemini-2.0-flash"},
    # "concept_extraction": {"provider": "openai", "model": "gpt-4o"},
    # "lesson_generation": {"provider": "anthropic", "model": "claude-sonnet-4-20250514"},
    # "answer_grading": {"provider": "anthropic", "model": "claude-sonnet-4-20250514"},
}
```

### 9. Token usage logger — `app/llm/usage_tracker.py`

```python
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("llm_usage")

@dataclass
class UsageRecord:
    timestamp: datetime
    provider: str
    model: str
    task: str
    input_tokens: int
    output_tokens: int
    success: bool
    latency_ms: float

class UsageTracker:
    """Log token usage per call. MVP writes to structured log. DB table later."""

    def log(self, record: UsageRecord):
        logger.info(
            "llm_call",
            extra={
                "provider": record.provider,
                "model": record.model,
                "task": record.task,
                "input_tokens": record.input_tokens,
                "output_tokens": record.output_tokens,
                "total_tokens": record.input_tokens + record.output_tokens,
                "success": record.success,
                "latency_ms": record.latency_ms,
            },
        )
```

### 10. Prompt template loader — `app/llm/prompts/loader.py`

```python
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent

def load_prompt(name: str, **variables) -> str:
    """
    Load a .md prompt template from app/llm/prompts/{name}.md
    and substitute {variables} using str.format_map.
    """
    path = PROMPTS_DIR / f"{name}.md"
    template = path.read_text()
    if variables:
        template = template.format_map(variables)
    return template
```

---

## Provider Comparison & When to Use Each

| Capability | OpenAI | Anthropic | Gemini |
|-----------|--------|-----------|--------|
| JSON mode | `response_format` | Prefill `{` | `response_mime_type` |
| Structured output | Native JSON schema | Tool use | Native JSON schema |
| Long context | 128K (gpt-4o) | 200K (Claude 3.5) | 1M (Gemini 1.5) |
| Cost (input) | Medium | Medium | Low |
| Math reasoning | Strong | Very strong | Strong |
| Best for | General tasks | Complex reasoning, grading | Large context, profiling |

**Recommended default routing for MathPath:**

| Task | Recommended Provider | Reasoning |
|------|---------------------|-----------|
| Book profiling | Gemini 2.0 Flash | Cheap, fast, handles large context |
| Concept extraction | OpenAI gpt-4o | Reliable structured output |
| Concept graph | OpenAI gpt-4o | Reliable structured output |
| Tidbit planning | OpenAI gpt-4o | Structured planning |
| Lesson generation | Anthropic Claude 3.5 | Best at nuanced explanations |
| Proof ladder | Anthropic Claude 3.5 | Strong mathematical reasoning |
| Quiz generation | OpenAI gpt-4o | Reliable rubric generation |
| Answer grading | Anthropic Claude 3.5 | Most generous/nuanced grading |

These are suggestions, not requirements. Any provider works for any task.

---

## Files to Create

```text
app/llm/__init__.py
app/llm/clients/__init__.py
app/llm/clients/base.py
app/llm/clients/openai_client.py
app/llm/clients/anthropic_client.py
app/llm/clients/gemini_client.py
app/llm/validators/__init__.py
app/llm/validators/json_validator.py
app/llm/validators/schema_validator.py
app/llm/usage_tracker.py
app/llm/prompts/__init__.py
app/llm/prompts/loader.py
```

Add to `requirements.txt`:

```text
openai>=1.30
anthropic>=0.28
google-generativeai>=0.7
jsonschema>=4.22
```

---

## Acceptance Criteria

- [ ] `get_llm_client("openai")` returns a working OpenAI client.
- [ ] `get_llm_client("anthropic")` returns a working Anthropic client.
- [ ] `get_llm_client("gemini")` returns a working Gemini client.
- [ ] `get_llm_client()` uses the default provider from settings.
- [ ] `get_llm_client(task="lesson_generation")` uses task-specific routing if configured.
- [ ] All three clients return `LLMResponse` with token usage.
- [ ] `client.generate_json(prompt, schema=SomeModel)` returns validated dict for all providers.
- [ ] Invalid JSON from any provider triggers retry (up to configured limit).
- [ ] Schema validation failure triggers retry with formatted error details.
- [ ] `extract_json()` handles raw JSON, fenced JSON, JSON-in-prose, and trailing commas.
- [ ] `load_prompt("book_profile", text="...")` loads and fills template.
- [ ] Token usage is logged for every call.
- [ ] Missing API key raises a clear error at client construction time, not at call time.

---

## Agent Prompt

```text
Create a multi-provider LLM client abstraction at mathpath/backend/app/llm/:

1. clients/base.py — abstract BaseLLMClient with generate() returning LLMResponse (text + token usage), and generate_json() with shared retry logic in base class. LLMResponse dataclass with text, parsed_json, input_tokens, output_tokens, model, provider.

2. clients/openai_client.py — OpenAI implementation using AsyncOpenAI. Use response_format={"type": "json_object"} for JSON calls. Return token usage from response.usage.

3. clients/anthropic_client.py — Anthropic implementation using AsyncAnthropic. Prefill assistant response with "{" for JSON calls. Return token usage from response.usage.

4. clients/gemini_client.py — Google Gemini implementation using google.generativeai. Use response_mime_type="application/json" for JSON calls. Return token usage from usage_metadata.

5. validators/json_validator.py — extract_json() handling: raw JSON, ```json fenced, brace extraction, trailing comma fix.

6. validators/schema_validator.py — validate_against_schema() with Pydantic models and JSON Schema dicts. format_validation_error() for retry prompts.

7. clients/__init__.py — get_llm_client(provider, model, task) factory with task-specific routing from settings.LLM_TASK_ROUTING.

8. usage_tracker.py — UsageTracker that logs provider, model, task, tokens, latency to structured log.

9. prompts/loader.py — load .md templates with variable substitution.

Add to config: LLM_PROVIDER, LLM_MODEL, OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, LLM_TASK_ROUTING.

Add openai, anthropic, google-generativeai, jsonschema to requirements.
```
