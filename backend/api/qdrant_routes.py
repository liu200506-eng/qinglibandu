"""Qdrant向量索引同步API路由"""
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Optional
from sqlalchemy.orm import Session

from database import get_db
from services.qdrant_sync_service import QdrantSyncService, get_qdrant_sync_service

router = APIRouter(prefix="/api/qdrant", tags=["Qdrant同步"])


@router.get("/consistency", summary="数据库和Qdrant一致性检查")
def consistency_check(db: Session = Depends(get_db)):
    service = get_qdrant_sync_service(db)
    return service.consistency_check()


@router.post("/embed-pending", summary="增量Embedding：为pending切片生成向量")
def embed_pending(batch_size: int = Body(20, embed=True), db: Session = Depends(get_db)):
    service = get_qdrant_sync_service(db)
    count = service.embed_pending_chunks(batch_size=batch_size)
    return {"embedded_count": count, "batch_size": batch_size}


@router.post("/delete-orphans", summary="删除孤立向量")
def delete_orphans(db: Session = Depends(get_db)):
    service = get_qdrant_sync_service(db)
    count = service.delete_orphan_vectors()
    return {"deleted_count": count}


@router.post("/sync", summary="完整同步：增量embedding + 删除孤立向量")
def full_sync(db: Session = Depends(get_db)):
    service = get_qdrant_sync_service(db)
    embedded = service.embed_pending_chunks(batch_size=100)
    deleted = service.delete_orphan_vectors()
    consistency = service.consistency_check()
    return {
        "embedded_count": embedded,
        "deleted_orphan_count": deleted,
        "consistency": consistency,
    }
