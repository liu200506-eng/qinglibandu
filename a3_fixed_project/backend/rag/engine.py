from typing import List, Dict
from .document_parser import DocumentParserFactory, calculate_file_hash, split_text, build_chunk_metadata
from .vector_store import QdrantVectorStore
from .embedding_model import EmbeddingModel, init_models
from .retrieval import DualRetrieval
from .config import settings
import os


class RAGEngine:
    def __init__(self):
        self.vector_store = QdrantVectorStore()
        self.embedding_model = EmbeddingModel.get_instance()
        self.retrieval = DualRetrieval()

    def ingest_document(self, file_path: str) -> Dict:
        file_hash = calculate_file_hash(file_path)
        source_file = os.path.basename(file_path)
        
        text = DocumentParserFactory.parse(file_path)
        if not text:
            return {"success": False, "message": "文档解析失败"}
        
        chunks = split_text(text, chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
        
        metadatas = []
        for i, chunk in enumerate(chunks):
            metadata = build_chunk_metadata(
                chunk_text=chunk,
                chunk_index=i,
                total_chunks=len(chunks),
                source_file=source_file,
                file_hash=file_hash,
            )
            metadata["text"] = chunk
            metadatas.append(metadata)
        
        vectors = self.embedding_model.encode(chunks)
        
        self.vector_store.delete_points_by_file_hash(file_hash)
        upserted_count = self.vector_store.upsert_points(vectors, metadatas)
        
        self.retrieval._build_bm25_index()
        
        return {
            "success": True,
            "file_hash": file_hash,
            "source_file": source_file,
            "chunks_count": len(chunks),
            "upserted_count": upserted_count,
        }

    def ingest_documents(self, file_paths: List[str]) -> List[Dict]:
        results = []
        for file_path in file_paths:
            result = self.ingest_document(file_path)
            results.append(result)
        return results

    def ingest_text(self, text: str, source_name: str, metadata: Dict = None) -> Dict:
        if not text or len(text.strip()) < 10:
            return {"success": False, "message": "文本内容太短"}
        
        chunks = split_text(text, chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
        
        metadatas = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = build_chunk_metadata(
                chunk_text=chunk,
                chunk_index=i,
                total_chunks=len(chunks),
                source_file=source_name,
                file_hash=f"text_{source_name}_{i}",
            )
            chunk_metadata["text"] = chunk
            if metadata:
                chunk_metadata.update(metadata)
            metadatas.append(chunk_metadata)
        
        vectors = self.embedding_model.encode(chunks)
        upserted_count = self.vector_store.upsert_points(vectors, metadatas)
        
        self.retrieval._build_bm25_index()
        
        return {
            "success": True,
            "source_name": source_name,
            "chunks_count": len(chunks),
            "upserted_count": upserted_count,
        }

    def ingest_knowledge_nodes(self, nodes: List[Dict]) -> Dict:
        total_upserted = 0
        errors = []
        
        for node in nodes:
            node_name = node.get("name", "unknown")
            subject_name = node.get("subject_name", "")
            lecture_text = node.get("lecture_text", "")
            exercises_json = node.get("exercises_json", "")
            flash_cards_json = node.get("flash_cards_json", "")
            
            combined_text = ""
            if lecture_text:
                combined_text += f"【讲义】\n{lecture_text}\n\n"
            if exercises_json:
                combined_text += f"【习题】\n{exercises_json}\n\n"
            if flash_cards_json:
                combined_text += f"【闪卡】\n{flash_cards_json}\n\n"
            
            if not combined_text.strip():
                errors.append(f"{node_name}: 无内容")
                continue
            
            source_name = f"{subject_name} - {node_name}"
            result = self.ingest_text(
                text=combined_text,
                source_name=source_name,
                metadata={
                    "node_id": node.get("id"),
                    "subject_id": node.get("subject_id"),
                    "subject_name": subject_name,
                    "node_name": node_name,
                    "content_type": "knowledge_node",
                }
            )
            
            if result["success"]:
                total_upserted += result["upserted_count"]
            else:
                errors.append(f"{node_name}: {result['message']}")
        
        return {
            "success": True,
            "total_upserted": total_upserted,
            "errors": errors,
        }

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        return self.retrieval.retrieve(query, top_k=top_k)

    def get_stats(self) -> Dict:
        return self.vector_store.get_collection_stats()

    def clear_all(self):
        self.vector_store.clear_collection()
        self.retrieval._build_bm25_index()
