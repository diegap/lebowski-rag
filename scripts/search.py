#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import Settings
from src.embeddings import OllamaEmbedder
from src.store import QuoteStore


def main() -> int:
    settings = Settings()

    parser = argparse.ArgumentParser(
        description="Search The Big Lebowski script"
    )
    parser.add_argument("queries", nargs="+", help="Search query(s)")
    parser.add_argument("-n", "--top", type=int, default=5, help="Number of results")
    parser.add_argument("-d", "--dude", action="store_true", help="Only The Dude")
    parser.add_argument("-c", "--character", default=None, help="Filter by character")
    parser.add_argument("--db", default=settings.DB_PATH)
    parser.add_argument("--host", default=settings.OLLAMA_HOST)
    parser.add_argument("--model", default=settings.EMBED_MODEL)
    args = parser.parse_args()

    embedder = OllamaEmbedder(host=args.host, model=args.model)
    store = QuoteStore(db_path=args.db, embedder=embedder)

    for query in args.queries:
        hits = store.search(
            query, top_k=args.top, character=args.character, dude_only=args.dude
        )
        if not hits:
            print(f'No results for "{query}"')
            continue

        print(f'\n--- "{query}" ({len(hits)} results) ---')
        for i, hit in enumerate(hits, 1):
            print(f"  {i}. [{hit.scene}] {hit.character} — {hit.heading}")
            print(f'     "{hit.text}"')
            print(f"     (distance: {hit.distance:.4f})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
