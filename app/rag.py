import json
from collections.abc import Iterator

import httpx

from src.config import Settings
from src.embeddings import OllamaEmbedder
from src.store import QuoteHit, QuoteStore

settings = Settings()
embedder = OllamaEmbedder(host=settings.OLLAMA_HOST, model=settings.EMBED_MODEL)
store = QuoteStore(db_path=settings.DB_PATH, embedder=embedder)

DUDE_SYSTEM = (
    "You are The Dude — Jeffrey Lebowski — from The Big Lebowski. You speak in a "
    "laid-back, casual California Dude voice. Use Dude-isms (\"man\", \"abide\", "
    "\"that's just, like, your opinion, man\"). Never break character at any time. "
    "You only know things from the events of The Big Lebowski. If you don't know "
    "something, say so in a Dude-like way. Keep answers brief and conversational."
)

DONE = "[DONE]"


def retrieve(
    query: str,
    top_k: int = 5,
    character: str | None = None,
    dude_only: bool = False,
) -> list[QuoteHit]:
    return store.search(query, top_k=top_k, character=character, dude_only=dude_only)


def build_context(hits: list[QuoteHit]) -> str:
    lines = []
    for hit in hits:
        lines.append(
            f"[scene {hit.scene}] {hit.character} — {hit.heading}\n"
            f'"{hit.text}"'
        )
    return "\n".join(lines)


def build_prompt(message: str, context: str) -> str:
    if context:
        return (
            f"Context from The Big Lebowski script:\n{context}\n\n"
            f"User: {message}\nThe Dude:"
        )
    return f"User: {message}\nThe Dude:"


def generate_stream(
    message: str,
    top_k: int = 5,
    character: str | None = None,
    dude_only: bool = False,
) -> Iterator[str]:
    try:
        hits = retrieve(message, top_k, character, dude_only)
        prompt = build_prompt(message, build_context(hits))
        payload = {
            "model": settings.MODEL,
            "system": DUDE_SYSTEM,
            "prompt": prompt,
            "stream": True,
        }
        with httpx.stream(
            "POST",
            f"{settings.OLLAMA_HOST}/api/generate",
            json=payload,
            timeout=httpx.Timeout(300.0),
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                token = chunk.get("response", "")
                if token:
                    yield token
    except httpx.HTTPError as exc:
        yield f"\n[Dude is unreachable: Ollama error ({exc.__class__.__name__})]"
    yield DONE
