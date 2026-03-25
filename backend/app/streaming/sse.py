"""SSE response formatting and graph streaming."""
import json
import time

from app.graph.builder import build_graph


HEARTBEAT_INTERVAL = 15  # seconds
TIMEOUT = 90  # seconds


async def research_event_generator(question: str, language: str = "zh-TW"):
    """Async generator that yields dicts for EventSourceResponse."""
    graph = build_graph()
    inputs = {
        "question": question,
        "language": language,
        "retry_count": 0,
        "documents": [],
        "graded_documents": [],
        "web_results": [],
        "sources": [],
    }

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
