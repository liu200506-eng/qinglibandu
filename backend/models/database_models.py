from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Student(Base):
    """学生表"""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    role = Column(String(20), default="student")  # student/teacher/admin
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # 关联
    profile = relationship("StudentProfile", back_populates="student", uselist=False)
    study_plans = relationship("StudyPlan", back_populates="student")
    learning_tasks = relationship("LearningTask", back_populates="student")
    feedback_records = relationship("Feedback", back_populates="student")
    chat_messages = relationship("ChatMessage", back_populates="student")
    workflow_records = relationship("WorkflowRecord", back_populates="student")
    learning_evidence = relationship("LearningEvidence", back_populates="student")


class StudentProfile(Base):
    """学生画像表"""
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), unique=True, nullable=False)
    education_level = Column(String(20), default="high_school")  # high_school(高中) / university(大学)
    grade = Column(String(20), default="")
    subjects = Column(JSON, default=list)  # 学科偏好列表
    cognitive_preference = Column(String(20), default="visual")  # visual/auditory/kinesthetic/reading
    learning_goal = Column(Text, default="")
    weak_points = Column(JSON, default=list)  # 薄弱知识点列表
    
    knowledge_mastery = Column(Float, default=50.0)
    prerequisite_gap = Column(Float, default=0.0)
    error_pattern_score = Column(Float, default=50.0)
    learning_efficiency = Column(Float, default=50.0)
    learning_persistence = Column(Float, default=50.0)
    
    learning_goals_constraints = Column(JSON, default=dict)
    resource_preference = Column(JSON, default=dict)
    confidence_scores = Column(JSON, default=dict)
    evidence_sources = Column(JSON, default=dict)
    
    emotional_state = Column(Float, default=70.0)
    knowledge_states = Column(JSON, default=dict)  # 知识点掌握状态
    profile_version = Column(Integer, default=1)  # 画像版本号
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关联
    student = relationship("Student", back_populates="profile")
    snapshots = relationship("ProfileSnapshot", back_populates="profile")


class ProfileSnapshot(Base):
    """画像快照表"""
    __tablename__ = "profile_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    knowledge_mastery = Column(Float, default=0.0)
    learning_stability = Column(Float, default=0.0)
    response_speed = Column(Float, default=0.0)
    emotional_state = Column(Float, default=70.0)
    self_driven_score = Column(Float, default=50.0)
    transfer_ability = Column(Float, default=50.0)
    weak_points_count = Column(Integer, default=0)
    correct_total = Column(Integer, default=0)
    error_total = Column(Integer, default=0)
    note = Column(String(200), default="")
    # 画像更新记录
    profile_version_before = Column(Integer, default=0)
    profile_version_after = Column(Integer, default=0)
    update_reason = Column(Text, default="")
    evidence_summary = Column(JSON, default=list)  # 使用的证据摘要
    affected_plans = Column(JSON, default=list)  # 受影响的学习计划

    # 关联
    profile = relationship("StudentProfile", back_populates="snapshots")


class Subject(Base):
    """科目表"""
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    course_code = Column(String(50), unique=True, nullable=False, index=True)  # 课程代码，唯一
    description = Column(Text, default="")
    icon = Column(String(50), default="")
    education_level = Column(String(20), default="high_school")  # high_school / university / all
    full_score = Column(Integer, default=100)  # 满分
    publish_status = Column(String(20), default="draft")  # draft/review/published/demo_only/archived
    schema_version = Column(String(10), default="2.0")
    created_at = Column(DateTime, server_default=func.now())

    # 关联
    knowledge_nodes = relationship("KnowledgeNode", back_populates="subject")
    courses = relationship("Course", back_populates="subject")
    source_documents = relationship("SourceDocument", back_populates="subject")


class KnowledgeNode(Base):
    """知识点表"""
    __tablename__ = "knowledge_nodes"
    __table_args__ = (
        UniqueConstraint('subject_id', 'node_code', name='uq_knowledge_node_subject_code'),
        Index('idx_knowledge_node_parent', 'parent_id'),
        Index('idx_knowledge_node_subject', 'subject_id'),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("knowledge_nodes.id"), nullable=True)
    node_code = Column(String(100), nullable=False)  # 知识点稳定编码
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    difficulty = Column(Float, default=0.5)  # 0-1难度系数
    mastery = Column(Float, default=0.0)  # 掌握程度
    mastery_threshold = Column(Float, default=0.7)  # 掌握阈值
    education_level = Column(String(20), default="high_school")  # high_school / university / all
    grade = Column(String(20), default=None)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    lecture_text = Column(Text, default=None)
    exercises_json = Column(Text, default=None)
    flash_cards_json = Column(Text, default=None)
    ai_generated_at = Column(DateTime, default=None)
    review_status = Column(String(20), default="pending")  # pending/approved/rejected
    reviewed_by = Column(String(50), default=None)
    reviewed_at = Column(DateTime, default=None)

    # 关联
    subject = relationship("Subject", back_populates="knowledge_nodes")
    parent = relationship("KnowledgeNode", remote_side=[id], backref="children")
    courses = relationship("CourseKnowledgeNode", back_populates="knowledge_node")
    learning_evidence = relationship("LearningEvidence", back_populates="knowledge_node")
    document_chunks = relationship("DocumentChunk", back_populates="knowledge_node")


