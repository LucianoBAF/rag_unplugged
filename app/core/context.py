"""Token counting and context-window assembly.

Uses tiktoken (cl100k_base) as a good-enough approximation for most models.
The budget is split into priority tiers so that the system prompt and recent
messages always fit, and older context is trimmed first.
"""

from __future__ import annotations

import logging

import tiktoken

from config import settings

log = logging.getLogger(__name__)

_enc = tiktoken.get_encoding("cl100k_base")

# Reserve 25 % of the context window for the model's response.
_RESPONSE_RESERVE = 0.25


def count_tokens(text: str) -> int:
    return len(_enc.encode(text))


def count_messages_tokens(messages: list[dict[str, str]]) -> int:
    """Rough token count for a list of chat messages (role + content)."""
    total = 0
    for m in messages:
        total += 4  # every message: <|im_start|>{role}\n … <|im_end|>\n
        total += count_tokens(m.get("content") or "")
    return total


def build_context(
    *,
    system_prompt: str,
    summary: str | None,
    recalled: list[str],
    recent_messages: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Assemble the prompt within the token budget.

    Priority order (first = highest, never trimmed):
      1. system prompt
      2. running conversation summary
      3. recalled past-context snippets (RAG over conversations)
      4. recent messages (oldest trimmed first if over budget)
    """
    budget = int(settings.context_window_size * (1 - _RESPONSE_RESERVE))

    ctx: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    used = count_messages_tokens(ctx)

    # ── summary ───────────────────────────────────
    if summary:
        blk = {"role": "system", "content": f"[Conversation summary so far]\n{summary}"}
        cost = count_messages_tokens([blk])
        if used + cost < budget:
            ctx.append(blk)
            used += cost

    # ── recalled memory snippets ──────────────────
    for snippet in recalled:
        blk = {"role": "system", "content": f"[Recalled context]\n{snippet}"}
        cost = count_messages_tokens([blk])
        if used + cost < budget:
            ctx.append(blk)
            used += cost
        else:
            break

    # ── recent messages (trim oldest if needed) ───
    trimmed = list(recent_messages)
    while trimmed and used + count_messages_tokens(trimmed) > budget:
        trimmed.pop(0)  # drop the oldest message

    ctx.extend(trimmed)
    log.debug(
        "Context assembled: %d tokens, %d messages (%d recent trimmed)",
        count_messages_tokens(ctx),
        len(ctx),
        len(recent_messages) - len(trimmed),
    )
    return ctx
