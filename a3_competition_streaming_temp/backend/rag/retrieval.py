from typing import List, Dict, Optional, Tuple
from rank_bm25 import BM25Okapi
import jieba
from .vector_store import QdrantVectorStore
from .embedding_model import EmbeddingModel, RerankerModel
from .config import settings


class DualRetrieval:
    def __init__(self):
        self.vector_store = QdrantVectorStore()
        self.embedding_model = EmbeddingModel.get_instance()
        self.reranker_model = RerankerModel.get_instance()
        self.bm25_index = None
        self.bm25_corpus = []
        self.bm25_metadatas = []
        self._build_bm25_index()

    def _build_bm25_index(self):
        stats = self.vector_store.get_collection_stats()
        if stats["total_points"] > 0:
            all_points = self.vector_store.client.scroll(
                collection_name=self.vector_store.collection_name,
                limit=stats["total_points"],
                with_payload=True,
            )[0]
            self.bm25_corpus = [point.payload.get("text", "") for point in all_points]
            self.bm25_metadatas = [point.payload or {} for point in all_points]
            tokenized_corpus = [list(jieba.cut(text)) for text in self.bm25_corpus]
            self.bm25_index = BM25Okapi(tokenized_corpus)

    def bm25_search(self, query: str, top_k: int = 10, filters: Optional[dict] = None) -> List[Dict]:
        if not self.bm25_index or not self.bm25_corpus:
            return []
        
        tokenized_query = list(jieba.cut(query))
        scores = self.bm25_index.get_scores(tokenized_query)
        
        results = []
        for idx in scores.argsort()[::-1]:
            metadata = self.bm25_metadatas[idx] if idx < len(self.bm25_metadatas) else {}
            if filters and any(metadata.get(key) != value for key, value in filters.items()):
                continue
            results.append({
                "score": float(scores[idx]),
                "text": self.bm25_corpus[idx],
                "type": "bm25",
                "metadata": metadata,
            })
            if len(results) >= top_k:
                break
        return results

    def vector_search(self, query: str, top_k: int = 10, filters: Optional[dict] = None) -> List[Dict]:
        query_vector = self.embedding_model.encode_single(query)
        return self.vector_store.search(query_vector, top_k=top_k, filters=filters)

    def dual_search(self, query: str, top_k: int = 10, filters: Optional[dict] = None) -> List[Dict]:
        bm25_results = self.bm25_search(query, top_k=settings.bm25_top_k, filters=filters)
        vector_results = self.vector_search(query, top_k=settings.vector_top_k, filters=filters)

        combined = {}
        for result in bm25_results:
            text = result["text"]
            if text not in combined:
                combined[text] = {"text": text, "bm25_score": 0, "vector_score": 0, "sources": [], "metadata": result.get("metadata", {})}
            combined[text]["bm25_score"] = result["score"]
            combined[text]["sources"].append("bm25")

        for result in vector_results:
            text = result["text"]
            if text not in combined:
                combined[text] = {"text": text, "bm25_score": 0, "vector_score": 0, "sources": [], "metadata": result.get("metadata", {})}
            if not combined[text].get("metadata"):
                combined[text]["metadata"] = result.get("metadata", {})
            combined[text]["vector_score"] = result["score"]
            combined[text]["sources"].append("vector")

        return list(combined.values())[:top_k]

    def rerank(self, query: str, documents: List[str]) -> List[Tuple[str, float]]:
        scores = self.reranker_model.predict(query, documents)
        sorted_pairs = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        return sorted_pairs

    def retrieve(self, query: str, top_k: int = 5, filters: Optional[dict] = None) -> List[Dict]:
        dual_results = self.dual_search(query, top_k=settings.bm25_top_k + settings.vector_top_k, filters=filters)
        
        if not dual_results:
            return []
        
        documents = [result["text"] for result in dual_results]
        reranked = self.rerank(query, documents)

        final_results = []
        for text, score in reranked[:top_k]:
            matched = next((r for r in dual_results if r["text"] == text), None)
            if matched:
                final_results.append({
                    "text": text,
                    "rerank_score": float(score),
                    "bm25_score": matched.get("bm25_score", 0),
                    "vector_score": matched.get("vector_score", 0),
                    "sources": matched.get("sources", []),
                    "source_file": matched.get("metadata", {}).get("source_file", ""),
                    "subject_name": matched.get("metadata", {}).get("subject_name", ""),
                    "node_name": matched.get("metadata", {}).get("node_name", ""),
                })
        
        return final_results
