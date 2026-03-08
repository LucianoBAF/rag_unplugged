"""Tool: recall past conversations from long-term memory."""

from __future__ import annotations

from typing import Any

from rag.store import search_conversations
from tools.base import Tool


class RecallMemoryTool(Tool):
    @property
    def name(self) -> str:
        return "recall_memory"

    @property
    def description(self) -> str:
        return (
            "Search past conversations for previously discussed topics, facts, or "
            "decisions. Use this when the user refers to something discussed earlier "
            "that isn't in the current context window."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for in past conversations.",
                },
            },
            "required": ["query"],
        }

    async def execute(self, *, query: str) -> str:
        results = await search_conversations(query, top_k=5)
        if not results:
            return "No relevant past conversations found."
        formatted = []
        for i, snippet in enumerate(results, 1):
            formatted.append(f"[{i}] {snippet[:300]}")
        return "\n\n".join(formatted)
