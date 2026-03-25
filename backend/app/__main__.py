"""CLI runner for testing the RAG graph end-to-end."""
import asyncio
import json
import sys

from app.graph.builder import build_graph


async def run(question: str, lang: str = "zh-TW"):
    graph = build_graph()
    inputs = {
        "question": question,
        "language": lang,
        "retry_count": 0,
        "documents": [],
        "graded_documents": [],
        "web_results": [],
        "sources": [],
    }

    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print(f"Language: {lang}")
    print(f"{'='*60}\n")

    async for mode, chunk in graph.astream(inputs, stream_mode=["updates", "custom"]):
        if mode == "custom":
            event = chunk.get("event", "")
            print(f"[STREAM] {json.dumps(chunk, ensure_ascii=False)}")
        elif mode == "updates":
            for node_name, updates in chunk.items():
                keys = list(updates.keys()) if isinstance(updates, dict) else []
                print(f"[UPDATE] {node_name}: {keys}")

    print(f"\n{'='*60}")
    print("Done!")


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "什麼是 LCEL？"
    asyncio.run(run(question))
