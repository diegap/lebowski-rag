# AGENTS.md

Contexto de trabajo para el proyecto **lebowski-rag** y los agentes que colaboran en él.

## Proyecto

Side-project para portfolio y para aprender RAG. Servicio basado en RAG sobre el guion de
"The Big Lebowski" con dos funciones:

- **Quote finder**: búsqueda semántica de citas del guion con contexto (personaje, escena).
- **Chat con El Dude**: conversación con la personalidad de El Dude, respondiendo con
  apoyo del guion (RAG: contexto recuperado + generación).

## Stack (confirmado)

- **LLM**: `llama3.2:3b` (instruct) vía Ollama. **Sin fallback a 8b** (descartado por fluidez;
  fácil de reintroducir con `ollama pull llama3.1:8b` + variable `MODEL`).
- **Embeddings**: `nomic-embed-text` (Ollama, 768 dims).
- **Vector store**: ChromaDB (persistencia local en `db/`).
- **API**: FastAPI, con streaming SSE en `/chat`.
- **Frontend**: Streamlit, 2 pestañas (Quote finder + Chat El Dude).
- **Fuente**: `data/thebiglebowski.pdf` (creado con Final Draft, texto nativo, 138 páginas).
  El PDF se **excluye de git** por derechos del guion; se añade manualmente (scp/prod).

## Estructura de directorios

```
lebowski-rag/
├── AGENTS.md
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── data/
│   ├── .gitkeep
│   └── thebiglebowski.pdf   # NO versionado (añadir manualmente)
├── src/
│   └── pdf_loader.py        # extraer texto Final Draft -> escenas/personajes
├── scripts/
│   ├── setup.sh             # ollama pull de modelos
│   └── deploy_oracle.sh     # pasos para Oracle ARM (systemd, nginx, HTTPS)
├── app/
│   ├── main.py              # FastAPI: /search + /chat (SSE)
│   ├── rag.py               # retrieve + prompt (voz del Dude) + llamada Ollama
│   └── ui.py                # Streamlit
└── .github/workflows/
    ├── ci.yml               # lint + smoke test (sin Ollama en runners)
    └── deploy-oracle.yml    # deploy a Oracle ARM (workflow_dispatch)
```

## Comandos

- **Setup de modelos**: `bash scripts/setup.sh` (instala/actualiza Ollama + pull de
  `llama3.2:3b` y `nomic-embed-text`).
- **Ingesta**: `python ingest.py` (PDF -> chunks por escena -> embeddings -> ChromaDB).
- **API**: `uvicorn app.main:app --reload`
- **UI**: `streamlit run app/ui.py`

## Configuración

Config vía variables de entorno (`.env`, ver `.env.example`):
`OLLAMA_HOST`, `DB_PATH`, `MODEL` (default `llama3.2:3b`), `EMBED_MODEL` (default `nomic-embed-text`).

## Convenciones

- No añadir comentarios en el código salvo que se pidan explícitamente.
- No versionar secretos, el PDF, la BD vectorial ni `.env`.
- Python 3, estilo cercano al estándar; sin librerías adicionales sin justificar.

## Decisiones registradas (ADR breve)

- **ChromaDB** como vector store por sencillez a esta escala (~500 chunks); FAISS sería
  overkill.
- **`llama3.2:3b`** único LLM por fluidez; el fallback 8b se descartó pero es trivial de
  reintroducir.
- **Historial de chat en memoria/sesión** (MVP), sin persistencia.
- **PDF excluido** del control de versiones por derechos del guion.
- **Python de punta a punta** (FastAPI + ChromaDB + Streamlit) en lugar de Kotlin: es el
  estándar del ecosistema RAG y el objetivo del proyecto es aprender RAG, no backend JVM.
- **Despliegue principal**: Oracle Cloud ARM Free Tier (24 GB RAM) vía GitHub Actions.
  Extra: Hugging Face Spaces como demo del quote finder.

## CI / Despliegue

- `ci.yml`: en cada push, lint + smoke test de retrieval/keywords (sin Ollama en runners).
- `deploy-oracle.yml`: `workflow_dispatch` + push a `main`; despliega a Oracle ARM vía SSH
  (pull, setup Ollama/modelos, reinicio de FastAPI + Streamlit por systemd). Deshabilitado
  hasta que existan los secretos de la VM Oracle.
