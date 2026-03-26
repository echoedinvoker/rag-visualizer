FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY app/ app/
COPY scripts/ scripts/

# Ensure data directories are writable
RUN mkdir -p /data/uploads && chmod -R 777 /data

# Default env vars for session management
ENV CHROMA_PERSIST_DIR=/data/chroma_db
ENV SESSION_TTL_HOURS=24
ENV MAX_UPLOAD_SIZE_MB=10
ENV MAX_FILES_PER_SESSION=5

# Expose port
EXPOSE 8080

# Entrypoint: run ingest (idempotent) then start server
CMD ["sh", "-c", "uv run python scripts/ingest_docs.py && uv run uvicorn app.main:app --host 0.0.0.0 --port 8080"]
