from pydantic_settings import BaseSettings
import os


class RAGSettings(BaseSettings):
    # Qdrant 配置
    # 模式选择："local"=本地嵌入式（无需Docker），"server"=连接独立Qdrant服务
    qdrant_mode: str = "server"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "qingli_docs"
    # 本地嵌入式模式的存储路径
    qdrant_local_path: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "qdrant_storage")
    
    embedding_model: str = "BAAI/bge-base-zh"
    reranker_model: str = "BAAI/bge-reranker-base"
    
    chunk_size: int = 1024
    chunk_overlap: int = 128
    
    bm25_top_k: int = 10
    vector_top_k: int = 10
    rerank_top_k: int = 5
    
    enable_ocr: bool = True
    enable_pdf: bool = True
    enable_word: bool = True
    
    model_config = {"extra": "ignore", "env_file": ".env"}


settings = RAGSettings()

# 确保本地存储目录存在
if settings.qdrant_mode == "local":
    os.makedirs(settings.qdrant_local_path, exist_ok=True)
