import argparse
import os
import sys
from pathlib import Path

import chromadb
import httpx
from dotenv import load_dotenv

from src import pdf_loader

load_dotenv()

DEFAULT_PDF = Path("data/thebiglebowski.pdf")
DEFAULT_OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
DEFAULT_DB_PATH = os.getenv("DB_PATH", "./db")

COLLECTION = "quotes"
EMBED_BATCH = 32
SEARCH_DOC_PREFIX = "search_document: "


def embed(texts: list[str], host: str, model: str) -> list[list[float]]:
    embeddings: list[list[float]] = []
    with httpx.Client(base_url=host, timeout=120) as client:
        for i in range(0, len(texts), EMBED_BATCH):
            batch = [SEARCH_DOC_PREFIX + t for t in texts[i : i + EMBED_BATCH]]
            resp = client.post("/api/embed", json={"model": model, "input": batch})
            resp.raise_for_status()
            embeddings.extend(resp.json()["embeddings"])
    return embeddings


def get_collection(path: str):
    client = chromadb.PersistentClient(path=path)
    return client.get_or_create_collection(
        COLLECTION,
        metadata={"hnsw:space": "cosine"},
        embedding_function=None,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest The Big Lebowski script into ChromaDB")
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--db", default=DEFAULT_DB_PATH)
    parser.add_argument("--host", default=DEFAULT_OLLAMA_HOST)
    parser.add_argument("--model", default=DEFAULT_EMBED_MODEL)
    args = parser.parse_args()

    if not args.pdf.exists():
        print(f"PDF no encontrado: {args.pdf}", file=sys.stderr)
        return 1

    turns = pdf_loader.parse_script(args.pdf)
    if not turns:
        print("No se extrajeron turnos de diálogo", file=sys.stderr)
        return 1

    texts = [t.text for t in turns]
    print(f"Extrayendo embeddings de {len(texts)} turnos con {args.model}...")
    try:
        embeddings = embed(texts, args.host, args.model)
    except httpx.HTTPError as exc:
        print(f"Error llamando a Ollama en {args.host}: {exc}", file=sys.stderr)
        return 1

    ids = [f"{t.scene:03d}-{i:03d}" for i, t in enumerate(turns)]
    metadatas = [
        {
            "scene": t.scene,
            "heading": t.heading,
            "character": t.character,
            "is_dude": t.speaker_is_dude,
        }
        for t in turns
    ]

    collection = get_collection(args.db)
    collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    print(f"Ingesta completada: {len(turns)} turnos en colección '{COLLECTION}' ({args.db}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())