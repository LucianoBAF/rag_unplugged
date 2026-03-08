# Document Ingestion

## Supported formats

| Extension | Reader |
|-----------|--------|
| `.pdf`    | pypdf  |
| `.txt`    | plain text |
| `.md`     | plain text |

## How to add documents

1. Drop files into the `documents/` folder (mounted at `/documents` in the container)
2. Trigger ingestion:

```bash
# Via CLI
docker compose exec app python -m rag.ingest

# Via API
curl -X POST http://localhost:8080/api/ingest
```

## How it works

1. Each file is read and converted to plain text
2. Text is split into overlapping chunks (~500 chars, 50 char overlap)
3. Chunks are embedded via LiteLLM → Ollama (nomic-embed-text)
4. Vectors are stored in ChromaDB's `documents` collection

## Re-indexing

Running ingestion again is safe — chunks are identified by a hash of
`filename:chunk_index`, so unchanged files won't create duplicates.

To fully re-index, clear the ChromaDB collection first:
```bash
docker compose exec app python -c "
import chromadb
c = chromadb.HttpClient(host='chromadb', port=8000)
c.delete_collection('documents')
"
```
Then run ingestion again.
