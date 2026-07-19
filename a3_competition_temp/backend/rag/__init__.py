from .config import settings, RAGSettings
from .document_parser import DocumentParserFactory, split_text, calculate_file_hash
from .vector_store import QdrantVectorStore

# 延迟导入 embedding_model，避免 torch DLL 问题导致整体启动失败
try:
    from .embedding_model import EmbeddingModel, RerankerModel, init_models
    from .retrieval import DualRetrieval
    from .engine import RAGEngine
    _rag_full_available = True
except Exception as e:
    print(f"[RAG] 部分模块加载失败（embedding/rerank不可用）: {e}")
    _rag_full_available = False
    EmbeddingModel = None
    RerankerModel = None
    init_models = None
    DualRetrieval = None
    RAGEngine = None

__all__ = [
    "settings",
    "RAGSettings",
    "DocumentParserFactory",
    "split_text",
    "calculate_file_hash",
    "QdrantVectorStore",
    "EmbeddingModel",
    "RerankerModel",
    "init_models",
    "DualRetrieval",
    "RAGEngine",
]
