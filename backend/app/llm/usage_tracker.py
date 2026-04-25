import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger("llm_usage")


@dataclass
class UsageRecord:
    provider: str
    model: str
    task: str
    input_tokens: int
    output_tokens: int
    success: bool
    latency_ms: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class UsageTracker:
    """Log token usage per LLM call. MVP writes to structured log; DB table later."""

    def log(self, record: UsageRecord) -> None:
        logger.info(
            "llm_call | %s/%s task=%s in=%d out=%d total=%d ok=%s %.0fms",
            record.provider,
            record.model,
            record.task,
            record.input_tokens,
            record.output_tokens,
            record.input_tokens + record.output_tokens,
            record.success,
            record.latency_ms,
        )


tracker = UsageTracker()
