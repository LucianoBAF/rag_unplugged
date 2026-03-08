"""Document ingestion: read files from /documents, chunk, embed, store in ChromaDB.

Supported formats: .pdf, .txt, .md

Run manually:
    python -m rag.ingest

Or via the API:
    POST /api/ingest
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from config import settings
from rag.store import add_documents, init_store

log = logging.getLogger(__name__)

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


# ── Readers ───────────────────────────────────────


def _read_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


_READERS = {
    ".pdf": _read_pdf,
    ".txt": _read_text,
    ".md": _read_text,
}


# ── Chunking ──────────────────────────────────────


def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split *text* into overlapping chunks by character count."""
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return [c.strip() for c in chunks if c.strip()]


# ── Public API ────────────────────────────────────


async def ingest_all(directory: str | None = None) -> int:
    """Ingest every supported file in *directory*. Returns number of chunks stored."""
    directory = directory or settings.documents_path
    docs_dir = Path(directory)
    if not docs_dir.exists():
        log.warning("Documents directory does not exist: %s", docs_dir)
        return 0

    await init_store()

    total = 0
    for path in sorted(docs_dir.rglob("*")):
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        reader = _READERS.get(path.suffix.lower())
        if not reader:
            continue

        log.info("Ingesting %s", path)
        text = reader(path)
        chunks = _chunk_text(text)
        if not chunks:
            continue

        ids = [
            hashlib.sha256(f"{path.name}:{i}".encode()).hexdigest()[:16]
            for i in range(len(chunks))
        ]
        metadatas = [{"source": path.name, "chunk": i} for i in range(len(chunks))]
        add_documents(ids, chunks, metadatas)
        total += len(chunks)
        log.info("  → %d chunks", len(chunks))

    log.info("Ingestion complete: %d total chunks", total)
    return total


# Allow running as: python -m rag.ingest
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)
    asyncio.run(ingest_all())
