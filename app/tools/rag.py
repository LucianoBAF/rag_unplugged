"""Tool: search personal documents via ChromaDB RAG."""

from __future__ import annotations

from typing import Any

from rag.store import search_documents
from tools.base import Tool


class SearchDocumentsTool(Tool):
    @property
    def name(self) -> str:
        return "search_documents"

    @property
    def description(self) -> str:
        return (
            "Search the user's personal documents (PDFs, notes, etc.) for "
            "information relevant to a query. Returns the most similar text snippets."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant document snippets.",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default 5).",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    async def execute(self, *, query: str, top_k: int = 5) -> str:
        results = await search_documents(query, top_k=top_k)
        if not results:
            return "No relevant documents found."
        formatted = []
        for i, snippet in enumerate(results, 1):
            formatted.append(f"[{i}] {snippet[:500]}")
        return "\n\n".join(formatted)
