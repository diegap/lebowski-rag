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

## Quote finder CLI

```bash
# Célebre quote
python scripts/search.py "that rug really tied the room together"

# Fuzzy / non-literal match
python scripts/search.py "flying rugs"

# Only The Dude's lines
python scripts/search.py "take it easy" -d

# Filter by character
python scripts/search.py "am I the only one around here" -c WALTER

# Top 10 results
python scripts/search.py "nihilists" -n 10
```

## API

Run the server with `uvicorn app.main:app --reload` (default `http://localhost:8000`).
Interactive docs at `http://localhost:8000/docs`.

### `GET /health`

```
curl http://localhost:8000/health
# {"status":"ok","turns":1271}
```

### `GET /search`

Semantic quote finder. Query params: `q` (required), `top_k` (default 5, 1–20),
`character`, `dude_only`.

```
curl "http://localhost:8000/search?q=that+rug+really+tied+the+room+together&top_k=3"
```

```json
{
  "query": "that rug really tied the room together",
  "results": [
    {
      "scene": 6,
      "heading": "INT. DUDE'S BUNGALOW - DAY",
      "character": "DUDE",
      "text": "That rug really tied the room together, did it not?",
      "distance": 0.35
    }
  ]
}
```

### `POST /chat`

Streaming chat with The Dude (SSE). Body: `message` (required), `top_k`,
`character`, `dude_only`.

```
curl -N -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What happened to your rug, man?"}'
```

Each token arrives as SSE: `data: {"token": "..."}`, ending with
`data: [DONE]`.

## UI (Streamlit)

The UI connects to the API — both must be running.

```bash
# Terminal 1: API
uvicorn app.main:app --reload     # http://localhost:8000

# Terminal 2: UI
streamlit run app/ui.py           # http://localhost:8501
```

Two tabs:

- **Quote finder**: semantic search with filters (top_k, character, only The Dude).
- **Chat with El Dude**: conversational chat with streaming, backed by the script.

For production (Oracle), set `API_URL` in `.env` to point to the API endpoint.

## Configuration

Environment variables in `.env` (see `.env.example`):
`OLLAMA_HOST`, `DB_PATH`, `MODEL` (default `llama3.2:3b`), `EMBED_MODEL` (default `nomic-embed-text`), `API_URL` (default `http://localhost:8000`).

## Structure

See `AGENTS.md` for the directory tree, conventions, and design decisions.

## Deployment

- **Primary**: Oracle Cloud ARM Free Tier (Always Free `VM.Standard.A1.Flex`, 2 OCPU /
  12 GB) via GitHub Actions (`deploy-oracle.yml`).
- `scripts/deploy_oracle.sh` provisions the VM on first deploy: Ollama, venv, systemd
  units (`lebowski-api` on `127.0.0.1:8000`, `lebowski-ui` on `127.0.0.1:8501`), nginx
  with HTTPS + WebSocket/SSE proxying (Streamlit DB), certbot, ufw, and a DuckDNS cron
  to keep the domain pointed at the instance.
- Required GitHub secrets: `ORACLE_HOST`, `ORACLE_USER`, `ORACLE_SSH_PRIVATE_KEY`,
  `ORACLE_DOMAIN` (the DuckDNS name, e.g. `lebowski.duckdns.org`), `DUCKDNS_TOKEN`.
- The workflow stays disabled until those secrets exist.
- **Extra demo**: Hugging Face Spaces (quote finder).
