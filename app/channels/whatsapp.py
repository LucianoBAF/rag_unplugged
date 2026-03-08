"""WhatsApp channel adapter – receives webhooks from WAHA and replies via its REST API."""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Request

from channels.base import Channel
from config import settings
from core.assistant import chat

log = logging.getLogger(__name__)

router = APIRouter()


class WhatsAppChannel(Channel):
    """Registers a FastAPI webhook route to receive WAHA events."""

    async def start(self) -> None:
        if not settings.waha_url:
            log.warning("WAHA_URL not set – WhatsApp channel disabled")
            return
        log.info("WhatsApp channel ready (webhook at /webhook/whatsapp)")

    async def stop(self) -> None:
        pass


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request) -> dict:
    """Handle incoming messages forwarded by WAHA."""
    body = await request.json()
    event = body.get("event")

    if event != "message":
        return {"status": "ignored"}

    payload = body.get("payload", {})
    from_number = payload.get("from", "")
    message_body = payload.get("body", "")

    if not message_body or not from_number:
        return {"status": "ignored"}

    # Strip the @c.us suffix for a cleaner session id
    phone = from_number.replace("@c.us", "")
    session_id = f"whatsapp:{phone}"

    log.info("[WhatsApp] %s: %s", session_id, message_body[:80])
    reply = await chat(session_id, message_body)

    # Send the reply back via WAHA REST API
    await _send_message(from_number, reply)
    return {"status": "ok"}


async def _send_message(chat_id: str, text: str) -> None:
    """Send a text message via WAHA."""
    url = f"{settings.waha_url}/api/sendText"
    payload = {
        "chatId": chat_id,
        "text": text,
        "session": settings.waha_session,
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
    except Exception as exc:
        log.error("Failed to send WhatsApp message: %s", exc)
