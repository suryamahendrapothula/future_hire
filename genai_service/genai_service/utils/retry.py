"""Retry helpers built on tenacity."""

from collections.abc import Awaitable, Callable
from typing import TypeVar

from groq import RateLimitError
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from genai_service.utils.exceptions import LLMError
from genai_service.utils.logging import get_logger

T = TypeVar("T")
logger = get_logger(__name__)


async def with_llm_retry(coro_factory: Callable[[], Awaitable[T]]) -> T:
    """Execute an async LLM call with exponential backoff retries.

    Uses longer waits for rate-limit errors (up to 60s) and up to 5 attempts.
    """
    last_exc: Exception | None = None

    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        retry=retry_if_exception_type(Exception),
        reraise=False,
    ):
        with attempt:
            try:
                return await coro_factory()
            except RateLimitError as exc:
                last_exc = exc
                attempt_num = attempt.retry_state.attempt_number
                logger.warning(
                    "llm_rate_limited",
                    attempt=attempt_num,
                    error=str(exc),
                )
                raise
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                logger.warning(
                    "llm_call_failed",
                    attempt=attempt.retry_state.attempt_number,
                    error=str(exc),
                )
                raise

    raise LLMError(
        "LLM call failed after retries",
        details=str(last_exc) if last_exc else None,
    )
