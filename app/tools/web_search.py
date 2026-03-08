"""Tool: web search via self-hosted SearXNG."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from config import settings
from tools.base import Tool

log = logging.getLogger(__name__)


class WebSearchTool(Tool):
    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "Search the web for current information using a self-hosted search engine. "
            "Use this when the user asks about recent events, facts you're unsure of, "
            "or anything that benefits from live web results."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The web search query.",
                },
            },
            "required": ["query"],
        }

    async def execute(self, *, query: str) -> str:
        url = f"{settings.searxng_url}/search"
        params = {"q": query, "format": "json", "engines": "google,bing,duckduckgo"}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            log.error("SearXNG search failed: %s", exc)
            return f"Web search failed: {exc}"

        results = data.get("results", [])[:5]
        if not results:
            return "No web results found."

        lines = []
        for r in results:
            title = r.get("title", "")
            snippet = r.get("content", "")
            link = r.get("url", "")
            lines.append(f"• {title}\n  {snippet}\n  {link}")
        return "\n\n".join(lines)
