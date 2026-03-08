"""REST API channel – direct HTTP access for testing and future integrations."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from core.assistant import chat
from rag.ingest import ingest_all

router = APIRouter(prefix="/api")


class ChatRequest(BaseModel):
    session_id: str = "api:default"
    message: str


class ChatResponse(BaseModel):
    reply: str


class IngestResponse(BaseModel):
    chunks: int


@router.post("/chat", response_model=ChatResponse)
async def api_chat(req: ChatRequest) -> ChatResponse:
    """Send a message and get a reply – useful for testing without Telegram/WhatsApp."""
    reply = await chat(req.session_id, req.message)
    return ChatResponse(reply=reply)


@router.post("/ingest", response_model=IngestResponse)
async def api_ingest() -> IngestResponse:
    """Trigger document ingestion from /documents."""
    total = await ingest_all()
    return IngestResponse(chunks=total)
