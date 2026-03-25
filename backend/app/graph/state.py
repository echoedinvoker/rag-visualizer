"""Graph state definition for the Agentic RAG pipeline."""
from typing import Literal, TypedDict


class ResearchState(TypedDict):
    question: str
    language: str  # "zh-TW" | "en"
    route: Literal["vector_store", "web_search"]
    documents: list[dict]
    graded_documents: list[dict]
    web_results: list[dict]
    generation: str
    hallucination_pass: bool
    relevance_pass: bool
    retry_count: int
    report: str
    sources: list[str]
