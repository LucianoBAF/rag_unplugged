# RAG Unplugged

A fully local, self-hosted personal assistant. Chat via Telegram or WhatsApp
with a private LLM that can search your documents, browse the web, and
remember past conversations — all running on your own hardware with zero
cloud API dependencies.

Thought for easy maintenance and extensibility by a single person - no complex orchestration and overheads.

Private and unfiltered LLM answers - no external LLM API dependencies, no third party SaaS. Use any uncensored model in Ollama, or even run your own LiteLLM-compatible model server for true, unfiltered answers.

## Architecture

```
Telegram ──┐                  ┌─► Ollama (GPU)
            ├─► FastAPI app ──┤
WhatsApp ──┘    │    │        └─► LiteLLM proxy
                │    ├─► ChromaDB (documents + memory)
                │    └─► SearXNG  (web search)
                │
           SQLite (conversation log)
```

Every block is a Docker container. 
The Python app (~500 lines) is the only custom approach; everything else is an off-the-shelf image for minimum maintenance.

## Prerequisites

| Requirement | Why |
|-------------|-----|
| Docker + Docker Compose | Runs everything |
| NVIDIA GPU + [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) | GPU passthrough for Ollama |
| Ollama models pulled | `ollama pull llama3.1` and `ollama pull nomic-embed-text` |

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env → set TELEGRAM_BOT_TOKEN (see app/channels/README.md)

# 2. Start everything
docker compose up -d

# 3. Pull models into Ollama (first time only)
docker compose exec ollama ollama pull llama3.1
docker compose exec ollama ollama pull nomic-embed-text

# 4. (Optional) Ingest your documents
# Drop PDFs/TXT/MD files into ./documents/, then:
docker compose exec app python -m rag.ingest

# 5. Test via REST API
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, who are you?"}'
```

## Configuration

All settings live in `.env` (see `.env.example` for documentation).
Model routing is in `litellm_config.yaml`.

### Changing models

Edit `litellm_config.yaml`, change the `model:` field, and restart:
```bash
docker compose restart litellm
```

## Project Structure

```
├── docker-compose.yml          # 6 services
├── litellm_config.yaml         # model routing
├── searxng/settings.yml        # search engine config
├── app/
│   ├── main.py                 # FastAPI entry
│   ├── config.py               # env-driven settings
│   ├── core/
│   │   ├── assistant.py        # orchestrator
│   │   ├── memory.py           # summarisation + recall
│   │   ├── context.py          # token-budgeted prompt builder
│   │   └── llm.py              # OpenAI SDK → LiteLLM
│   ├── tools/                  # extensible tool system
│   │   ├── base.py             # Tool ABC
│   │   ├── rag.py              # search documents
│   │   ├── web_search.py       # SearXNG
│   │   └── recall.py           # search past conversations
│   ├── channels/               # messaging adapters
│   │   ├── telegram.py         # polling mode
│   │   ├── whatsapp.py         # WAHA webhooks
│   │   └── api.py              # REST endpoint
│   ├── rag/
│   │   ├── store.py            # ChromaDB wrapper
│   │   └── ingest.py           # PDF/TXT/MD → chunks → vectors
│   └── storage/
│       └── conversation.py     # SQLite message log
├── documents/                  # your files go here
└── data/                       # persistent runtime data (gitignored)
```

## Adding a New Tool

1. Create `app/tools/my_tool.py` implementing the `Tool` ABC
2. Register it in `app/tools/__init__.py`
3. Done — the LLM will see it via function-calling

## Adding a New Channel

1. Create `app/channels/my_channel.py` implementing the `Channel` ABC
2. Wire startup/shutdown in `app/main.py`
3. Done — the orchestrator (`core/assistant.chat()`) is channel-agnostic
