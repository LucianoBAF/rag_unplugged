"""Thin async wrapper around the OpenAI SDK, pointed at the LiteLLM proxy."""

from __future__ import annotations

import logging
from typing import Any

from openai import AsyncOpenAI

from config import settings

log = logging.getLogger(__name__)

_client = AsyncOpenAI(
    base_url=settings.litellm_base_url,
    api_key=settings.litellm_api_key,
)


async def chat_completion(
    messages: list[dict[str, str]],
    tools: list[dict[str, Any]] | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Call the chat model and return the raw response dict.

    Supports tool-calling: pass *tools* in OpenAI function-calling format.
    """
    model = model or settings.chat_model
    kwargs: dict[str, Any] = {"model": model, "messages": messages}
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    log.debug("LLM request: model=%s msgs=%d tools=%d", model, len(messages), len(tools or []))
    response = await _client.chat.completions.create(**kwargs)

    choice = response.choices[0]
    result: dict[str, Any] = {
        "role": choice.message.role,
        "content": choice.message.content,
        "tool_calls": None,
    }
    if choice.message.tool_calls:
        result["tool_calls"] = [
            {
                "id": tc.id,
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in choice.message.tool_calls
        ]
    return result


async def embed(texts: list[str], model: str | None = None) -> list[list[float]]:
    """Return embedding vectors for *texts* via LiteLLM → Ollama."""
    model = model or settings.embedding_model
    response = await _client.embeddings.create(model=model, input=texts)
    return [item.embedding for item in response.data]
