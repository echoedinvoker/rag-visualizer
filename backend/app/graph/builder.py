"""Config-driven graph factory.

Converts a JSON graph config into a compiled LangGraph ``StateGraph``.
Also preserves the legacy ``build_graph()`` for backward compatibility.
"""
from __future__ import annotations

from functools import partial

from langgraph.graph import END, START, StateGraph

from app.graph.registry import NODE_REGISTRY, make_field_router
from app.graph.state import SharedState
from app.graph.validator import validate_graph


def build_graph_from_config(config: dict) -> StateGraph:
    """Build and compile a LangGraph from a JSON config dict.

    Raises ``ValueError`` if the config fails validation.
    """
    errors = validate_graph(config)
    if errors:
        raise ValueError(f"Invalid graph config: {'; '.join(errors)}")

    builder = StateGraph(SharedState)

    # --- Add nodes ---
    for node_id, node_def in config["nodes"].items():
        node_type = node_def["type"]
        node_fn = NODE_REGISTRY[node_type]
        node_cfg = {**node_def.get("config", {}), "_node_id": node_id}
        builder.add_node(node_id, partial(node_fn, node_config=node_cfg))

    # --- Add regular edges ---
    for edge in config.get("edges", []):
        src = START if edge["source"] == "START" else edge["source"]
        tgt = END if edge["target"] == "END" else edge["target"]
        builder.add_edge(src, tgt)

    # --- Add conditional edges ---
    for cond in config.get("conditional_edges", []):
        src = START if cond["source"] == "START" else cond["source"]
        mapping = {}
        for value, tgt_id in cond["mapping"].items():
            mapping[value] = END if tgt_id == "END" else tgt_id
        router_fn = make_field_router(cond["router_field"], mapping)
        builder.add_conditional_edges(src, router_fn, mapping)

    return builder.compile()


# ---------------------------------------------------------------------------
# Legacy builder (backward compatibility for /api/research)
# ---------------------------------------------------------------------------

MAX_RETRIES = 3


def _route_after_router(state: SharedState) -> str:
    return "retriever" if state["route"] == "vector_store" else "web_search"


def _route_after_grader(state: SharedState) -> str:
    return "web_search" if len(state.get("graded_documents", [])) == 0 else "generator"


def _route_after_hallucination(state: SharedState) -> str:
    if state.get("hallucination_pass"):
        return "relevance_checker"
    return "generator" if state.get("retry_count", 0) < MAX_RETRIES else "report_builder"


def _route_after_relevance(state: SharedState) -> str:
    if state.get("relevance_pass"):
        return "report_builder"
    return "web_search" if state.get("retry_count", 0) < MAX_RETRIES else "report_builder"


def build_graph() -> StateGraph:
    """Legacy hardcoded graph builder — used by /api/research for backward compat."""
    from app.graph.nodes import (
        build_report,
        check_hallucination,
        check_relevance,
        generate_answer,
        grade_documents,
        retrieve_documents,
        route_question,
        web_search,
    )

    graph = StateGraph(SharedState)

    graph.add_node("router", route_question)
    graph.add_node("retriever", retrieve_documents)
    graph.add_node("web_search", web_search)
    graph.add_node("grader", grade_documents)
    graph.add_node("generator", generate_answer)
    graph.add_node("hallucination_checker", check_hallucination)
    graph.add_node("relevance_checker", check_relevance)
    graph.add_node("report_builder", build_report)

    graph.set_entry_point("router")

    graph.add_conditional_edges("router", _route_after_router, {
        "retriever": "retriever",
        "web_search": "web_search",
    })
    graph.add_edge("retriever", "grader")
    graph.add_conditional_edges("grader", _route_after_grader, {
        "web_search": "web_search",
        "generator": "generator",
    })
    graph.add_edge("web_search", "generator")
    graph.add_edge("generator", "hallucination_checker")
    graph.add_conditional_edges("hallucination_checker", _route_after_hallucination, {
        "relevance_checker": "relevance_checker",
        "generator": "generator",
        "report_builder": "report_builder",
    })
    graph.add_conditional_edges("relevance_checker", _route_after_relevance, {
        "report_builder": "report_builder",
        "web_search": "web_search",
    })
    graph.add_edge("report_builder", END)

    return graph.compile()
