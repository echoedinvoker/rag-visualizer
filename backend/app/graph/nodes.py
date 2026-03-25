"""All node functions for the Agentic RAG graph."""
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
    RELEVANCE_SYSTEM,
    REPORT_SYSTEM,
    ROUTER_SYSTEM,
)
from app.graph.state import ResearchState
from app.rag.vectorstore import get_retriever
from app.tools.web_search import get_web_search_tool


def _llm() -> ChatOpenAI:
    return ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=get_openai_api_key())


def _ts() -> int:
    return int(time.time())


# --- Structured output schemas ---


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


# --- Node functions (all async for get_stream_writer compatibility) ---


async def route_question(state: ResearchState) -> dict:
    writer = get_stream_writer()
    writer({"event": "node_start", "node": "router", "timestamp": _ts()})

    llm = _llm().with_structured_output(RouteQuery)
    prompt = ChatPromptTemplate.from_messages([
        ("system", ROUTER_SYSTEM),
        ("human", "{question}"),
    ])
    chain = prompt | llm
    result = await chain.ainvoke({"question": state["question"]})

    writer({
        "event": "route_decision",
        "node": "router",
        "decision": result.route,
        "timestamp": _ts(),
    })
    return {"route": result.route}


async def retrieve_documents(state: ResearchState) -> dict:
    writer = get_stream_writer()
    writer({"event": "node_start", "node": "retriever", "timestamp": _ts()})

    retriever = get_retriever()
    docs = await retriever.ainvoke(state["question"])
    doc_list = [
        {"content": doc.page_content, "source": doc.metadata.get("source", "unknown")}
        for doc in docs
    ]

    writer({
        "event": "documents_retrieved",
        "node": "retriever",
        "count": len(doc_list),
        "sources": [d["source"] for d in doc_list],
        "timestamp": _ts(),
    })
    return {"documents": doc_list}


async def web_search(state: ResearchState) -> dict:
    writer = get_stream_writer()
    writer({"event": "node_start", "node": "web_search", "timestamp": _ts()})

    tool = get_web_search_tool()
    raw = await tool.ainvoke(state["question"])
    # TavilySearch returns {"results": [...]} dict
    results = raw.get("results", []) if isinstance(raw, dict) else raw
    web_list = [
        {"content": r.get("content", ""), "source": r.get("url", "")}
        for r in results
    ]

    writer({
        "event": "web_search_complete",
        "node": "web_search",
        "count": len(web_list),
        "sources": [r["source"] for r in web_list],
        "timestamp": _ts(),
    })
    return {"web_results": web_list}


async def grade_documents(state: ResearchState) -> dict:
    writer = get_stream_writer()
    writer({"event": "node_start", "node": "grader", "timestamp": _ts()})

    llm = _llm().with_structured_output(GradeDocument)
    prompt = ChatPromptTemplate.from_messages([
        ("system", GRADER_SYSTEM),
        ("human", "Document:\n{document}\n\nQuestion: {question}"),
    ])
    chain = prompt | llm

    graded = []
    passed = 0
    failed = 0

    for doc in state["documents"]:
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
            "node": "grader",
            "doc_id": doc["source"],
            "relevant": is_relevant,
            "timestamp": _ts(),
        })

    writer({
        "event": "grading_complete",
        "node": "grader",
        "passed": passed,
        "failed": failed,
        "fallback": len(graded) == 0,
        "timestamp": _ts(),
    })
    return {"graded_documents": graded}


async def generate_answer(state: ResearchState) -> dict:
    writer = get_stream_writer()
    writer({"event": "node_start", "node": "generator", "timestamp": _ts()})

    # Increment retry_count on re-entry (first call keeps it at 0)
    retry_count = state.get("retry_count", 0)
    if state.get("generation"):
        retry_count += 1
        writer({
            "event": "retry",
            "node": "generator",
            "reason": "regenerating",
            "attempt": retry_count + 1,
            "timestamp": _ts(),
        })

    # Merge graded_documents + web_results as context
    context_docs = state.get("graded_documents", []) + state.get("web_results", [])
    context = "\n\n---\n\n".join(
        f"[Source: {d['source']}]\n{d['content']}" for d in context_docs
    )
    sources = list({d["source"] for d in context_docs})

    lang = "繁體中文" if state.get("language", "zh-TW") == "zh-TW" else "English"
    prompt = ChatPromptTemplate.from_messages([
        ("system", GENERATOR_SYSTEM.format(language=lang)),
        ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ])
    chain = prompt | _llm()
    result = await chain.ainvoke({
        "context": context,
        "question": state["question"],
    })

    writer({
        "event": "generation_complete",
        "node": "generator",
        "timestamp": _ts(),
    })
    return {
        "generation": result.content,
        "sources": sources,
        "retry_count": retry_count,
    }


async def check_hallucination(state: ResearchState) -> dict:
    writer = get_stream_writer()
    writer({"event": "node_start", "node": "hallucination_checker", "timestamp": _ts()})

    context_docs = state.get("graded_documents", []) + state.get("web_results", [])
    documents_text = "\n\n".join(d["content"] for d in context_docs)

    llm = _llm().with_structured_output(HallucinationCheck)
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
        "node": "hallucination_checker",
        "grounded": grounded,
        "timestamp": _ts(),
    })
    return {"hallucination_pass": grounded}


async def check_relevance(state: ResearchState) -> dict:
    writer = get_stream_writer()
    writer({"event": "node_start", "node": "relevance_checker", "timestamp": _ts()})

    llm = _llm().with_structured_output(RelevanceCheck)
    prompt = ChatPromptTemplate.from_messages([
        ("system", RELEVANCE_SYSTEM),
        ("human", "Question: {question}\n\nGeneration: {generation}"),
    ])
    chain = prompt | llm
    result = await chain.ainvoke({
        "question": state["question"],
        "generation": state["generation"],
    })

    useful = result.useful == "yes"
    writer({
        "event": "relevance_check",
        "node": "relevance_checker",
        "useful": useful,
        "timestamp": _ts(),
    })
    return {"relevance_pass": useful}


async def build_report(state: ResearchState) -> dict:
    writer = get_stream_writer()
    writer({"event": "node_start", "node": "report_builder", "timestamp": _ts()})

    lang = "繁體中文" if state.get("language", "zh-TW") == "zh-TW" else "English"
    prompt = ChatPromptTemplate.from_messages([
        ("system", REPORT_SYSTEM.format(language=lang)),
        ("human", "Answer:\n{generation}\n\nSources: {sources}"),
    ])
    chain = prompt | _llm()
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
