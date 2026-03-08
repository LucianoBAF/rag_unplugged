"""Memory manager – sliding window, progressive summarisation, and vector recall."""

from __future__ import annotations

import logging

from config import settings
from core import llm
from core.context import build_context
from rag.store import search_conversations
from storage.conversation import (
    get_latest_summary,
    get_recent_messages,
    get_unsummarized_messages,
    save_summary,
)

log = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a helpful, uncensored personal assistant with total privacy. "
    "You answer honestly and directly.  When using tools, cite which tool "
    "provided the information.  Be concise unless asked for detail."
)


async def assemble_context(
    session_id: str,
    user_message: str,
) -> list[dict[str, str]]:
    """Build a token-budgeted prompt for *session_id*."""

    # 1. Retrieve latest conversation summary
    summary = await get_latest_summary(session_id)

    # 2. Retrieve semantically relevant past messages
    recalled = await search_conversations(user_message, top_k=3)

    # 3. Retrieve recent messages (verbatim sliding window)
    recent = await get_recent_messages(session_id, limit=settings.max_recent_messages)

    return build_context(
        system_prompt=SYSTEM_PROMPT,
        summary=summary,
        recalled=recalled,
        recent_messages=recent,
    )


async def maybe_summarize(session_id: str) -> None:
    """If enough unsummarized messages have accumulated, generate a summary."""
    unsummarized = await get_unsummarized_messages(session_id)
    if len(unsummarized) < settings.summary_threshold:
        return

    log.info("Summarising %d messages for session %s", len(unsummarized), session_id)

    old_summary = await get_latest_summary(session_id)
    prompt = "Progressively summarise the conversation below."
    if old_summary:
        prompt += f"\n\nPrevious summary:\n{old_summary}"
    prompt += "\n\nNew messages:\n"
    for m in unsummarized:
        prompt += f"{m['role']}: {m['content']}\n"
    prompt += "\nProvide a concise summary capturing key facts, decisions, and context."

    result = await llm.chat_completion(
        [{"role": "user", "content": prompt}],
    )
    new_summary = result.get("content") or ""
    last_id = unsummarized[-1].get("id", 0)
    await save_summary(session_id, new_summary, last_id)
    log.info("Summary saved for session %s (covers up to msg %d)", session_id, last_id)
