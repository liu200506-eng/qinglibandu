from typing import List
import os

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from sentence_transformers import SentenceTransformer, CrossEncoder
from .config import settings
import threading
import time


class EmbeddingModel:
    _instance = None
    _lock = threading.Lock()
    _model = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        if self._model is None:
            self._model = SentenceTransformer(settings.embedding_model)

    def encode(self, texts: List[str]) -> List[List[float]]:
        return self._model.encode(texts).tolist()

    def encode_single(self, text: str) -> List[float]:
        return self._model.encode(text).tolist()


class RerankerModel:
    _instance = None
    _lock = threading.Lock()
    _model = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        if self._model is None:
            self._model = CrossEncoder(settings.reranker_model)

    def predict(self, query: str, documents: List[str]) -> List[float]:
        pairs = [[query, doc] for doc in documents]
        scores = self._model.predict(pairs)
        return scores.tolist()


def init_models():
    start_time = time.time()
    print(f"正在加载Embedding模型: {settings.embedding_model}")
    EmbeddingModel.get_instance()
    print(f"Embedding模型加载完成，耗时: {time.time() - start_time:.2f}s")
    
    start_time = time.time()
    print(f"正在加载Reranker模型: {settings.reranker_model}")
    RerankerModel.get_instance()
    print(f"Reranker模型加载完成，耗时: {time.time() - start_time:.2f}s")


def get_embedding_function():
    """获取embedding函数（用于Qdrant同步服务）"""
    def embed(text):
        return EmbeddingModel.get_instance().encode_single(text)
    return embed


def get_reranker():
    """获取reranker实例"""
    return RerankerModel.get_instance()
