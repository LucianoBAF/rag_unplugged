"""Abstract base for messaging channel adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Channel(ABC):
    """Every channel (Telegram, WhatsApp, REST API …) implements this."""

    @abstractmethod
    async def start(self) -> None:
        """Begin listening for messages."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Graceful shutdown."""
        ...
