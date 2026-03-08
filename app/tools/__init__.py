"""Tool registry – auto-discovers all Tool subclasses in this package."""

from __future__ import annotations

from tools.base import Tool
from tools.rag import SearchDocumentsTool
from tools.recall import RecallMemoryTool
from tools.web_search import WebSearchTool

# ── Singleton registry ────────────────────────────

_ALL_TOOLS: list[Tool] = [
    SearchDocumentsTool(),
    WebSearchTool(),
    RecallMemoryTool(),
]


def get_all_tools() -> list[Tool]:
    """Return all registered tool instances."""
    return list(_ALL_TOOLS)


def get_tool_specs() -> list[dict]:
    """Return OpenAI function-calling specs for every tool."""
    return [t.spec for t in _ALL_TOOLS]


def get_tool_by_name(name: str) -> Tool | None:
    """Look up a tool by its function name."""
    for t in _ALL_TOOLS:
        if t.name == name:
            return t
    return None
