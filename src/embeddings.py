import httpx

DOC_PREFIX = "search_document: "
QUERY_PREFIX = "search_query: "
DEFAULT_BATCH = 32
DEFAULT_TIMEOUT = 120


class OllamaEmbedder:
    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        batch_size: int = DEFAULT_BATCH,
    ) -> None:
        self.host = host
        self.model = model
        self.batch_size = batch_size

    def _call(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        with httpx.Client(base_url=self.host, timeout=DEFAULT_TIMEOUT) as client:
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i : i + self.batch_size]
                resp = client.post(
                    "/api/embed", json={"model": self.model, "input": batch}
                )
                resp.raise_for_status()
                embeddings.extend(resp.json()["embeddings"])
        return embeddings

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        prefixed = [DOC_PREFIX + t for t in texts]
        return self._call(prefixed)

    def embed_query(self, text: str) -> list[float]:
        prefixed = [QUERY_PREFIX + text]
        return self._call(prefixed)[0]
