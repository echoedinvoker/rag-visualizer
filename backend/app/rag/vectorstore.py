"""Chroma vector store management."""
import chromadb
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from app.config import CHROMA_PERSIST_DIR, get_openai_api_key


def get_vectorstore() -> Chroma:
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=get_openai_api_key(),
    )
    return Chroma(
        client=client,
        collection_name="langchain_docs",
        embedding_function=embeddings,
    )


def get_retriever(k: int = 5):
    return get_vectorstore().as_retriever(search_kwargs={"k": k})
