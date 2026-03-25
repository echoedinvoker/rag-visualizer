# RAG Visualizer

**Real-time visualization of Agentic RAG decision flows** — watch AI think through routing, retrieval, grading, hallucination detection, and report generation.

> [Live Demo](https://rag-visualizer-cty.pages.dev)

## What it does

Enter any research topic and watch the AI pipeline work in real-time:

1. **Router** — decides whether to search the knowledge base or the web
2. **Retriever** — fetches relevant documents from a vector store
3. **Grader** — scores each document for relevance, falls back to web search if all fail
4. **Generator** — produces an answer citing sources
5. **Hallucination Check** — verifies the answer is grounded in documents
6. **Relevance Check** — verifies the answer addresses the question
7. **Report Builder** — formats the final research report

Failed checks trigger automatic retries with supplementary search — all visible in real-time on the flow graph.

## Architecture

```
┌─────────────────────┐     SSE      ┌──────────────────────┐
│   Nuxt 4 (SPA)      │◄────────────►│   FastAPI + SSE      │
│   Vue Flow graph     │              │   LangGraph pipeline │
│   Ant Design Vue     │              │   Chroma vector DB   │
│   i18n (zh-TW/en)   │              │   Tavily web search  │
│                      │              │   OpenAI gpt-4o-mini │
│   Cloudflare Pages   │              │   Fly.io (Tokyo)     │
└─────────────────────┘              └──────────────────────┘
```

### Three-layer Agentic RAG

| Layer | Technique | Purpose |
|-------|-----------|---------|
| 1 | Adaptive RAG | Route questions to vector store or web search |
| 2 | Corrective RAG (CRAG) | Grade retrieved documents, fallback on low quality |
| 3 | Self-RAG | Check for hallucinations and answer relevance |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Nuxt 4, Vue 3, Vue Flow, Ant Design Vue 4, @nuxtjs/i18n |
| Backend | FastAPI, LangGraph, LangChain, Chroma, Tavily |
| LLM | OpenAI gpt-4o-mini |
| Deploy | Cloudflare Pages (frontend), Fly.io (backend) |

## Quick Start

### Backend

```bash
cd backend
cp .env.example .env  # Add your OPENAI_API_KEY and TAVILY_API_KEY
uv sync
uv run python scripts/ingest_docs.py  # Ingest LangChain/LangGraph docs
uv run uvicorn app.main:app --port 8000
```

### Frontend

```bash
cd frontend
bun install
NUXT_PUBLIC_API_BASE=http://localhost:8000 bun dev
```

Open http://localhost:3000 and start researching.

## Pre-loaded Knowledge Base

The vector store is pre-loaded with 7 official LangChain/LangGraph documentation files (446 chunks):

- Graph API (nodes, edges, state, conditional edges)
- Workflows & Agents patterns
- Thinking in LangGraph (architecture guide)
- Agentic RAG tutorial
- Streaming modes
- RAG pipeline
- Agent fundamentals

Questions within these topics route to the vector store; everything else routes to web search via Tavily.

## Features

- Real-time flow graph with animated nodes and edges
- Side-by-side graph + execution log layout
- Automatic retry visualization (hallucination/relevance failures)
- Markdown research report with cited sources
- Bilingual UI (繁體中文 / English) with browser language detection
- Rate limiting (20 req/min) and concurrent connection limits
- Mobile responsive

## License

MIT
