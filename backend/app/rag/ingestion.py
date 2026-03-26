"""Ingest user-uploaded files into a session-specific Chroma collection."""
from __future__ import annotations

from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.vectorstore import get_vectorstore

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


def ingest_file(file_path: str, collection_name: str) -> int:
    """Ingest a single file into a Chroma collection.

    Returns the number of chunks ingested.
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}. Supported: {SUPPORTED_EXTENSIONS}")

    # Read content
    if ext == ".pdf":
        content = _read_pdf(path)
    else:
        content = path.read_text(encoding="utf-8", errors="replace")

    if not content.strip():
        return 0

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_text(content)

    # Ingest into collection
    vectorstore = get_vectorstore(collection_name)
    texts = chunks
    metadatas = [{"source": path.name}] * len(chunks)
    vectorstore.add_texts(texts=texts, metadatas=metadatas)

    return len(chunks)


def _read_pdf(path: Path) -> str:
    """Extract text from a PDF file."""
    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        raise RuntimeError("pypdf is required for PDF uploads. Install with: pip install pypdf")
