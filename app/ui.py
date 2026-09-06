import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
import streamlit as st

from src.config import Settings

st.set_page_config(page_title="Lebowski RAG", page_icon="🎳", layout="centered")

settings = Settings()
API_URL = settings.API_URL
TIMEOUT_SEARCH = httpx.Timeout(connect=10.0, read=300.0, write=10.0, pool=10.0)
TIMEOUT_CHAT = httpx.Timeout(connect=10.0, read=None, write=10.0, pool=10.0)

st.title("Lebowski RAG")
tab_search, tab_chat = st.tabs(["Quote Finder", "Chat with El Dude"])

# ---------------------------------------------------------------------------
# Quote Finder
# ---------------------------------------------------------------------------
with tab_search:
    query = st.text_input("Search the script", placeholder="that rug really tied the room together")

    col1, col2, col3 = st.columns(3)
    with col1:
        top_k = st.selectbox("Results", range(1, 21), index=4)
    with col2:
        character = st.text_input("Character", placeholder="e.g. WALTER")
    with col3:
        dude_only = st.checkbox("Only The Dude")

    if st.button("Search", type="primary") and query:
        params = {"q": query, "top_k": top_k, "dude_only": dude_only}
        if character:
            params["character"] = character

        try:
            with httpx.Client(timeout=TIMEOUT_SEARCH) as client:
                resp = client.get(f"{API_URL}/search", params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.ConnectError:
            st.error(f"Cannot connect to API at {API_URL}. Is uvicorn running?")
            st.stop()

        results = data.get("results", [])
        st.info(f"**{data['query']}** — {len(results)} result(s)")

        for hit in results:
            with st.expander(f"[Scene {hit['scene']}] {hit['character']} — {hit['heading']}"):
                st.markdown(f"**{hit['heading']}**")
                st.markdown(f"**{hit['character']}:** _{hit['text']}_")
                st.caption(f"Distance: {hit['distance']:.4f}")

# ---------------------------------------------------------------------------
# Chat with El Dude
# ---------------------------------------------------------------------------
with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Ask The Dude..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        payload = {"message": prompt}
        try:
            with httpx.Client(timeout=TIMEOUT_CHAT) as client:
                with client.stream(
                    "POST", f"{API_URL}/chat", json=payload
                ) as stream:
                    def _sse_tokens():
                        for line in stream.iter_lines():
                            if not line.startswith("data: "):
                                continue
                            raw = line[len("data: "):]
                            if raw == "[DONE]":
                                break
                            yield json.loads(raw).get("token", "")

                    with st.chat_message("assistant"):
                        full = st.write_stream(_sse_tokens())
        except httpx.ConnectError:
            with st.chat_message("assistant"):
                st.error(f"Cannot connect to API at {API_URL}. Is uvicorn running?")
            full = ""

        st.session_state.messages.append({"role": "assistant", "content": full or ""})
