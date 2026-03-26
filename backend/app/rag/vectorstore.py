"""Chroma vector store management."""
import chromadb
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from app.config import CHROMA_PERSIST_DIR, get_openai_api_key


def get_vectorstore(collection_name: str = "langchain_docs") -> Chroma:
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=get_openai_api_key(),
    )
    return Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embeddings,
    )


def get_retriever(k: int = 5, collection_name: str = "langchain_docs"):
    return get_vectorstore(collection_name).as_retriever(search_kwargs={"k": k})


def delete_collection(collection_name: str):
    """Delete a Chroma collection by name."""
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    try:
        client.delete_collection(collection_name)
    except ValueError:
        pass  # Collection doesn't exist


def list_collections() -> list[str]:
    """List all Chroma collection names."""
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    return [c.name for c in client.list_collections()]
