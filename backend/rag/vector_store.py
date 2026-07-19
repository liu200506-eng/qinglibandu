from typing import List, Optional, Tuple, Dict
from qdrant_client import QdrantClient, models
from qdrant_client.models import VectorParams, Distance, PointStruct, Filter
from .config import settings
import uuid
import requests
import json


class QdrantVectorStore:
    def __init__(self):
        # 支持两种模式：本地嵌入式（无需Docker）和服务器模式（需独立Qdrant服务）
        if settings.qdrant_mode == "local":
            # 本地嵌入式模式，数据存储在本地文件
            self.client = QdrantClient(path=settings.qdrant_local_path)
            print(f"[Qdrant] 使用本地嵌入式模式，存储路径: {settings.qdrant_local_path}")
        else:
            # 服务器模式，连接独立的Qdrant服务（如Docker启动的）
            self.client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                check_compatibility=False,
            )
            print(f"[Qdrant] 连接服务器模式: {settings.qdrant_host}:{settings.qdrant_port}")
        self.collection_name = settings.qdrant_collection
        self._ensure_collection()

    def _ensure_collection(self):
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=768,
                    distance=Distance.COSINE,
                ),
            )

    def upsert_points(self, vectors: List[List[float]], metadatas: List[Dict]) -> int:
        points = []
        for i, (vector, metadata) in enumerate(zip(vectors, metadatas)):
            point_id = str(uuid.uuid4())
            points.append(PointStruct(
                id=point_id,
                vector=vector,
                payload=metadata,
            ))
        
        if hasattr(self.client, 'upload_points'):
            result = self.client.upload_points(
                collection_name=self.collection_name,
                points=points,
            )
        else:
            result = self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
        
        if hasattr(result, 'upserted_count'):
            return result.upserted_count
        elif hasattr(result, 'count'):
            return result.count
        else:
            return len(points)

    def search(self, query_vector: List[float], top_k: int = 10, filters: Optional[dict] = None) -> List[dict]:
        qdrant_filter = None
        
        if filters:
            must_conditions = []
            for key, value in filters.items():
                if isinstance(value, str):
                    must_conditions.append(
                        models.FieldCondition(key=key, match=models.MatchValue(value=value))
                    )
                elif isinstance(value, list):
                    must_conditions.append(
                        models.FieldCondition(key=key, match=models.MatchAny(any=value))
                    )
            if must_conditions:
                qdrant_filter = models.Filter(must=must_conditions)
        
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
                query_filter=qdrant_filter,
            )
            
            return [
                {
                    "score": result.score,
                    "text": result.payload.get("text", ""),
                    "metadata": result.payload,
                }
                for result in results
            ]
        except Exception as e:
            print(f"[Qdrant] 搜索失败: {e}")
            return []

    def delete_points_by_file_hash(self, file_hash: str) -> int:
        try:
            result = self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="file_hash",
                                match=models.MatchValue(value=file_hash),
                            ),
                        ]
                    )
                ),
            )
            if hasattr(result, 'deleted_count'):
                return result.deleted_count
            elif hasattr(result, 'count'):
                return result.count
            else:
                return 0
        except Exception as e:
            print(f"[Qdrant] 删除失败: {e}")
            return 0

    def get_collection_stats(self) -> dict:
        stats = self.client.get_collection(collection_name=self.collection_name)
        return {
            "total_points": stats.points_count,
            "vectors_count": getattr(stats, "vectors_count", stats.points_count),
            "config": stats.config,
        }

    def count_by_filter(self, filters: Dict) -> int:
        conditions = [
            models.FieldCondition(key=key, match=models.MatchValue(value=value))
            for key, value in filters.items()
        ]
        result = self.client.count(
            collection_name=self.collection_name,
            count_filter=models.Filter(must=conditions),
            exact=True,
        )
        return int(result.count)

    def clear_collection(self):
        self.client.delete_collection(collection_name=self.collection_name)
        self._ensure_collection()