class Course(Base):
    """课程视频表"""
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint('course_code', name='uq_course_code'),
        Index('idx_course_subject', 'subject_id'),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    course_code = Column(String(100), unique=True, nullable=False)  # 课程唯一代码
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    video_url = Column(String(500), default="")
    thumbnail_url = Column(String(500), default="")
    duration = Column(Integer, default=0)  # 时长（分钟）
    teacher = Column(String(50), default="")
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    # 关联
    subject = relationship("Subject", back_populates="courses")
    knowledge_nodes = relationship("CourseKnowledgeNode", back_populates="course")


class CourseKnowledgeNode(Base):
    """课程-知识点关联表"""
    __tablename__ = "course_knowledge_nodes"
    __table_args__ = (
        UniqueConstraint('course_id', 'knowledge_node_id', name='uq_course_knowledge_node'),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    knowledge_node_id = Column(Integer, ForeignKey("knowledge_nodes.id"), nullable=False)

    # 关联
    course = relationship("Course", back_populates="knowledge_nodes")
    knowledge_node = relationship("KnowledgeNode", back_populates="courses")


class StudyPlan(Base):
    """学习计划表"""
    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    title = Column(String(200), default="")
    plan_type = Column(String(50), default="")  # 查漏补缺/提分冲刺/考试冲刺/平衡发展
    target_score = Column(Integer, default=0)
    study_period = Column(String(50), default="")
    weak_points = Column(JSON, default=list)
    content = Column(Text, default="")  # 计划内容JSON
    status = Column(String(20), default="pending")  # pending/active/completed
    profile_version = Column(Integer, default=0)  # 创建时的画像版本
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关联
    student = relationship("Student", back_populates="study_plans")


class LearningTask(Base):
    """学习任务表"""
    __tablename__ = "learning_tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    task_id = Column(String(100), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    task_type = Column(String(50), default="")
    difficulty = Column(Float, default=0.5)
    estimated_minutes = Column(Integer, default=30)
    explanation = Column(Text, default="")
    status = Column(String(20), default="pending")  # pending/in_progress/completed
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关联
    student = relationship("Student", back_populates="learning_tasks")


class ResourcePack(Base):
    """学习资源包表"""
    __tablename__ = "resource_packs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    pack_id = Column(String(100), unique=True, nullable=False)
    lecture_text = Column(Text, default="")
    exercises = Column(JSON, default=list)
    mind_map = Column(JSON, default=dict)
    flash_cards = Column(JSON, default=list)
    quality_score = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now())

    # 关联
    student = relationship("Student")


class Feedback(Base):
    """学习反馈表"""
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    description = Column(Text, nullable=False)
    feedback_type = Column(String(50), default="suggestion")  # suggestion/bug/correction/other
    subject = Column(String(50), default="")
    rating = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now(), index=True)

    # 关联
    student = relationship("Student", back_populates="feedback_records")


