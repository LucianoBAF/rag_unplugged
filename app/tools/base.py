"""Base protocol for tools and the auto-discovery registry."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    """Every tool must implement this interface.

    Subclasses expose themselves to the LLM in OpenAI function-calling format
    via :pyattr:`spec` and execute real work in :pymeth:`execute`.
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """JSON-Schema for the tool's arguments."""
        ...

    @abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        """Run the tool and return a human-readable result string."""
        ...

    # ── Helpers ───────────────────────────────────

    @property
    def spec(self) -> dict[str, Any]:
        """Return the OpenAI function-calling tool definition."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    async def __call__(self, raw_arguments: str) -> str:
        """Parse a JSON arguments string and delegate to :pymeth:`execute`."""
        kwargs = json.loads(raw_arguments) if raw_arguments else {}
        return await self.execute(**kwargs)
