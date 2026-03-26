"""Predefined pipeline templates.

Each template is a complete GraphConfig dict that can be fed directly to
``build_graph_from_config()``.
"""
from __future__ import annotations

TEMPLATES: dict[str, dict] = {
    "simple-rag": {
        "id": "simple-rag",
        "name": "Simple RAG",
        "description": "Basic RAG pipeline: route → retrieve → generate → report. No quality checks.",
        "config": {
            "nodes": {
                "router_1": {
                    "type": "router",
                    "config": {"model": "gpt-4o-mini"},
                    "position": {"x": 250, "y": 0},
                },
                "retriever_1": {
                    "type": "retriever",
                    "config": {"knowledge_base": "langchain_docs", "top_k": 5},
                    "position": {"x": 100, "y": 150},
                },
                "web_search_1": {
                    "type": "web_search",
                    "config": {"max_results": 3},
                    "position": {"x": 400, "y": 150},
                },
                "generator_1": {
                    "type": "generator",
                    "config": {"model": "gpt-4o-mini"},
                    "position": {"x": 250, "y": 300},
                },
                "report_1": {
                    "type": "report_builder",
                    "config": {},
                    "position": {"x": 250, "y": 450},
                },
            },
            "edges": [
                {"source": "START", "target": "router_1"},
                {"source": "retriever_1", "target": "generator_1"},
                {"source": "web_search_1", "target": "generator_1"},
                {"source": "generator_1", "target": "report_1"},
                {"source": "report_1", "target": "END"},
            ],
            "conditional_edges": [
                {
                    "source": "router_1",
                    "router_field": "route",
                    "mapping": {
                        "vector_store": "retriever_1",
                        "web_search": "web_search_1",
                    },
                },
            ],
        },
    },

    "crag": {
        "id": "crag",
        "name": "CRAG",
        "description": "Corrective RAG: adds document grading. If all documents fail, falls back to web search.",
        "config": {
            "nodes": {
                "router_1": {
                    "type": "router",
                    "config": {"model": "gpt-4o-mini"},
                    "position": {"x": 250, "y": 0},
                },
                "retriever_1": {
                    "type": "retriever",
                    "config": {"knowledge_base": "langchain_docs", "top_k": 5},
                    "position": {"x": 100, "y": 150},
                },
                "web_search_1": {
                    "type": "web_search",
                    "config": {"max_results": 3},
                    "position": {"x": 400, "y": 150},
                },
                "grader_1": {
                    "type": "grader",
                    "config": {"model": "gpt-4o-mini"},
                    "position": {"x": 100, "y": 300},
                },
                "generator_1": {
                    "type": "generator",
                    "config": {"model": "gpt-4o-mini"},
                    "position": {"x": 250, "y": 450},
                },
                "report_1": {
                    "type": "report_builder",
                    "config": {},
                    "position": {"x": 250, "y": 600},
                },
            },
            "edges": [
                {"source": "START", "target": "router_1"},
                {"source": "retriever_1", "target": "grader_1"},
                {"source": "web_search_1", "target": "generator_1"},
                {"source": "generator_1", "target": "report_1"},
                {"source": "report_1", "target": "END"},
            ],
            "conditional_edges": [
                {
                    "source": "router_1",
                    "router_field": "route",
                    "mapping": {
                        "vector_store": "retriever_1",
                        "web_search": "web_search_1",
                    },
                },
                {
                    "source": "grader_1",
                    "router_field": "grader_fallback",
                    "mapping": {
                        "True": "web_search_1",
                        "False": "generator_1",
                    },
                },
            ],
        },
    },

    "self-rag": {
        "id": "self-rag",
        "name": "Self-RAG",
        "description": "Adds hallucination and relevance checks after generation. Retries if quality fails.",
        "config": {
            "nodes": {
                "router_1": {
                    "type": "router",
                    "config": {"model": "gpt-4o-mini"},
                    "position": {"x": 250, "y": 0},
                },
                "retriever_1": {
                    "type": "retriever",
                    "config": {"knowledge_base": "langchain_docs", "top_k": 5},
                    "position": {"x": 100, "y": 150},
                },
                "web_search_1": {
                    "type": "web_search",
                    "config": {"max_results": 3},
                    "position": {"x": 400, "y": 150},
                },
                "generator_1": {
                    "type": "generator",
                    "config": {"model": "gpt-4o-mini", "max_retries": 3},
                    "position": {"x": 250, "y": 300},
                },
                "hallucination_1": {
                    "type": "hallucination_checker",
                    "config": {"model": "gpt-4o-mini"},
                    "position": {"x": 250, "y": 450},
                },
                "relevance_1": {
                    "type": "relevance_checker",
                    "config": {"model": "gpt-4o-mini"},
                    "position": {"x": 250, "y": 600},
                },
                "report_1": {
                    "type": "report_builder",
                    "config": {},
                    "position": {"x": 250, "y": 750},
                },
            },
            "edges": [
                {"source": "START", "target": "router_1"},
                {"source": "retriever_1", "target": "generator_1"},
                {"source": "web_search_1", "target": "generator_1"},
                {"source": "generator_1", "target": "hallucination_1"},
                {"source": "report_1", "target": "END"},
            ],
            "conditional_edges": [
                {
                    "source": "router_1",
                    "router_field": "route",
                    "mapping": {
                        "vector_store": "retriever_1",
                        "web_search": "web_search_1",
                    },
                },
                {
                    "source": "hallucination_1",
                    "router_field": "hallucination_pass",
                    "mapping": {
                        "True": "relevance_1",
                        "False": "generator_1",
                        "default": "report_1",
                    },
                },
                {
                    "source": "relevance_1",
                    "router_field": "relevance_pass",
                    "mapping": {
                        "True": "report_1",
                        "False": "web_search_1",
                        "default": "report_1",
                    },
                },
            ],
        },
    },

    "full-agentic": {
        "id": "full-agentic",
        "name": "Full Agentic RAG",
        "description": "Complete 3-layer RAG: routing + document grading + hallucination/relevance checks with retry.",
        "config": {
            "nodes": {
                "router_1": {
                    "type": "router",
                    "config": {"model": "gpt-4o-mini"},
                    "position": {"x": 250, "y": 0},
                },
                "retriever_1": {
                    "type": "retriever",
                    "config": {"knowledge_base": "langchain_docs", "top_k": 5},
                    "position": {"x": 100, "y": 150},
                },
                "web_search_1": {
                    "type": "web_search",
                    "config": {"max_results": 3},
                    "position": {"x": 400, "y": 150},
                },
                "grader_1": {
                    "type": "grader",
                    "config": {"model": "gpt-4o-mini"},
                    "position": {"x": 100, "y": 300},
                },
                "generator_1": {
                    "type": "generator",
                    "config": {"model": "gpt-4o-mini", "max_retries": 3},
                    "position": {"x": 250, "y": 450},
                },
                "hallucination_1": {
                    "type": "hallucination_checker",
                    "config": {"model": "gpt-4o-mini"},
                    "position": {"x": 250, "y": 600},
                },
                "relevance_1": {
                    "type": "relevance_checker",
                    "config": {"model": "gpt-4o-mini"},
                    "position": {"x": 250, "y": 750},
                },
                "report_1": {
                    "type": "report_builder",
                    "config": {},
                    "position": {"x": 250, "y": 900},
                },
            },
            "edges": [
                {"source": "START", "target": "router_1"},
                {"source": "retriever_1", "target": "grader_1"},
                {"source": "web_search_1", "target": "generator_1"},
                {"source": "generator_1", "target": "hallucination_1"},
                {"source": "report_1", "target": "END"},
            ],
            "conditional_edges": [
                {
                    "source": "router_1",
                    "router_field": "route",
                    "mapping": {
                        "vector_store": "retriever_1",
                        "web_search": "web_search_1",
                    },
                },
                {
                    "source": "grader_1",
                    "router_field": "grader_fallback",
                    "mapping": {
                        "True": "web_search_1",
                        "False": "generator_1",
                    },
                },
                {
                    "source": "hallucination_1",
                    "router_field": "hallucination_pass",
                    "mapping": {
                        "True": "relevance_1",
                        "False": "generator_1",
                        "default": "report_1",
                    },
                },
                {
                    "source": "relevance_1",
                    "router_field": "relevance_pass",
                    "mapping": {
                        "True": "report_1",
                        "False": "web_search_1",
                        "default": "report_1",
                    },
                },
            ],
        },
    },
}


def get_template(template_id: str) -> dict | None:
    return TEMPLATES.get(template_id)


def list_templates() -> list[dict]:
    return [
        {"id": t["id"], "name": t["name"], "description": t["description"]}
        for t in TEMPLATES.values()
    ]
