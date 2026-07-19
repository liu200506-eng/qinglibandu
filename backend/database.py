import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
# 统一数据库路径为 backend/database/qingli.db（与 path_utils.DATABASE_PATH 一致）
DATABASE_DIR = os.path.join(BACKEND_DIR, "database")
os.makedirs(DATABASE_DIR, exist_ok=True)
DB_PATH = os.path.join(DATABASE_DIR, "qingli.db")

def _set_sqlite_encoding(dbapi_conn, connection_record):
    try:
        dbapi_conn.execute("PRAGMA encoding = 'UTF-8'")
    except Exception:
        pass

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)
from sqlalchemy import event
event.listen(engine, "connect", _set_sqlite_encoding)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from models.database_models import (Student, StudentProfile, ProfileSnapshot, Subject, 
        KnowledgeNode, Course, CourseKnowledgeNode, StudyPlan, LearningTask, 
        ResourcePack, Feedback, ChatMessage, WorkflowRecord, ErrorRecord, 
        LearningEvidence, SourceDocument, DocumentChunk)
    Base.metadata.create_all(bind=engine)
