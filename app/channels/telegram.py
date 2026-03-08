"""Telegram channel adapter – uses python-telegram-bot in polling mode.

Polling avoids the need to expose the server to the internet, which is
ideal for a self-hosted personal assistant.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from channels.base import Channel
from config import settings
from core.assistant import chat
from storage.conversation import clear_session

log = logging.getLogger(__name__)


class TelegramChannel(Channel):
    def __init__(self) -> None:
        self._app: Application | None = None

    async def start(self) -> None:
        token = settings.telegram_bot_token
        if not token:
            log.warning("TELEGRAM_BOT_TOKEN not set – Telegram channel disabled")
            return

        self._app = Application.builder().token(token).build()
        self._app.add_handler(CommandHandler("reset", self._handle_reset))
        self._app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
        )

        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling(allowed_updates=Update.ALL_TYPES)  # type: ignore[union-attr]
        log.info("Telegram bot started (polling)")

    async def stop(self) -> None:
        if self._app:
            await self._app.updater.stop()  # type: ignore[union-attr]
            await self._app.stop()
            await self._app.shutdown()
            log.info("Telegram bot stopped")

    # ── Handlers ──────────────────────────────────

    @staticmethod
    async def _handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.message.text:
            return
        session_id = f"telegram:{update.effective_user.id}"  # type: ignore[union-attr]
        user_text = update.message.text

        log.info("[Telegram] %s: %s", session_id, user_text[:80])
        reply = await chat(session_id, user_text)
        await update.message.reply_text(reply)

    @staticmethod
    async def _handle_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message:
            return
        session_id = f"telegram:{update.effective_user.id}"  # type: ignore[union-attr]
        await clear_session(session_id)
        await update.message.reply_text("Conversation cleared. Let's start fresh!")
