"""Assemble the full Agentic RAG StateGraph."""
from langgraph.graph import END, StateGraph

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
from app.graph.state import ResearchState

MAX_RETRIES = 3


def _route_after_router(state: ResearchState) -> str:
    return "retriever" if state["route"] == "vector_store" else "web_search"


def _route_after_grader(state: ResearchState) -> str:
    return "web_search" if len(state.get("graded_documents", [])) == 0 else "generator"


def _route_after_hallucination(state: ResearchState) -> str:
    if state.get("hallucination_pass"):
        return "relevance_checker"
    return "generator" if state.get("retry_count", 0) < MAX_RETRIES else "report_builder"


def _route_after_relevance(state: ResearchState) -> str:
    if state.get("relevance_pass"):
        return "report_builder"
    return "web_search" if state.get("retry_count", 0) < MAX_RETRIES else "report_builder"


def build_graph() -> StateGraph:
    graph = StateGraph(ResearchState)

    # Add nodes
    graph.add_node("router", route_question)
    graph.add_node("retriever", retrieve_documents)
    graph.add_node("web_search", web_search)
    graph.add_node("grader", grade_documents)
    graph.add_node("generator", generate_answer)
    graph.add_node("hallucination_checker", check_hallucination)
    graph.add_node("relevance_checker", check_relevance)
    graph.add_node("report_builder", build_report)

    # Entry point
    graph.set_entry_point("router")

    # Edges
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
