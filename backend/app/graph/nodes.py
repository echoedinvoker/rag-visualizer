"""All node functions for the dynamic RAG pipeline.

Every node follows the same contract:
    async def node_fn(state: SharedState, *, node_config: dict | None = None) -> dict

``node_config`` is injected by ``functools.partial`` at graph-build time so
each instance of the same node type can carry different settings.

The node ID used in stream events comes from ``node_config["_node_id"]``,
which is set automatically by the graph builder.
"""
from __future__ import annotations

import time
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.config import get_stream_writer
from pydantic import BaseModel, Field

from app.config import get_openai_api_key
from app.graph.prompts import (
    GENERATOR_SYSTEM,
    GRADER_SYSTEM,
    HALLUCINATION_SYSTEM,
    QUERY_REWRITER_SYSTEM,
    RELEVANCE_SYSTEM,
    REPORT_SYSTEM,
    ROUTER_SYSTEM,
    SUMMARIZER_SYSTEM,
)
from app.graph.state import SharedState
from app.rag.vectorstore import get_retriever
from app.tools.web_search import get_web_search_tool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _llm(model: str = "gpt-4o-mini", temperature: float = 0) -> ChatOpenAI:
    return ChatOpenAI(model=model, temperature=temperature, api_key=get_openai_api_key())


def _ts() -> int:
    return int(time.time())


def _nid(node_config: dict | None) -> str:
    """Return the node ID stored in config, or 'unknown'."""
    return (node_config or {}).get("_node_id", "unknown")


def _cfg(node_config: dict | None, key: str, default=None):
    """Read a setting from node_config with a fallback."""
    return (node_config or {}).get(key, default)


def get_best_documents(state: SharedState) -> list[dict]:
    """Pick the best available document list: graded > raw > web_results."""
    docs = state.get("graded_documents") or state.get("documents") or state.get("web_results") or []
    return docs


# ---------------------------------------------------------------------------
# Structured output schemas
# ---------------------------------------------------------------------------

class RouteQuery(BaseModel):
    """Route a user question to the appropriate data source."""
    route: Literal["vector_store", "web_search"] = Field(
        description="Route to vector_store for LangChain/LangGraph topics, web_search otherwise"
    )


class GradeDocument(BaseModel):
    """Binary relevance score for a retrieved document."""
    relevant: Literal["yes", "no"] = Field(description="Is the document relevant to the question?")


class HallucinationCheck(BaseModel):
    """Check if generation is grounded in documents."""
    grounded: Literal["yes", "no"] = Field(description="Is the generation grounded in the documents?")


class RelevanceCheck(BaseModel):
    """Check if generation answers the question."""
    useful: Literal["yes", "no"] = Field(description="Does the generation answer the question?")


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------

async def route_question(state: SharedState, *, node_config: dict | None = None) -> dict:
    nid = _nid(node_config)
    model = _cfg(node_config, "model", "gpt-4o-mini")
    writer = get_stream_writer()
    writer({"event": "node_start", "node": nid, "type": "router", "timestamp": _ts()})

    llm = _llm(model).with_structured_output(RouteQuery)
    prompt = ChatPromptTemplate.from_messages([
        ("system", ROUTER_SYSTEM),
        ("human", "{question}"),
    ])
    chain = prompt | llm
    result = await chain.ainvoke({"question": state["question"]})

    writer({
        "event": "route_decision",
        "node": nid,
        "decision": result.route,
        "timestamp": _ts(),
    })
    return {"route": result.route}


async def retrieve_documents(state: SharedState, *, node_config: dict | None = None) -> dict:
    nid = _nid(node_config)
    top_k = _cfg(node_config, "top_k", 5)
    knowledge_base = _cfg(node_config, "knowledge_base", "langchain-docs")
    writer = get_stream_writer()
    writer({"event": "node_start", "node": nid, "type": "retriever", "timestamp": _ts()})

    retriever = get_retriever(k=top_k, collection_name=knowledge_base)
    docs = await retriever.ainvoke(state["question"])
    doc_list = [
        {"content": doc.page_content, "source": doc.metadata.get("source", "unknown")}
        for doc in docs
    ]

    writer({
        "event": "documents_retrieved",
        "node": nid,
        "count": len(doc_list),
        "sources": [d["source"] for d in doc_list],
        "timestamp": _ts(),
    })
    return {"documents": doc_list}


