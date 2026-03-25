"""FastAPI application with SSE streaming for Agentic RAG."""
import asyncio
import time
from collections import defaultdict

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sse_starlette.sse import EventSourceResponse

from app.config import ALLOWED_ORIGINS, get_openai_api_key, get_tavily_api_key
from app.rag.vectorstore import get_vectorstore
from app.streaming.sse import HEARTBEAT_INTERVAL, research_event_generator

app = FastAPI(title="RAG Visualizer API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Track concurrent SSE connections per IP
_active_connections: dict[str, int] = defaultdict(int)
MAX_CONCURRENT_PER_IP = 2


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded. Max 20 requests per minute."},
    )


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/knowledge-bases")
async def knowledge_bases():
    try:
        vs = get_vectorstore()
        count = vs._collection.count()
        return {
            "bases": [
                {
                    "name": "LangChain & LangGraph Docs",
                    "collection": "langchain_docs",
                    "document_count": count,
                }
            ]
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/research")
@limiter.limit("20/minute")
async def research(
    request: Request,
    q: str = Query(..., min_length=1, max_length=500, description="Research question"),
    lang: str = Query("zh-TW", pattern="^(zh-TW|en)$", description="Response language"),
):
    # Check API keys are available
    try:
        get_openai_api_key()
        get_tavily_api_key()
    except RuntimeError as e:
        return JSONResponse(status_code=503, content={"error": str(e)})

    # Check concurrent connection limit
    client_ip = get_remote_address(request)
    if _active_connections[client_ip] >= MAX_CONCURRENT_PER_IP:
        return JSONResponse(
            status_code=429,
            content={"error": f"Max {MAX_CONCURRENT_PER_IP} concurrent connections per IP."},
        )

    async def event_stream():
        _active_connections[client_ip] += 1
        last_data_time = time.time()
        try:
            # Interleave heartbeats with research events
            research_gen = research_event_generator(q, lang)
            heartbeat_due = asyncio.get_event_loop().time() + HEARTBEAT_INTERVAL

            async for event_data in research_gen:
                yield event_data
                last_data_time = time.time()

                # Reset heartbeat timer after each real event
                heartbeat_due = asyncio.get_event_loop().time() + HEARTBEAT_INTERVAL

        finally:
            _active_connections[client_ip] -= 1
            if _active_connections[client_ip] <= 0:
                del _active_connections[client_ip]

    return EventSourceResponse(
        event_stream(),
        media_type="text/event-stream",
    )