class ChatMessage(Base):
    """聊天消息表"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user/assistant
    content = Column(Text, nullable=False)
    mode = Column(String(50), default="normal")  # normal/socratic/hint
    created_at = Column(DateTime, server_default=func.now(), index=True)

    # 关联
    student = relationship("Student", back_populates="chat_messages")


class WorkflowRecord(Base):
    """工作流记录表"""
    __tablename__ = "workflow_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    status = Column(String(20), default="pending")  # pending/running/completed/failed
    diagnosis = Column(JSON, default=dict)
    study_plan = Column(JSON, default=list)
    resource_pack = Column(JSON, default=dict)
    workflow_explanation = Column(Text, default="")
    agent_traces = Column(JSON, default=list)
    summary = Column(String(200), default="")
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关联
    student = relationship("Student", back_populates="workflow_records")


class ErrorRecord(Base):
    """错题记录表"""
    __tablename__ = "error_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    user_answer = Column(String(10), default="")
    correct_answer = Column(String(10), nullable=False)
    error_type = Column(String(100), default="")
    explanation = Column(Text, default="")
    knowledge_node_id = Column(Integer, ForeignKey("knowledge_nodes.id"), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)

    # 关联
    student = relationship("Student")
    knowledge_node = relationship("KnowledgeNode")


class LearningEvidence(Base):
    """学习证据表 - 支撑动态学习画像"""
    __tablename__ = "learning_evidence"
    __table_args__ = (
        UniqueConstraint('source_event_id', name='uq_learning_evidence_source_event'),
        Index('idx_evidence_user', 'user_id'),
        Index('idx_evidence_node', 'knowledge_node_id'),
        Index('idx_evidence_type', 'evidence_type'),
        Index('idx_evidence_created', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    knowledge_node_id = Column(Integer, ForeignKey("knowledge_nodes.id"), nullable=False)
    session_id = Column(String(100), nullable=True)  # 学习会话ID
    task_id = Column(String(100), nullable=True)  # 关联的学习任务ID
    source_event_id = Column(String(200), unique=True, nullable=False)  # 源事件ID，防重复
    evidence_type = Column(String(50), nullable=False)  # diagnosis/practice/review/socratic/code_task/resource_completion/active_question
    score = Column(Float, default=0.0)  # 得分
    max_score = Column(Float, default=100.0)  # 满分
    normalized_score = Column(Float, default=0.0)  # 归一化分数 0-1
    is_correct = Column(Boolean, default=None)  # 是否正确
    response_time_ms = Column(Integer, default=0)  # 响应时间(毫秒)
    attempt_count = Column(Integer, default=1)  # 尝试次数
    hint_count = Column(Integer, default=0)  # 提示次数
    error_pattern_id = Column(Integer, ForeignKey("error_records.id"), nullable=True)
    resource_type = Column(String(50), default="")
    profile_version_before = Column(Integer, default=0)  # 更新前画像版本
    profile_version_after = Column(Integer, default=0)  # 更新后画像版本
    raw_payload_json = Column(Text, default=None)  # 原始负载数据
    created_at = Column(DateTime, server_default=func.now(), index=True)

    # 关联
    student = relationship("Student", back_populates="learning_evidence")
    knowledge_node = relationship("KnowledgeNode", back_populates="learning_evidence")
    error_record = relationship("ErrorRecord")


class SourceDocument(Base):
    """来源文档表 - 来源追溯"""
    __tablename__ = "source_documents"
    __table_args__ = (
        UniqueConstraint('subject_id', 'doc_hash', name='uq_source_doc_hash'),
        Index('idx_source_doc_subject', 'subject_id'),
        Index('idx_source_doc_review', 'review_status'),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    title = Column(String(200), nullable=False)  # 文档标题
    author = Column(String(100), default="")  # 作者
    version = Column(String(20), default="1.0")  # 版本
    chapter = Column(String(100), default="")  # 章节
    section = Column(String(100), default="")  # 小节
    page_number = Column(String(20), default="")  # 页码
    url = Column(String(500), default="")  # 来源URL
    doc_hash = Column(String(64), nullable=False)  # 内容哈希
    license_type = Column(String(50), default="unknown")  # 许可类型
    review_status = Column(String(20), default="pending")  # pending/approved/rejected
    reviewed_by = Column(String(50), default=None)
    reviewed_at = Column(DateTime, default=None)
    created_at = Column(DateTime, server_default=func.now(), index=True)

    # 关联
    subject = relationship("Subject", back_populates="source_documents")
    chunks = relationship("DocumentChunk", back_populates="source_document")


class DocumentChunk(Base):
    """文档切片表 - RAG向量化管理"""
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint('source_doc_id', 'chunk_index', name='uq_doc_chunk_index'),
        Index('idx_doc_chunk_node', 'knowledge_node_id'),
        Index('idx_doc_chunk_hash', 'content_hash'),
        Index('idx_doc_chunk_vector', 'vector_id'),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source_doc_id = Column(Integer, ForeignKey("source_documents.id"), nullable=False)
    knowledge_node_id = Column(Integer, ForeignKey("knowledge_nodes.id"), nullable=True)
    chunk_index = Column(Integer, default=0)  # 切片序号
    content = Column(Text, nullable=False)  # 切片内容
    content_hash = Column(String(64), nullable=False)  # 内容哈希
    vector_id = Column(String(100), nullable=True)  # Qdrant向量ID
    embedding_model = Column(String(100), default="")  # Embedding模型版本
    embedding_status = Column(String(20), default="pending")  # pending/embedded/failed
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关联
    source_document = relationship("SourceDocument", back_populates="chunks")
    knowledge_node = relationship("KnowledgeNode", back_populates="document_chunks")
