import argparse
import sys
from pathlib import Path

import httpx

from src.config import Settings
from src.embeddings import OllamaEmbedder
from src.pdf_loader import parse_script
from src.store import QuoteStore


def main() -> int:
    settings = Settings()

    parser = argparse.ArgumentParser(
        description="Ingest The Big Lebowski script into ChromaDB"
    )
    parser.add_argument("--pdf", type=Path, default=settings.PDF)
    parser.add_argument("--db", default=settings.DB_PATH)
    parser.add_argument("--host", default=settings.OLLAMA_HOST)
    parser.add_argument("--model", default=settings.EMBED_MODEL)
    args = parser.parse_args()

    if not args.pdf.exists():
        print(f"PDF not found: {args.pdf}", file=sys.stderr)
        return 1

    turns = parse_script(args.pdf)
    if not turns:
        print("No dialogue turns extracted", file=sys.stderr)
        return 1

    embedder = OllamaEmbedder(host=args.host, model=args.model)
    store = QuoteStore(db_path=args.db, embedder=embedder)

    print(f"Embedding {len(turns)} turns with {args.model}...")
    try:
        store.index(turns)
    except httpx.HTTPError as exc:
        print(f"Error calling Ollama at {args.host}: {exc}", file=sys.stderr)
        return 1

    print(f"Ingestion complete: {store.count()} turns in collection 'quotes' ({args.db}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
