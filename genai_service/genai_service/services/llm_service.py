"""LLM service powered by Groq SDK with structured output helpers."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import TypeVar

from groq import AsyncGroq
from pydantic import BaseModel

from genai_service.config import Settings, get_settings
from genai_service.utils.exceptions import ConfigurationError, LLMError
from genai_service.utils.logging import get_logger
from genai_service.utils.retry import with_llm_retry

logger = get_logger(__name__)
T = TypeVar("T", bound=BaseModel)


def _build_groq_client(settings: Settings) -> AsyncGroq:
    """Create an AsyncGroq client.

    The SDK automatically reads ``GROQ_API_KEY`` from the environment.
    If ``groq_api_key`` is set explicitly in settings, pass it through.
    """
    import os
    api_key = settings.groq_api_key or os.environ.get("GROQ_API_KEY")
    try:
        return AsyncGroq(
            api_key=api_key,
            timeout=settings.llm_timeout_seconds,
            max_retries=1,  # we handle retries via tenacity
        )
    except Exception as exc:
        raise ConfigurationError(
            "Failed to initialize Groq client. "
            "Ensure GROQ_API_KEY is set in .env or environment."
        ) from exc


def get_groq_client() -> AsyncGroq:
    return _build_groq_client(get_settings())


def reset_groq_cache() -> None:
    pass


def _schema_instruction(schema: type[BaseModel]) -> str:
    """Build a concise JSON-schema instruction for the LLM."""
    raw = schema.model_json_schema()
    return (
        "You MUST respond with ONLY valid JSON (no markdown fences, no extra text) "
        f"matching this JSON schema:\n{json.dumps(raw, indent=2)}"
    )


class LLMService:
    """Thin async wrapper for structured Groq LLM invocations."""

    def __init__(self, client: AsyncGroq | None = None) -> None:
        self._client = client

    @property
    def client(self) -> AsyncGroq:
        return self._client or get_groq_client()

    async def astructured(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        model_override: str | None = None,
    ) -> T:
        """Invoke Groq LLM and parse response into a Pydantic model."""

        settings = get_settings()

        async def _call() -> T:
            # Append JSON-schema instruction to the system prompt
            full_system = f"{system}\n\n{_schema_instruction(schema)}"
            active_model = model_override or settings.groq_model

            try:
                completion = await self.client.chat.completions.create(
                    model=active_model,
                    messages=[
                        {"role": "system", "content": full_system},
                        {"role": "user", "content": user},
                    ],
                    temperature=settings.llm_temperature,
                    max_tokens=4096,
                    top_p=1,
                    stream=False,
                    response_format={"type": "json_object"},
                )
            except Exception as first_exc:
                logger.warning(
                    "primary_llm_model_failed_trying_fallback",
                    model=active_model,
                    fallback=settings.groq_fallback_model,
                    error=str(first_exc),
                )
                completion = await self.client.chat.completions.create(
                    model=settings.groq_fallback_model,
                    messages=[
                        {"role": "system", "content": full_system},
                        {"role": "user", "content": user},
                    ],
                    temperature=settings.llm_temperature,
                    max_tokens=4096,
                    top_p=1,
                    stream=False,
                    response_format={"type": "json_object"},
                )

            content = completion.choices[0].message.content
            if not content:
                raise LLMError("Groq returned empty response")

            try:
                data = json.loads(content)
            except json.JSONDecodeError as exc:
                raise LLMError(
                    "Groq response is not valid JSON",
                    details=content[:500],
                ) from exc

            try:
                return schema.model_validate(data)
            except Exception as exc:
                raise LLMError(
                    "Failed to validate Groq response against schema",
                    details=str(exc),
                ) from exc

        try:
            return await with_llm_retry(_call)
        except LLMError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("structured_llm_failure", error=str(exc))
            raise LLMError("Structured LLM invocation failed", details=str(exc)) from exc
