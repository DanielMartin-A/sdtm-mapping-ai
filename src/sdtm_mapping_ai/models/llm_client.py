"""Shared LLM client with retry logic, JSON parsing, and response validation.

Fixes applied:
- C1: Single client class eliminates duplication across DomainPredictor/VariableMapper
- C3: tenacity retry on transient API errors
- H2: Safe handling of empty/None LLM responses
- M5: Input sanitization helper for prompt injection defense
"""

from __future__ import annotations

import json
import logging as _logging
from typing import Any

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from sdtm_mapping_ai.config import LLMProvider, get_settings

# BUG 1 FIX: tenacity's before_sleep_log requires a stdlib logging.Logger
# (it calls logger.log(level, msg)), NOT a structlog BoundLogger (which lacks .log()).
# Using structlog here would raise AttributeError on the first retry attempt.
_tenacity_logger = _logging.getLogger("sdtm_mapping_ai.llm_client")

# Exceptions worth retrying across providers
_RETRYABLE_EXCEPTIONS: tuple[type[BaseException], ...] = (
    ConnectionError,
    TimeoutError,
)

try:
    import anthropic

    _RETRYABLE_EXCEPTIONS = (*_RETRYABLE_EXCEPTIONS, anthropic.APIStatusError)
except ImportError:
    pass

try:
    import openai

    _RETRYABLE_EXCEPTIONS = (*_RETRYABLE_EXCEPTIONS, openai.APIError)
except ImportError:
    pass


def sanitize_for_prompt(values: list[str], max_items: int = 5, max_chars: int = 100) -> str:
    """FIX M5: Sanitize sample values before injecting into LLM prompts.

    Strips curly braces (prevents f-string/template breaks) and truncates.
    """
    if not values:
        return "(none)"
    safe = []
    for v in values[:max_items]:
        cleaned = str(v)[:max_chars].replace("{", "").replace("}", "")
        safe.append(cleaned)
    return ", ".join(safe)


class LLMClient:
    """Unified LLM client supporting Anthropic, OpenAI, and Ollama.

    FIX C1: Eliminates duplicated client init/call/parse code.
    FIX C3: Automatic retry with exponential backoff on transient failures.
    FIX H2: Validates non-empty text before returning.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: Any = None

    @property
    def client(self) -> Any:
        if self._client is None:
            match self.settings.sdtm_llm_provider:
                case LLMProvider.OPENAI:
                    from openai import OpenAI

                    self._client = OpenAI(api_key=self.settings.openai_api_key)
                case LLMProvider.ANTHROPIC:
                    from anthropic import Anthropic

                    self._client = Anthropic(api_key=self.settings.anthropic_api_key)
                case LLMProvider.OLLAMA:
                    from openai import OpenAI

                    self._client = OpenAI(
                        base_url=f"{self.settings.ollama_base_url}/v1",
                        api_key="ollama",
                    )
                case _:
                    raise ValueError(f"Unsupported provider: {self.settings.sdtm_llm_provider}")
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
        before_sleep=before_sleep_log(_tenacity_logger, _logging.WARNING),
        reraise=True,
    )
    def call(self, prompt: str, system: str = "") -> str:
        """Call the LLM and return the text response.

        FIX C3: Retries up to 3 times with exponential backoff on transient errors.
        FIX H2: Raises ValueError on empty responses instead of passing None downstream.
        """
        model = self.settings.get_llm_model_name()

        match self.settings.sdtm_llm_provider:
            case LLMProvider.ANTHROPIC:
                messages = [{"role": "user", "content": prompt}]
                kwargs: dict[str, Any] = {"model": model, "max_tokens": 500, "messages": messages}
                if system:
                    kwargs["system"] = system
                response = self.client.messages.create(**kwargs)
                # FIX H2: Guard against empty content array
                if not response.content:
                    raise ValueError("Anthropic returned empty content array")
                text_blocks = [b.text for b in response.content if hasattr(b, "text")]
                if not text_blocks:
                    raise ValueError("Anthropic response contained no text blocks")
                return text_blocks[0]

            case LLMProvider.OPENAI | LLMProvider.OLLAMA:
                messages_list = []
                if system:
                    messages_list.append({"role": "system", "content": system})
                messages_list.append({"role": "user", "content": prompt})
                response = self.client.chat.completions.create(
                    model=model, max_tokens=500, messages=messages_list, temperature=0.1,
                )
                # FIX H2: Guard against None content (refusals)
                text = response.choices[0].message.content
                if not text:
                    raise ValueError("OpenAI/Ollama returned empty content")
                return text

            case _:
                raise ValueError(f"Unsupported provider: {self.settings.sdtm_llm_provider}")

    def call_json(self, prompt: str, system: str = "") -> dict:
        """Call the LLM, parse the response as JSON, and return the dict.

        Handles markdown-fenced JSON (```json ... ```) that LLMs sometimes produce.
        """
        raw = self.call(prompt, system)
        return self.parse_json(raw)

    @staticmethod
    def parse_json(text: str) -> dict:
        """Parse LLM text response as JSON, stripping markdown fences if present."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            # Strip ```json or ``` fences
            first_newline = cleaned.index("\n") if "\n" in cleaned else len(cleaned)
            cleaned = cleaned[first_newline + 1:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
        return json.loads(cleaned)
