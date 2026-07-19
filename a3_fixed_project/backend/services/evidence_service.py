"""学习证据服务 - 自动记录学习行为并支撑画像更新"""
from datetime import datetime
import json
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from models.database_models import (
    LearningEvidence, StudentProfile, KnowledgeNode, Subject,
    ProfileSnapshot, StudyPlan
)
from database import SessionLocal


class EvidenceService:
    """学习证据服务"""

    # 证据类型权重（用于画像更新）
    EVIDENCE_WEIGHTS = {
        "diagnosis": 1.5,           # 诊断测试（权重最高）
        "practice": 1.0,             # 普通练习
        "review": 1.2,               # 错题复练
        "socratic": 0.8,             # 苏格拉底问答
        "code_task": 1.3,            # 代码任务
        "resource_completion": 0.5,  # 资源完成
        "active_question": 0.3,     # 主动提问
    }

    def __init__(self, db: Session):
        self.db = db

    def _generate_source_event_id(
        self, user_id: int, evidence_type: str, 
        knowledge_node_id: int, session_id: Optional[str] = None,
        task_id: Optional[str] = None, external_id: Optional[str] = None
    ) -> str:
        """生成稳定的源事件ID，防止重复"""
        if external_id:
            return "ext_" + str(external_id)
        parts = [str(user_id), evidence_type, str(knowledge_node_id)]
        if session_id:
            parts.append(session_id)
        if task_id:
            parts.append(task_id)
        # 使用时间戳到秒级，同一秒内同一节点同一类型视为同一事件
        parts.append(datetime.utcnow().strftime("%Y%m%d%H%M%S"))
        raw = "|".join(parts)
        return "evd_" + uuid.uuid5(uuid.NAMESPACE_DNS, raw).hex

    def create_evidence(
        self,
        user_id: int,
        knowledge_node_id: int,
        evidence_type: str,
        score: float = 0.0,
        max_score: float = 100.0,
        is_correct: Optional[bool] = None,
        response_time_ms: int = 0,
        hint_count: int = 0,
        attempt_count: int = 1,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        source_event_id: Optional[str] = None,
        error_pattern_id: Optional[int] = None,
        resource_type: str = "",
        raw_payload: Optional[Dict[str, Any]] = None,
    ) -> LearningEvidence:
        """创建学习证据（幂等：相同source_event_id不重复写入）"""
        # 生成或使用提供的source_event_id
        if not source_event_id:
            source_event_id = self._generate_source_event_id(
                user_id, evidence_type, knowledge_node_id, session_id, task_id
            )

        # 检查是否已存在（幂等性）
        existing = self.db.query(LearningEvidence).filter(
            LearningEvidence.source_event_id == source_event_id
        ).first()
        if existing:
            return existing

        # 计算归一化分数 0-1
        normalized_score = 0.0
        if max_score > 0:
            normalized_score = max(0.0, min(1.0, score / max_score))

        # 自动判断是否正确（如果未指定）
        if is_correct is None and max_score > 0:
            is_correct = normalized_score >= 0.6

        # 获取当前画像版本
        profile = self.db.query(StudentProfile).filter(
            StudentProfile.student_id == user_id
        ).first()
        profile_version_before = profile.profile_version if profile else 0

        evidence = LearningEvidence(
            user_id=user_id,
            knowledge_node_id=knowledge_node_id,
            session_id=session_id,
            task_id=task_id,
            source_event_id=source_event_id,
            evidence_type=evidence_type,
            score=score,
            max_score=max_score,
            normalized_score=normalized_score,
            is_correct=is_correct,
            response_time_ms=response_time_ms,
            hint_count=hint_count,
            attempt_count=attempt_count,
            error_pattern_id=error_pattern_id,
            resource_type=resource_type,
            profile_version_before=profile_version_before,
            profile_version_after=profile_version_before,  # 默认不变，画像更新时回写
            raw_payload_json=json.dumps(raw_payload, ensure_ascii=False) if raw_payload else None,
        )
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        return evidence

    def get_user_evidence(
        self, user_id: int, limit: int = 100, offset: int = 0,
        evidence_type: Optional[str] = None
    ) -> List[LearningEvidence]:
        """获取用户的学习证据列表"""
        query = self.db.query(LearningEvidence).filter(
            LearningEvidence.user_id == user_id
        )
        if evidence_type:
            query = query.filter(LearningEvidence.evidence_type == evidence_type)
        return query.order_by(desc(LearningEvidence.created_at)).limit(limit).offset(offset).all()

    def get_user_node_evidence(
        self, user_id: int, knowledge_node_id: int, limit: int = 50
    ) -> List[LearningEvidence]:
        """获取用户指定知识点的学习证据"""
        return self.db.query(LearningEvidence).filter(
            and_(
                LearningEvidence.user_id == user_id,
                LearningEvidence.knowledge_node_id == knowledge_node_id
            )
        ).order_by(desc(LearningEvidence.created_at)).limit(limit).all()

    def get_user_node_evidence_by_code(
        self, user_id: int, course_code: str, node_code: str, limit: int = 50
    ) -> List[LearningEvidence]:
        """通过course_code+node_code获取学习证据"""
        # 联表查询
        return self.db.query(LearningEvidence).join(
            KnowledgeNode, LearningEvidence.knowledge_node_id == KnowledgeNode.id
        ).join(
            Subject, KnowledgeNode.subject_id == Subject.id
        ).filter(
            and_(
                LearningEvidence.user_id == user_id,
                Subject.course_code == course_code,
                KnowledgeNode.node_code == node_code
            )
        ).order_by(desc(LearningEvidence.created_at)).limit(limit).all()

    def list_evidence(
        self, user_id: Optional[int] = None, 
        knowledge_node_id: Optional[int] = None,
        evidence_type: Optional[str] = None,
        limit: int = 100, offset: int = 0
    ) -> List[LearningEvidence]:
        """通用查询接口"""
        query = self.db.query(LearningEvidence)
        if user_id:
            query = query.filter(LearningEvidence.user_id == user_id)
        if knowledge_node_id:
            query = query.filter(LearningEvidence.knowledge_node_id == knowledge_node_id)
        if evidence_type:
            query = query.filter(LearningEvidence.evidence_type == evidence_type)
        return query.order_by(desc(LearningEvidence.created_at)).limit(limit).offset(offset).all()


def get_evidence_service(db: Optional[Session] = None) -> EvidenceService:
    """获取学习证据服务实例"""
    if db is None:
        db = SessionLocal()
    return EvidenceService(db)
