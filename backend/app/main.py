"""FastAPI application with SSE streaming for Agentic RAG."""
import asyncio
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Query, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sse_starlette.sse import EventSourceResponse

from app.config import (
    ALLOWED_ORIGINS,
    CHROMA_PERSIST_DIR,
    MAX_FILES_PER_SESSION,
    MAX_UPLOAD_SIZE_MB,
    get_openai_api_key,
    get_tavily_api_key,
)
from app.graph.templates import get_template, list_templates
from app.graph.validator import validate_graph
from app.rag.vectorstore import get_vectorstore
from app.session.cleanup import cleanup_expired_sessions
from app.session.manager import get_session_manager
from app.streaming.sse import (
    HEARTBEAT_INTERVAL,
    graph_run_event_generator,
    research_event_generator,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background cleanup task
    task = asyncio.create_task(cleanup_expired_sessions())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="RAG Pipeline Studio API", lifespan=lifespan)

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


# ---------------------------------------------------------------------------
# Health & info
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

@app.post("/api/session")
async def create_session():
    mgr = get_session_manager()
    session = mgr.create_session()
    return {"session_id": session.id, "collection_name": session.collection_name}


@app.post("/api/session/{session_id}/upload")
async def upload_file(session_id: str, file: UploadFile = File(...)):
    mgr = get_session_manager()
    session = mgr.get_session(session_id)
    if not session:
        return JSONResponse(status_code=404, content={"error": "Session not found"})

    # Check file count limit
    if len(session.files) >= MAX_FILES_PER_SESSION:
        return JSONResponse(status_code=400, content={
            "error": f"Max {MAX_FILES_PER_SESSION} files per session"
        })

    # Check file size
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_SIZE_MB:
        return JSONResponse(status_code=400, content={
            "error": f"File too large ({size_mb:.1f}MB). Max {MAX_UPLOAD_SIZE_MB}MB"
        })

    # Save file
    upload_dir = Path(CHROMA_PERSIST_DIR) / "uploads" / session_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex[:8]
    file_ext = Path(file.filename or "file.txt").suffix
    file_path = upload_dir / f"{file_id}{file_ext}"
    file_path.write_bytes(contents)

    # Ingest into Chroma
    try:
        from app.rag.ingestion import ingest_file
        chunk_count = ingest_file(str(file_path), session.collection_name)
    except Exception as e:
        file_path.unlink(missing_ok=True)
        return JSONResponse(status_code=400, content={"error": str(e)})

    # Record file in session
    file_info = {
        "id": file_id,
        "name": file.filename,
        "size": len(contents),
        "chunks": chunk_count,
    }
    mgr.add_file(session_id, file_info)

    return {"file": file_info, "collection_name": session.collection_name}


@app.get("/api/session/{session_id}/files")
async def list_session_files(session_id: str):
    mgr = get_session_manager()
    session = mgr.get_session(session_id)
    if not session:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    return {"files": session.files, "collection_name": session.collection_name}


@app.delete("/api/session/{session_id}/files/{file_id}")
async def delete_session_file(session_id: str, file_id: str):
    mgr = get_session_manager()
    session = mgr.get_session(session_id)
    if not session:
        return JSONResponse(status_code=404, content={"error": "Session not found"})

    mgr.remove_file(session_id, file_id)

    # Delete file from disk
    upload_dir = Path(CHROMA_PERSIST_DIR) / "uploads" / session_id
    for f in upload_dir.glob(f"{file_id}*"):
        f.unlink(missing_ok=True)

    return {"ok": True}


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

@app.get("/api/templates")
async def templates_list():
    return {"templates": list_templates()}


@app.get("/api/templates/{template_id}")
async def template_detail(template_id: str):
    t = get_template(template_id)
    if t is None:
        return JSONResponse(status_code=404, content={"error": f"Template '{template_id}' not found."})
    return t


# ---------------------------------------------------------------------------
# Graph validation & execution
# ---------------------------------------------------------------------------

class GraphValidateRequest(BaseModel):
    nodes: dict
    edges: list = Field(default_factory=list)
    conditional_edges: list = Field(default_factory=list)


class GraphRunRequest(BaseModel):
    config: dict
    question: str = Field(..., min_length=1, max_length=500)
    language: str = Field(default="zh-TW", pattern="^(zh-TW|en)$")


@app.post("/api/graph/validate")
async def graph_validate(body: GraphValidateRequest):
    config = {"nodes": body.nodes, "edges": body.edges, "conditional_edges": body.conditional_edges}
    errors = validate_graph(config)
    return {"valid": len(errors) == 0, "errors": errors}


@app.post("/api/graph/run")
@limiter.limit("20/minute")
async def graph_run(request: Request, body: GraphRunRequest):
    # Check API keys
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

    config = body.config
    question = body.question
    language = body.language

    async def event_stream():
        _active_connections[client_ip] += 1
        try:
            async for event_data in graph_run_event_generator(config, question, language):
                yield event_data
        finally:
            _active_connections[client_ip] -= 1
            if _active_connections[client_ip] <= 0:
                del _active_connections[client_ip]

    return EventSourceResponse(
        event_stream(),
        media_type="text/event-stream",
    )


# ---------------------------------------------------------------------------
# Legacy SSE endpoint (backward compatibility)
# ---------------------------------------------------------------------------

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
