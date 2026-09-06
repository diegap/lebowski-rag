# lebowski-rag

Side-project para portfolio y para aprender RAG. Servicio RAG sobre el guion de
"The Big Lebowski" (stack 100% opensource).

## Funciones

- **Quote finder**: búsqueda semántica de citas del guion con contexto (personaje, escena).
- **Chat con El Dude**: conversación con la personalidad de El Dude, apoyándose en el guion
  (RAG: contexto recuperado + generación).

## Stack

| Capa        | Herramienta                  |
|-------------|------------------------------|
| LLM         | `llama3.2:3b` vía Ollama     |
| Embeddings  | `nomic-embed-text` (Ollama)  |
| Vector DB   | ChromaDB (local, `db/`)      |
| API         | FastAPI (SSE en `/chat`)     |
| Frontend    | Streamlit (2 pestañas)       |

## Requisitos

- macOS (Apple Silicon) o Linux, con Ollama instalado.
- Python 3.10+.

## Puesta en marcha local

```bash
# 1. Modelos
bash scripts/setup.sh

# 2. Dependencias
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Añadir el guion (no se versiona)
#    Copia data/thebiglebowski.pdf al directorio data/ (manual, por derechos del guion).

# 4. Ingesta
python ingest.py

# 5. API + UI
uvicorn app.main:app --reload     # http://localhost:8000
streamlit run app/ui.py           # http://localhost:8501
```

## Configuración

Variables de entorno en `.env` (ver `.env.example`):
`OLLAMA_HOST`, `DB_PATH`, `MODEL` (default `llama3.2:3b`), `EMBED_MODEL` (default `nomic-embed-text`).

## Estructura

Ver `AGENTS.md` para el árbol de directorios, convenciones y decisiones de diseño.

## Despliegue

- **Principal**: Oracle Cloud ARM Free Tier vía GitHub Actions (`deploy-oracle.yml`).
- **Demo extra**: Hugging Face Spaces (quote finder).
