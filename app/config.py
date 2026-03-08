"""Centralised settings loaded from environment / .env file."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── LLM ───────────────────────────────────────
    litellm_base_url: str = "http://litellm:4000/v1"
    litellm_api_key: str = "sk-local-dev"
    chat_model: str = "chat"
    embedding_model: str = "text-embedding"

    # ── Context window ────────────────────────────
    context_window_size: int = 8192
    max_recent_messages: int = 20
    summary_threshold: int = 30

    # ── ChromaDB ──────────────────────────────────
    chromadb_host: str = "chromadb"
    chromadb_port: int = 8000

    # ── SearXNG ───────────────────────────────────
    searxng_url: str = "http://searxng:8080"

    # ── Telegram ──────────────────────────────────
    telegram_bot_token: str = ""

    # ── WhatsApp (WAHA) ──────────────────────────
    waha_url: str = "http://waha:3000"
    waha_session: str = "default"

    # ── Paths ─────────────────────────────────────
    db_path: str = "/data/conversations.db"
    documents_path: str = "/documents"

    # ── App ───────────────────────────────────────
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
