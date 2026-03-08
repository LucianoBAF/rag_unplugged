"""Conversation persistence with SQLite (async via aiosqlite)."""

from __future__ import annotations

import aiosqlite

from config import settings

_db: aiosqlite.Connection | None = None


async def init_db() -> None:
    """Open the database and create tables if needed."""
    global _db
    _db = await aiosqlite.connect(settings.db_path)
    _db.row_factory = aiosqlite.Row
    await _db.executescript(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT    NOT NULL,
            role        TEXT    NOT NULL,
            content     TEXT    NOT NULL,
            token_count INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_messages_session
            ON messages(session_id, id);

        CREATE TABLE IF NOT EXISTS summaries (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id              TEXT    NOT NULL,
            summary                 TEXT    NOT NULL,
            covers_until_message_id INTEGER NOT NULL,
            created_at              TEXT    NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_summaries_session
            ON summaries(session_id, created_at DESC);
        """
    )
    await _db.commit()


async def close_db() -> None:
    global _db
    if _db:
        await _db.close()
        _db = None


# ── Messages ──────────────────────────────────────


async def save_message(
    session_id: str, role: str, content: str, token_count: int = 0
) -> int:
    assert _db
    cursor = await _db.execute(
        "INSERT INTO messages (session_id, role, content, token_count) VALUES (?, ?, ?, ?)",
        (session_id, role, content, token_count),
    )
    await _db.commit()
    return cursor.lastrowid  # type: ignore[return-value]


async def get_recent_messages(
    session_id: str, limit: int = 20
) -> list[dict[str, str | int]]:
    assert _db
    cursor = await _db.execute(
        "SELECT id, role, content FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
        (session_id, limit),
    )
    rows = await cursor.fetchall()
    return [{"id": r["id"], "role": r["role"], "content": r["content"]} for r in reversed(rows)]


async def get_unsummarized_messages(
    session_id: str,
) -> list[dict[str, str | int]]:
    """Return messages after the latest summary."""
    assert _db
    cursor = await _db.execute(
        "SELECT covers_until_message_id FROM summaries "
        "WHERE session_id = ? ORDER BY id DESC LIMIT 1",
        (session_id,),
    )
    row = await cursor.fetchone()
    after_id = row["covers_until_message_id"] if row else 0

    cursor = await _db.execute(
        "SELECT id, role, content FROM messages WHERE session_id = ? AND id > ? ORDER BY id",
        (session_id, after_id),
    )
    rows = await cursor.fetchall()
    return [{"id": r["id"], "role": r["role"], "content": r["content"]} for r in rows]


# ── Summaries ─────────────────────────────────────


async def save_summary(
    session_id: str, summary: str, covers_until_message_id: int
) -> None:
    assert _db
    await _db.execute(
        "INSERT INTO summaries (session_id, summary, covers_until_message_id) VALUES (?, ?, ?)",
        (session_id, summary, covers_until_message_id),
    )
    await _db.commit()


async def get_latest_summary(session_id: str) -> str | None:
    assert _db
    cursor = await _db.execute(
        "SELECT summary FROM summaries WHERE session_id = ? ORDER BY id DESC LIMIT 1",
        (session_id,),
    )
    row = await cursor.fetchone()
    return row["summary"] if row else None


async def clear_session(session_id: str) -> None:
    """Delete all messages and summaries for a session."""
    assert _db
    await _db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    await _db.execute("DELETE FROM summaries WHERE session_id = ?", (session_id,))
    await _db.commit()
