"""RAG Unplugged – FastAPI entry point.

Starts all services (DB, ChromaDB, Telegram bot) on startup and tears
them down gracefully on shutdown via FastAPI's lifespan protocol.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from channels.api import router as api_router
from channels.telegram import TelegramChannel
from channels.whatsapp import router as whatsapp_router
from config import settings
from rag.store import init_store
from storage.conversation import close_db, init_db

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
)
log = logging.getLogger("rag_unplugged")

_telegram = TelegramChannel()


@asynccontextmanager
async def lifespan(application: FastAPI):  # noqa: ANN201, ARG001
    # ── Startup ───────────────────────────────────
    log.info("Starting RAG Unplugged …")
    await init_db()
    await init_store()
    await _telegram.start()
    log.info("All systems go.")

    yield

    # ── Shutdown ──────────────────────────────────
    log.info("Shutting down …")
    await _telegram.stop()
    await close_db()
    log.info("Goodbye.")


app = FastAPI(title="RAG Unplugged", version="0.1.0", lifespan=lifespan)
app.include_router(api_router)
app.include_router(whatsapp_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