async def web_search(state: SharedState, *, node_config: dict | None = None) -> dict:
    nid = _nid(node_config)
    max_results = _cfg(node_config, "max_results", 3)
    writer = get_stream_writer()
    writer({"event": "node_start", "node": nid, "type": "web_search", "timestamp": _ts()})

    tool = get_web_search_tool(max_results=max_results)
    raw = await tool.ainvoke(state["question"])
    results = raw.get("results", []) if isinstance(raw, dict) else raw
    web_list = [
        {"content": r.get("content", ""), "source": r.get("url", "")}
        for r in results
    ]

    writer({
        "event": "web_search_complete",
        "node": nid,
        "count": len(web_list),
        "sources": [r["source"] for r in web_list],
        "timestamp": _ts(),
    })
    return {"web_results": web_list}


async def grade_documents(state: SharedState, *, node_config: dict | None = None) -> dict:
    nid = _nid(node_config)
    model = _cfg(node_config, "model", "gpt-4o-mini")
    writer = get_stream_writer()
    writer({"event": "node_start", "node": nid, "type": "grader", "timestamp": _ts()})

    llm = _llm(model).with_structured_output(GradeDocument)
    prompt = ChatPromptTemplate.from_messages([
        ("system", GRADER_SYSTEM),
        ("human", "Document:\n{document}\n\nQuestion: {question}"),
    ])
    chain = prompt | llm

    graded = []
    passed = 0
    failed = 0

    for doc in state.get("documents", []):
        result = await chain.ainvoke({
            "document": doc["content"],
            "question": state["question"],
        })
        is_relevant = result.relevant == "yes"
        if is_relevant:
            graded.append(doc)
            passed += 1
        else:
            failed += 1

        writer({
            "event": "doc_graded",
            "node": nid,
            "doc_id": doc["source"],
            "relevant": is_relevant,
            "timestamp": _ts(),
        })

    fallback = len(graded) == 0
    writer({
        "event": "grading_summary",
        "node": nid,
        "passed": passed,
        "failed": failed,
        "fallback": fallback,
        "timestamp": _ts(),
    })
    return {"graded_documents": graded, "grader_fallback": fallback}


async def generate_answer(state: SharedState, *, node_config: dict | None = None) -> dict:
    nid = _nid(node_config)
    model = _cfg(node_config, "model", "gpt-4o-mini")
    temperature = _cfg(node_config, "temperature", 0)
    writer = get_stream_writer()
    writer({"event": "node_start", "node": nid, "type": "generator", "timestamp": _ts()})

    retry_count = state.get("retry_count", 0)
    if state.get("generation"):
        retry_count += 1
        writer({
            "event": "retry",
            "node": nid,
            "reason": "regenerating",
            "attempt": retry_count + 1,
            "timestamp": _ts(),
        })

    context_docs = get_best_documents(state)
    context = "\n\n---\n\n".join(
        f"[Source: {d['source']}]\n{d['content']}" for d in context_docs
    )
    sources = list({d["source"] for d in context_docs})

    lang = "繁體中文" if state.get("language", "zh-TW") == "zh-TW" else "English"
    prompt = ChatPromptTemplate.from_messages([
        ("system", GENERATOR_SYSTEM.format(language=lang)),
        ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ])
    chain = prompt | _llm(model, temperature)
    result = await chain.ainvoke({
        "context": context,
        "question": state["question"],
    })

    writer({
        "event": "generation_complete",
        "node": nid,
        "timestamp": _ts(),
    })
    return {
        "generation": result.content,
        "sources": sources,
        "retry_count": retry_count,
    }


async def check_hallucination(state: SharedState, *, node_config: dict | None = None) -> dict:
    nid = _nid(node_config)
    model = _cfg(node_config, "model", "gpt-4o-mini")
    writer = get_stream_writer()
    writer({"event": "node_start", "node": nid, "type": "hallucination_checker", "timestamp": _ts()})

    context_docs = get_best_documents(state)
    documents_text = "\n\n".join(d["content"] for d in context_docs)

    llm = _llm(model).with_structured_output(HallucinationCheck)
    prompt = ChatPromptTemplate.from_messages([
        ("system", HALLUCINATION_SYSTEM),
        ("human", "Documents:\n{documents}\n\nGeneration: {generation}"),
    ])
    chain = prompt | llm
    result = await chain.ainvoke({
        "documents": documents_text,
        "generation": state["generation"],
    })

    grounded = result.grounded == "yes"
    writer({
        "event": "hallucination_check",
        "node": nid,
        "grounded": grounded,
        "timestamp": _ts(),
    })
    return {"hallucination_pass": grounded}


