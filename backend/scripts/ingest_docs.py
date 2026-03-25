"""Ingest LangChain/LangGraph documentation into Chroma vector store.

Idempotent: skips if collection already has documents.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.vectorstore import get_vectorstore

DOCS_BASE = "https://raw.githubusercontent.com/langchain-ai/docs/main/"

DOC_PATHS = [
    "src/oss/langgraph/graph-api.mdx",
    "src/oss/langgraph/workflows-agents.mdx",
    "src/oss/langgraph/thinking-in-langgraph.mdx",
    "src/oss/langgraph/agentic-rag.mdx",
    "src/oss/langgraph/streaming.mdx",
    "src/oss/langchain/rag.mdx",
    "src/oss/langchain/agents.mdx",
]

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def download_docs() -> list[dict]:
    """Download all docs from GitHub. Returns list of {content, source}."""
    docs = []
    with httpx.Client(timeout=30) as client:
        for path in DOC_PATHS:
            url = DOCS_BASE + path
            print(f"  Downloading {path}...")
            try:
                resp = client.get(url)
                resp.raise_for_status()
                docs.append({"content": resp.text, "source": path})
                print(f"    OK ({len(resp.text)} chars)")
            except httpx.HTTPError as e:
                print(f"    FAILED: {e}")
    return docs


def ingest():
    vectorstore = get_vectorstore()

    # Check if already ingested
    collection = vectorstore._collection
    count = collection.count()
    if count > 0:
        print(f"Collection already has {count} documents. Skipping ingest.")
        return

    print("Downloading documentation...")
    raw_docs = download_docs()
    if not raw_docs:
        print("No documents downloaded. Aborting.")
        return

    print(f"\nSplitting {len(raw_docs)} documents...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    all_texts = []
    all_metadatas = []
    for doc in raw_docs:
        chunks = splitter.split_text(doc["content"])
        for chunk in chunks:
            all_texts.append(chunk)
            all_metadatas.append({"source": doc["source"]})

    print(f"Ingesting {len(all_texts)} chunks into Chroma...")
    vectorstore.add_texts(texts=all_texts, metadatas=all_metadatas)
    print(f"Done! Collection now has {collection.count()} documents.")


if __name__ == "__main__":
    ingest()
