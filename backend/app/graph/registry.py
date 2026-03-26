"""Node and router registries for config-driven graph construction."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.graph.nodes import (
    build_report,
    check_hallucination,
    check_relevance,
    generate_answer,
    grade_documents,
    query_rewrite,
    retrieve_documents,
    summarize_documents,
    web_search,
    route_question,
)

# ---------------------------------------------------------------------------
# Node Registry: node_type string → async callable
# ---------------------------------------------------------------------------
NODE_REGISTRY: dict[str, Callable] = {
    "router": route_question,
    "retriever": retrieve_documents,
    "web_search": web_search,
    "grader": grade_documents,
    "generator": generate_answer,
    "hallucination_checker": check_hallucination,
    "relevance_checker": check_relevance,
    "report_builder": build_report,
    "summarizer": summarize_documents,
    "query_rewriter": query_rewrite,
}

# ---------------------------------------------------------------------------
# Generic Field Router Factory
# ---------------------------------------------------------------------------


def make_field_router(field: str, mapping: dict[str, str]) -> Callable:
    """Create a routing function that reads *field* from state and maps to a node.

    The *mapping* dict maps field values to target node IDs.  A ``"default"``
    key serves as a catch-all.
    """

    def router(state: dict[str, Any]) -> str:
        value = state.get(field)
        # Try exact match, then str conversion, then default
        target = mapping.get(value) or mapping.get(str(value)) or mapping.get("default")
        if target is None:
            raise ValueError(
                f"Router field '{field}' has value '{value}' "
                f"not found in mapping {list(mapping.keys())}. "
                f"Add a 'default' key to handle unexpected values."
            )
        return target

    return router