async def check_relevance(state: SharedState, *, node_config: dict | None = None) -> dict:
    nid = _nid(node_config)
    model = _cfg(node_config, "model", "gpt-4o-mini")
    writer = get_stream_writer()
    writer({"event": "node_start", "node": nid, "type": "relevance_checker", "timestamp": _ts()})

    question = state.get("original_question") or state.get("question")

    llm = _llm(model).with_structured_output(RelevanceCheck)
    prompt = ChatPromptTemplate.from_messages([
        ("system", RELEVANCE_SYSTEM),
        ("human", "Question: {question}\n\nGeneration: {generation}"),
    ])
    chain = prompt | llm
    result = await chain.ainvoke({
        "question": question,
        "generation": state["generation"],
    })

    useful = result.useful == "yes"
    writer({
        "event": "relevance_check",
        "node": nid,
        "useful": useful,
        "timestamp": _ts(),
    })
    return {"relevance_pass": useful}


async def build_report(state: SharedState, *, node_config: dict | None = None) -> dict:
    nid = _nid(node_config)
    model = _cfg(node_config, "model", "gpt-4o-mini")
    writer = get_stream_writer()
    writer({"event": "node_start", "node": nid, "type": "report_builder", "timestamp": _ts()})

    lang = "繁體中文" if state.get("language", "zh-TW") == "zh-TW" else "English"
    prompt = ChatPromptTemplate.from_messages([
        ("system", REPORT_SYSTEM.format(language=lang)),
        ("human", "Answer:\n{generation}\n\nSources: {sources}"),
    ])
    chain = prompt | _llm(model)
    result = await chain.ainvoke({
        "generation": state["generation"],
        "sources": "\n".join(state.get("sources", [])),
    })

    writer({
        "event": "research_complete",
        "report": result.content,
        "sources": state.get("sources", []),
        "timestamp": _ts(),
    })
    return {"report": result.content}


# ---------------------------------------------------------------------------
# New nodes: summarizer + query_rewriter
# ---------------------------------------------------------------------------

async def summarize_documents(state: SharedState, *, node_config: dict | None = None) -> dict:
    nid = _nid(node_config)
    model = _cfg(node_config, "model", "gpt-4o-mini")
    max_length = _cfg(node_config, "max_length", 500)
    writer = get_stream_writer()
    writer({"event": "node_start", "node": nid, "type": "summarizer", "timestamp": _ts()})

    docs = state.get("documents") or state.get("web_results") or []
    docs_text = "\n\n---\n\n".join(d["content"] for d in docs)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SUMMARIZER_SYSTEM.format(max_length=max_length)),
        ("human", "{documents}"),
    ])
    chain = prompt | _llm(model)
    result = await chain.ainvoke({"documents": docs_text})

    writer({
        "event": "summary_complete",
        "node": nid,
        "timestamp": _ts(),
    })
    return {"summary": result.content}


async def query_rewrite(state: SharedState, *, node_config: dict | None = None) -> dict:
    nid = _nid(node_config)
    model = _cfg(node_config, "model", "gpt-4o-mini")
    writer = get_stream_writer()
    writer({"event": "node_start", "node": nid, "type": "query_rewriter", "timestamp": _ts()})

    original = state["question"]
    prompt = ChatPromptTemplate.from_messages([
        ("system", QUERY_REWRITER_SYSTEM),
        ("human", "{question}"),
    ])
    chain = prompt | _llm(model)
    result = await chain.ainvoke({"question": original})

    rewritten = result.content.strip()
    writer({
        "event": "query_rewritten",
        "node": nid,
        "original": original,
        "rewritten": rewritten,
        "timestamp": _ts(),
    })

    update: dict = {"question": rewritten}
    # Preserve original question if not already set
    if not state.get("original_question"):
        update["original_question"] = original
    return update
