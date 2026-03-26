"""SSE response formatting and graph streaming."""
import json
import time

from app.graph.builder import build_graph, build_graph_from_config


HEARTBEAT_INTERVAL = 15  # seconds
TIMEOUT = 90  # seconds


def _initial_state(question: str, language: str) -> dict:
    """Common initial state for all graph executions."""
    return {
        "question": question,
        "original_question": question,
        "language": language,
        "retry_count": 0,
        "documents": [],
        "graded_documents": [],
        "web_results": [],
        "sources": [],
        "hallucination_pass": False,
        "relevance_pass": False,
        "grader_fallback": False,
    }


async def research_event_generator(question: str, language: str = "zh-TW"):
    """Async generator for the legacy /api/research endpoint."""
    graph = build_graph()
    inputs = _initial_state(question, language)

    start_time = time.time()

    try:
        async for mode, chunk in graph.astream(inputs, stream_mode=["updates", "custom"]):
            if time.time() - start_time > TIMEOUT:
                yield {"data": json.dumps({"event": "timeout", "message": "Research timed out"}, ensure_ascii=False)}
                return

            if mode == "custom":
                yield {"data": json.dumps(chunk, ensure_ascii=False)}

    except Exception as e:
        yield {"data": json.dumps({
            "event": "error",
            "message": str(e),
            "timestamp": int(time.time()),
        }, ensure_ascii=False)}


async def graph_run_event_generator(config: dict, question: str, language: str = "zh-TW"):
    """Async generator for the new /api/graph/run endpoint.

    Builds a graph from a user-supplied config and streams execution events.
    """
    try:
        graph = build_graph_from_config(config)
    except ValueError as e:
        yield {"data": json.dumps({
            "event": "graph_error",
            "message": str(e),
            "timestamp": int(time.time()),
        }, ensure_ascii=False)}
        return

    inputs = _initial_state(question, language)

    # Emit graph_start
    node_count = len(config.get("nodes", {}))
    yield {"data": json.dumps({
        "event": "graph_start",
        "node_count": node_count,
        "timestamp": int(time.time()),
    }, ensure_ascii=False)}

    start_time = time.time()

    try:
        async for mode, chunk in graph.astream(inputs, stream_mode=["updates", "custom"]):
            if time.time() - start_time > TIMEOUT:
                yield {"data": json.dumps({"event": "timeout", "message": "Research timed out"}, ensure_ascii=False)}
                return

            if mode == "custom":
                yield {"data": json.dumps(chunk, ensure_ascii=False)}

        # Emit graph_complete
        yield {"data": json.dumps({
            "event": "graph_complete",
            "total_duration_ms": int((time.time() - start_time) * 1000),
            "timestamp": int(time.time()),
        }, ensure_ascii=False)}

    except Exception as e:
        yield {"data": json.dumps({
            "event": "graph_error",
            "node": getattr(e, "node", None),
            "message": str(e),
            "timestamp": int(time.time()),
        }, ensure_ascii=False)}
