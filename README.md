# lebowski-rag

RAG-based service over the script of "The Big Lebowski", built with an open-source stack.

## Features

- **Quote finder**: semantic search for script quotes with context (character, scene).
- **Chat with The Dude**: converse with The Dude's personality, backed by the script
  (RAG: retrieved context + generation).

## Stack

| Layer       | Tool                        |
|-------------|-----------------------------|
| LLM         | `llama3.2:3b` via Ollama    |
| Embeddings  | `nomic-embed-text` (Ollama) |
| Vector DB   | ChromaDB (local, `db/`)     |
| API         | FastAPI (SSE on `/chat`)    |
| Frontend    | Streamlit (2 tabs)          |

## Requirements

- macOS (Apple Silicon) or Linux, with Ollama installed.
- Python 3.10+.

## Local setup

```bash
# 1. Models
bash scripts/setup.sh

# 2. Dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Add the script (not versioned)
#    Copy data/thebiglebowski.pdf into the data/ directory (manual, due to script rights).

# 4. Ingest
python ingest.py

# 5. API + UI
uvicorn app.main:app --reload     # http://localhost:8000
streamlit run app/ui.py           # http://localhost:8501
```

## Configuration

Environment variables in `.env` (see `.env.example`):
`OLLAMA_HOST`, `DB_PATH`, `MODEL` (default `llama3.2:3b`), `EMBED_MODEL` (default `nomic-embed-text`).

## Structure

See `AGENTS.md` for the directory tree, conventions, and design decisions.

## Deployment

- **Primary**: Oracle Cloud ARM Free Tier via GitHub Actions (`deploy-oracle.yml`).
- **Extra demo**: Hugging Face Spaces (quote finder).
