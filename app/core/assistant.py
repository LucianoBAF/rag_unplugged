"""Central orchestrator – the single entry point that channels call.

Receives a (session_id, user_message) pair and returns the assistant's reply.
Handles tool execution loops, memory persistence, and summarisation.
"""

from __future__ import annotations

import json
import logging

from core import llm
from core.context import count_tokens
from core.memory import assemble_context, maybe_summarize
from rag.store import add_conversation_message
from storage.conversation import save_message
from tools import get_tool_by_name, get_tool_specs

log = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 5  # safety limit for tool-call loops


async def chat(session_id: str, user_message: str) -> str:
    """Process a user message and return the assistant's reply."""

    # 1. Persist user message
    msg_id = await save_message(
        session_id, "user", user_message, count_tokens(user_message)
    )
    # Store in vector DB for future recall
    add_conversation_message(
        f"msg-{msg_id}", user_message, {"session_id": session_id, "role": "user"}
    )

    # 2. Build token-budgeted context
    messages = await assemble_context(session_id, user_message)

    # 3. Call LLM (with tool loop)
    tool_specs = get_tool_specs()
    for _ in range(MAX_TOOL_ROUNDS):
        result = await llm.chat_completion(messages, tools=tool_specs or None)

        # If no tool calls, we're done
        if not result.get("tool_calls"):
            break

        # Append the assistant's tool-call message
        messages.append(
            {
                "role": "assistant",
                "content": result.get("content") or "",
                "tool_calls": result["tool_calls"],
            }
        )

        # Execute each tool call and append results
        for tc in result["tool_calls"]:
            fn_name = tc["function"]["name"]
            fn_args = tc["function"]["arguments"]
            tool = get_tool_by_name(fn_name)
            if tool:
                log.info("Executing tool: %s(%s)", fn_name, fn_args[:100])
                try:
                    tool_result = await tool(fn_args)
                except Exception as exc:
                    log.error("Tool %s failed: %s", fn_name, exc)
                    tool_result = f"Tool error: {exc}"
            else:
                tool_result = f"Unknown tool: {fn_name}"

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": tool_result,
                }
            )
    else:
        log.warning("Tool loop hit MAX_TOOL_ROUNDS for session %s", session_id)

    reply = result.get("content") or "(no response)"

    # 4. Persist assistant reply
    reply_id = await save_message(
        session_id, "assistant", reply, count_tokens(reply)
    )
    add_conversation_message(
        f"msg-{reply_id}", reply, {"session_id": session_id, "role": "assistant"}
    )

    # 5. Trigger summarisation if needed (fire-and-forget style)
    try:
        await maybe_summarize(session_id)
    except Exception as exc:
        log.error("Summarisation failed: %s", exc)

    return reply
