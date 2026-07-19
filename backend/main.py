import sys
import os

# 在导入任何 ML 库之前设置 HF 镜像，避免模型检查时访问 huggingface.co 超时
os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
os.environ.setdefault('HF_HUB_OFFLINE', '1')

# 添加本地依赖目录到Python路径（追加到末尾，让系统包优先）
_libs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libs")
if _libs_path not in sys.path:
    sys.path.append(_libs_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from database import init_db
from api import (
    profile_router, planning_router, resource_router,
    tutoring_router, feedback_router, workflow_router, voice_router,
    auth_router, db_router, experiment_router, rag_router, ragas_router,
    evidence_router, qdrant_router
)
from api.multimodal_routes import router as multimodal_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    print("正在初始化数据库...")
    try:
        init_db()
        from database import SessionLocal
        from services.primary_course_service import ensure_primary_course
        db = SessionLocal()
        try:
            result = ensure_primary_course(db)
            print(f"计算机网络课程检查完成: {result}")
        finally:
            db.close()
        print("数据库初始化完成")
    except Exception as e:
        print(f"数据库初始化警告: {e}")
    
    # 初始化RAG引擎
    print("正在初始化RAG引擎...")
    try:
        from rag.engine import RAGEngine
        from rag.embedding_model import init_models

        init_models()
        app.state.rag_engine = RAGEngine()
        print("RAG引擎初始化成功")
    except Exception as e:
        print(f"RAG引擎初始化失败: {e}")
        app.state.rag_engine = None

    # 自动初始化 Qdrant 向量索引（首次启动或集合为空时）
    # 解决"知识库有文件但运行页面为空"问题：确保 docker compose up 后 RAG 可用
    if app.state.rag_engine is not None:
        try:
            stats = app.state.rag_engine.get_stats("计算机网络")
            if stats.get("total_points", 0) == 0:
                print("检测到 Qdrant 向量索引为空，正在自动发布计算机网络课程...")
                from services.publish_service import PublishService
                db = SessionLocal()
                try:
                    service = PublishService(db_session=db)
                    result = service.publish_course("computer_network")
                    if result.success:
                        print(f"[OK] 课程发布成功，向量索引已建立: {result.release_id}")
                        # 重新初始化 RAG 引擎以加载新索引
                        app.state.rag_engine = RAGEngine()
                        print("[OK] RAG 引擎已重新加载向量索引")
                    else:
                        print(f"[WARN] 课程发布未成功: {result.error}")
                        print("   可手动运行: python backend/manage_knowledge.py publish computer_network")
                finally:
                    db.close()
            else:
                print(f"Qdrant 已有 {stats.get('total_points', 0)} 条向量，跳过自动初始化")
        except Exception as e:
            print(f"[ERROR] 向量索引自动初始化失败（不阻塞启动）: {e}")
            print("   可手动运行: python backend/manage_knowledge.py publish computer_network")

    yield
    # 关闭时清理资源
    print("关闭应用...")

app = FastAPI(
    title="青藜伴读 API",
    description="AI学习决策与陪练系统 API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile_router, prefix="/api")
app.include_router(planning_router, prefix="/api")
app.include_router(resource_router, prefix="/api")
app.include_router(tutoring_router, prefix="/api")
app.include_router(feedback_router, prefix="/api")
app.include_router(workflow_router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(db_router, prefix="/api")
app.include_router(multimodal_router, prefix="/api")
app.include_router(experiment_router, prefix="/api")
app.include_router(rag_router, prefix="/api")
app.include_router(ragas_router, prefix="/api")
# evidence_router自带/api前缀，无需重复添加
app.include_router(evidence_router)
app.include_router(qdrant_router)


@app.get("/")
async def root():
    return {"message": "青藜伴读 API", "version": "1.0.0"}


import shutil
from sqlalchemy import create_engine, text


@app.get("/health")
async def health_check():
    checks = {}
    all_passed = True
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy", "message": "SQLite连接正常"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "message": f"数据库连接失败: {str(e)[:50]}"}
        all_passed = False
    
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        client.get_collections()
        checks["qdrant"] = {"status": "healthy", "message": "Qdrant连接正常"}
    except Exception as e:
        checks["qdrant"] = {"status": "unhealthy", "message": f"Qdrant连接失败: {str(e)[:50]}"}
        all_passed = False
    
    try:
        from rag.embedding_model import EmbeddingModel, RerankerModel
        embedding_model = EmbeddingModel.get_instance()
        checks["embedding_model"] = {"status": "healthy", "message": f"模型加载成功: {embedding_model.__class__.__name__}"}
        
        reranker_model = RerankerModel.get_instance()
        checks["reranker_model"] = {"status": "healthy", "message": f"重排模型加载成功: {reranker_model.__class__.__name__}"}
    except Exception as e:
        checks["embedding_model"] = {"status": "unhealthy", "message": f"Embedding模型加载失败: {str(e)[:50]}"}
        checks["reranker_model"] = {"status": "unhealthy", "message": "Rerank模型加载失败"}
        all_passed = False
    
    try:
        from utils.llm_client import llm_config_status
        llm_status = llm_config_status()
        if llm_status["configured"]:
            checks["llm_service"] = {"status": "healthy", "message": f"LLM配置就绪: {llm_status['provider']} / {llm_status['model']}"}
        else:
            checks["llm_service"] = {"status": "degraded", "message": "未配置大模型API密钥"}
            all_passed = False
    except Exception as e:
        checks["llm_service"] = {"status": "degraded", "message": f"LLM服务不可用: {str(e)[:50]}"}
        all_passed = False
    
    try:
        upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        checks["file_storage"] = {"status": "healthy", "message": f"文件存储目录正常: {upload_dir}"}
    except Exception as e:
        checks["file_storage"] = {"status": "unhealthy", "message": f"文件存储目录异常: {str(e)[:50]}"}
        all_passed = False
    
    try:
        disk_usage = shutil.disk_usage(".")
        free_gb = disk_usage.free / (1024 ** 3)
        checks["disk_space"] = {"status": "healthy" if free_gb > 1 else "warning", 
                               "message": f"磁盘剩余空间: {free_gb:.1f} GB"}
    except Exception as e:
        checks["disk_space"] = {"status": "unknown", "message": f"无法检测磁盘空间: {str(e)[:50]}"}
    
    checks["rag_engine"] = {"status": "healthy" if app.state.rag_engine else "unhealthy",
                            "message": "RAG引擎已初始化" if app.state.rag_engine else "RAG引擎未初始化"}
    
    return {
        "status": "healthy" if all_passed else "degraded",
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "service": "青藜伴读 API",
        "version": "1.0.0",
        "checks": checks
    }


@app.get("/api/llm/status")
async def llm_status():
    """只报告配置状态，不发起模型调用，也绝不返回密钥。"""
    from utils.llm_client import llm_config_status
    status = llm_config_status()
    return {
        **status,
        "message": "大模型配置已就绪" if status["configured"] else "未配置大模型API密钥，请检查 backend/.env",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
        timeout_keep_alive=300
    )
