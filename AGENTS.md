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
├── ingest.py                # orquestación de ingesta (parser -> embeddings -> ChromaDB)
├── src/
│   ├── config.py            # Settings desde .env (OLLAMA_HOST, DB_PATH, MODEL, EMBED_MODEL)
│   ├── embeddings.py        # OllamaEmbedder: embed_documents() / embed_query()
│   ├── store.py             # QuoteStore (index/search/count) + QuoteHit; contrato cliente-agnóstico
│   └── pdf_loader.py        # extraer texto Final Draft -> escenas/turnos de diálogo
├── scripts/
│   ├── search.py            # demo CLI de retrieval (previo a la API)
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
- **Ingesta**: `python ingest.py` (PDF -> turnos de diálogo -> embeddings -> ChromaDB).
- **Retrieval (demo CLI, previo a la API)**: `python scripts/search.py "that rug really tied
  the room together"` (flags: `-n/--top`, `-d/--dude`, `-c/--character`).
- **API**: `uvicorn app.main:app --reload`
- **UI**: `streamlit run app/ui.py`

## Configuración

Config vía variables de entorno (`.env`, ver `.env.example`):
`OLLAMA_HOST`, `DB_PATH`, `MODEL` (default `llama3.2:3b`), `EMBED_MODEL` (default `nomic-embed-text`),
`API_URL` (default `http://localhost:8000`).

## Convenciones

- No añadir comentarios en el código salvo que se pidan explícitamente.
- No versionar secretos, el PDF, la BD vectorial ni `.env`.
- Python 3, estilo cercano al estándar; sin librerías adicionales sin justificar.

## Decisiones registradas (ADR breve)

- **ChromaDB** como vector store por sencillez a esta escala (1271 turnos de diálogo en la
  colección `quotes`); FAISS sería overkill.
- **Capa de dominio cliente-agnóstica en `src/`**: `QuoteStore` (con `OllamaEmbedder`
  inyectado) es el único contrato que usan CLI (`scripts/search.py`), API (`app/main.py`) y
  UI (`app/ui.py`). Los clientes son capas de presentación delgadas; el embedder inyectado
  permite testear la búsqueda sin Ollama.
- **Chunking por turno de diálogo** (con metadatos `character`, `heading`, `scene`,
  `is_dude`) en lugar de escena completa: recuperación afilada para el quote finder y
  filtro por personaje (p. ej. solo El Dude).
- **`llama3.2:3b`** único LLM por fluidez; el fallback 8b se descartó pero es trivial de
  reintroducir.
- **Historial de chat en memoria/sesión** (MVP), sin persistencia.
- **PDF excluido** del control de versiones por derechos del guion.
- **Python de punta a punta** (FastAPI + ChromaDB + Streamlit) en lugar de Kotlin: es el
  estándar del ecosistema RAG y el objetivo del proyecto es aprender RAG, no backend JVM.
- **Despliegue principal**: Oracle Cloud ARM Free Tier (2 OCPU / 12 GB, `A1.Flex`) vía
  GitHub Actions. `scripts/deploy_oracle.sh` provisiona la VM (Ollama, systemd para API y
  UI, nginx HTTPS + WebSocket → Streamlit, certbot, ufw, cron DuckDNS). Dominio DuckDNS.
  Extra: Hugging Face Spaces como demo del quote finder.

## CI / Despliegue

- `ci.yml`: en cada push, lint + smoke test de retrieval/keywords (sin Ollama en runners).
- `deploy-oracle.yml`: `workflow_dispatch` + push a `main`; despliega a Oracle ARM vía SSH
  (scp de `app`/`src`/scripts, provisionamiento con `scripts/deploy_oracle.sh`, reinicio de
  FastAPI + Streamlit por systemd). Deshabilitado hasta que existan los secretos de la VM
  Oracle (`ORACLE_HOST`, `ORACLE_USER`, `ORACLE_SSH_PRIVATE_KEY`, `ORACLE_DOMAIN`,
  `DUCKDNS_TOKEN`).

## Gestión de sesiones

Avisar al usuario cada vez que sea conveniente iniciar una nueva sesión, para no saturar el
contexto. Momentos típicos para avisar:

- Al iniciar una fase nueva e independiente del proyecto (p. ej. pasar del bootstrap a la
  Fase 1 del pipeline de ingesta).
- Cuando la conversación actual se ha vuelto larga o repite mucho contexto.
- Antes de tareas pesadas que requieran cargar mucho código/mensajes en contexto.

Avisar de forma breve, indicando qué se hará en la nueva sesión y por qué conviene una
sesión limpia.
