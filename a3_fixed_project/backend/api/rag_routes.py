from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import tempfile

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/upload", summary="上传文档并入库")
async def upload_documents(request: Request, files: List[UploadFile] = File(...)):
    engine = request.app.state.rag_engine
    if not engine:
        raise HTTPException(status_code=500, detail="RAG引擎未初始化，请安装依赖后重启")
    
    results = []
    for file in files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as f:
            f.write(await file.read())
            temp_path = f.name
        
        try:
            result = engine.ingest_document(temp_path)
            result["filename"] = file.filename
            results.append(result)
        finally:
            os.unlink(temp_path)
    
    return {"results": results}


@router.post("/query", summary="检索问答")
async def query_documents(
    request: Request,
    query: str = Query(...),
    top_k: int = Query(5, ge=1, le=20),
):
    engine = request.app.state.rag_engine
    if not engine:
        raise HTTPException(status_code=500, detail="RAG引擎未初始化，请安装依赖后重启")
    
    results = engine.retrieve(query, top_k=top_k)
    return {"query": query, "results": results}


@router.get("/stats", summary="获取知识库统计")
async def get_stats(request: Request):
    engine = request.app.state.rag_engine
    if not engine:
        raise HTTPException(status_code=500, detail="RAG引擎未初始化，请安装依赖后重启")
    
    stats = engine.get_stats()
    return stats


@router.delete("/clear", summary="清空知识库")
async def clear_knowledge_base(request: Request):
    engine = request.app.state.rag_engine
    if not engine:
        raise HTTPException(status_code=500, detail="RAG引擎未初始化，请安装依赖后重启")
    
    engine.clear_all()
    return {"message": "知识库已清空"}


@router.get("/health", summary="健康检查")
async def health_check(request: Request):
    engine = request.app.state.rag_engine
    if engine:
        return {"status": "healthy", "rag_engine": "ready"}
    return {"status": "healthy", "rag_engine": "not initialized", "message": "请安装RAG依赖后重启"}
