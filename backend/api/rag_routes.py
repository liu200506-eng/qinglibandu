from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import tempfile
import traceback

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/upload", summary="上传文档并入库")
async def upload_documents(
    request: Request,
    files: List[UploadFile] = File(...),
    subject: str = Form("计算机网络"),
):
    engine = request.app.state.rag_engine
    if not engine:
        raise HTTPException(status_code=500, detail="RAG引擎未初始化，请安装依赖后重启")
    
    results = []
    for file in files:
        temp_path = None
        try:
            file_content = await file.read()
            file_size = len(file_content)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as f:
                f.write(file_content)
                temp_path = f.name
            
            print(f"[RAG] 开始处理文件: {file.filename}, 大小: {file_size} bytes")
            
            result = engine.ingest_document(temp_path, source_name=file.filename, metadata={"subject_name": subject})
            result["filename"] = file.filename
            results.append(result)
            print(f"[RAG] 文件处理结果: {file.filename} -> {result.get('success', False)}")
            
        except Exception as e:
            print(f"[RAG] 文件处理异常: {file.filename} -> {str(e)}")
            traceback.print_exc()
            results.append({
                "filename": file.filename,
                "success": False,
                "message": str(e)
            })
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
    
    return {"results": results}


@router.post("/query", summary="检索问答")
async def query_documents(
    request: Request,
    query: str = Query(...),
    top_k: int = Query(5, ge=1, le=20),
    subject: str = Query("计算机网络"),
):
    engine = request.app.state.rag_engine
    if not engine:
        raise HTTPException(status_code=500, detail="RAG引擎未初始化，请安装依赖后重启")
    
    results = engine.retrieve(query, top_k=top_k, subject=subject)
    return {"query": query, "results": results}


@router.get("/stats", summary="获取知识库统计")
async def get_stats(request: Request, subject: str = Query("计算机网络")):
    engine = request.app.state.rag_engine
    if not engine:
        raise HTTPException(status_code=500, detail="RAG引擎未初始化，请安装依赖后重启")
    
    stats = engine.get_stats(subject=subject)
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
