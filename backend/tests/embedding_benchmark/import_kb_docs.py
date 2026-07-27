"""把 knowledge_base/computer_network/documents/ 下的所有 markdown 文档
导入到 Qdrant 的 qingli_docs collection，用于 Embedding 评测。

用法:
    cd backend
    python -m tests.embedding_benchmark.import_kb_docs
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from rag.engine import RAGEngine
from rag.config import settings
from qdrant_client import QdrantClient

KNOWLEDGE_BASE = Path(__file__).resolve().parents[2] / "knowledge_base"
COURSE_DOCS = KNOWLEDGE_BASE / "computer_network" / "documents"
COLLECTION = settings.qdrant_collection


def main():
    print(f"Collection: {COLLECTION}")
    print(f"Source dir: {COURSE_DOCS}")

    # 1. 清空现有 collection
    client = QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        check_compatibility=False,
    )
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION in collections:
        print(f"Deleting existing '{COLLECTION}'...")
        client.delete_collection(COLLECTION)
        print("  Deleted.")

    # 2. 读取所有 markdown 文件
    md_files = sorted(COURSE_DOCS.glob("*.md"))
    print(f"Found {len(md_files)} markdown documents")

    # 3. 逐个导入
    engine = RAGEngine()
    total_chunks = 0
    for i, md_file in enumerate(md_files, 1):
        print(f"[{i}/{len(md_files)}] Ingesting {md_file.name}...", end=" ", flush=True)
        result = engine.ingest_document(str(md_file))
        if result.get("success"):
            chunks = result.get("chunks_count", 0)
            total_chunks += chunks
            print(f"OK ({chunks} chunks)")
        else:
            print(f"FAILED: {result.get('message', 'unknown')}")

    # 4. 验证
    stats = client.get_collection(COLLECTION)
    print(f"\nDone! Total: {total_chunks} chunks in '{COLLECTION}'")
    print(f"Qdrant reports: {stats.points_count or 0} points")

    if stats.points_count:
        sample, _ = client.scroll(COLLECTION, limit=3, with_payload=True)
        for p in sample:
            sf = (p.payload or {}).get("source_file", "?")
            txt = (p.payload or {}).get("text", "")[:80]
            print(f"  [{p.id}] file={sf} text={txt}...")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())