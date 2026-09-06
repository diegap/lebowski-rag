import json
from collections.abc import Iterator

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app import rag

app = FastAPI(title="Lebowski RAG", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    top_k: int = 5
    character: str | None = None
    dude_only: bool = False


def _sse(stream: Iterator[str]) -> Iterator[str]:
    for token in stream:
        if token == rag.DONE:
            yield f"data: {rag.DONE}\n\n"
            break
        yield f"data: {json.dumps({'token': token})}\n\n"


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "turns": rag.store.count()}


@app.get("/search")
def search(
    q: str = Query(..., description="Search query"),
    top_k: int = Query(default=5, ge=1, le=20),
    character: str | None = Query(default=None),
    dude_only: bool = Query(default=False),
) -> dict:
    hits = rag.retrieve(q, top_k, character, dude_only)
    return {
        "query": q,
        "results": [
            {
                "scene": hit.scene,
                "heading": hit.heading,
                "character": hit.character,
                "text": hit.text,
                "distance": hit.distance,
            }
            for hit in hits
        ],
    }


@app.post("/chat")
def chat(req: ChatRequest) -> StreamingResponse:
    stream = rag.generate_stream(
        req.message,
        top_k=req.top_k,
        character=req.character,
        dude_only=req.dude_only,
    )
    return StreamingResponse(
        _sse(stream),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
