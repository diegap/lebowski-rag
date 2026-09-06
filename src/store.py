from dataclasses import dataclass

import chromadb

from src.embeddings import OllamaEmbedder
from src.pdf_loader import DialogueTurn

COLLECTION = "quotes"


@dataclass
class QuoteHit:
    scene: int
    heading: str
    character: str
    text: str
    distance: float


class QuoteStore:
    def __init__(self, db_path: str, embedder: OllamaEmbedder) -> None:
        self.embedder = embedder
        client = chromadb.PersistentClient(path=db_path)
        self._col = client.get_or_create_collection(
            COLLECTION,
            metadata={"hnsw:space": "cosine"},
            embedding_function=None,
        )

    def index(self, turns: list[DialogueTurn]) -> None:
        ids = [f"{t.scene:03d}-{i:03d}" for i, t in enumerate(turns)]
        texts = [t.text for t in turns]
        embeddings = self.embedder.embed_documents(texts)
        metadatas = [
            {
                "scene": t.scene,
                "heading": t.heading,
                "character": t.character,
                "is_dude": t.speaker_is_dude,
            }
            for t in turns
        ]
        self._col.upsert(
            ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
        character: str | None = None,
        dude_only: bool = False,
    ) -> list[QuoteHit]:
        q_emb = self.embedder.embed_query(query)

        where = None
        if dude_only:
            where = {"is_dude": True}
        elif character is not None:
            where = {"character": character.upper()}

        results = self._col.query(
            query_embeddings=[q_emb],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        hits: list[QuoteHit] = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            hits.append(
                QuoteHit(
                    scene=meta["scene"],
                    heading=meta["heading"],
                    character=meta["character"],
                    text=doc,
                    distance=dist,
                )
            )
        return hits

    def count(self) -> int:
        return self._col.count()
