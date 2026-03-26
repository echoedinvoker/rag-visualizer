"""Shared state definition for the dynamic RAG pipeline."""
from typing import Annotated, TypedDict

from operator import add


class SharedState(TypedDict):
    """Superset state shared by all node types.

    Each node reads only the fields it needs and returns only the fields it modifies.
    Fields using ``Annotated[list, add]`` accumulate across multiple node invocations;
    plain fields are overwritten.
    """

    # --- Query ---
    question: str                                       # current question (may be rewritten)
    original_question: str                              # preserved original question
    language: str                                       # "zh-TW" | "en"

    # --- Routing ---
    route: str                                          # router decision (e.g. "vector_store", "web_search")

    # --- Retrieval ---
    documents: list[dict]                               # raw retrieved documents (overwrite per retrieval)
    graded_documents: list[dict]                        # documents that passed grading (overwrite per grading)
    web_results: Annotated[list[dict], add]             # web search results (accumulate)

    # --- Generation ---
    generation: str                                     # LLM-generated answer (overwrite)
    summary: str                                        # summarizer output

    # --- Quality gates ---
    hallucination_pass: bool                            # grounded in documents?
    relevance_pass: bool                                # answers the question?
    grader_fallback: bool                               # all documents filtered out?
    retry_count: int                                    # generation retry counter

    # --- Output ---
    report: str                                         # formatted final report
    sources: Annotated[list[str], add]                  # citation sources (accumulate)


# Backward compatibility alias
ResearchState = SharedState
