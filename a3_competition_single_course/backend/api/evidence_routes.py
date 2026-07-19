"""学习证据API路由"""
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from database import get_db
from services.evidence_service import EvidenceService, get_evidence_service
from services.profile_update_service import ProfileUpdateService, get_profile_update_service
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api", tags=["学习证据"])


class EvidenceCreate(BaseModel):
    user_id: int = Field(..., description="学生ID")
    knowledge_node_id: int = Field(..., description="知识点ID")
    evidence_type: str = Field(..., description="证据类型: diagnosis/practice/review/socratic/code_task/resource_completion/active_question")
    score: float = Field(0.0, description="得分")
    max_score: float = Field(100.0, description="满分")
    is_correct: Optional[bool] = Field(None, description="是否正确")
    response_time_ms: int = Field(0, description="响应时间(毫秒)")
    hint_count: int = Field(0, description="提示次数")
    attempt_count: int = Field(1, description="尝试次数")
    session_id: Optional[str] = Field(None, description="学习会话ID")
    task_id: Optional[str] = Field(None, description="学习任务ID")
    source_event_id: Optional[str] = Field(None, description="源事件ID（用于幂等）")
    error_pattern_id: Optional[int] = Field(None, description="错题模式ID")
    resource_type: str = Field("", description="资源类型")
    raw_payload: Optional[dict] = Field(None, description="原始负载数据")


class EvidenceOut(BaseModel):
    id: int
    user_id: int
    knowledge_node_id: int
    session_id: Optional[str]
    task_id: Optional[str]
    source_event_id: str
    evidence_type: str
    score: float
    max_score: float
    normalized_score: float
    is_correct: Optional[bool]
    response_time_ms: int
    attempt_count: int
    hint_count: int
    profile_version_before: int
    profile_version_after: int
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/evidence", response_model=EvidenceOut, summary="创建学习证据")
def create_evidence(payload: EvidenceCreate, db: Session = Depends(get_db)):
    """创建学习证据（幂等：相同source_event_id不重复写入）"""
    service = EvidenceService(db)
    try:
        evidence = service.create_evidence(
            user_id=payload.user_id,
            knowledge_node_id=payload.knowledge_node_id,
            evidence_type=payload.evidence_type,
            score=payload.score,
            max_score=payload.max_score,
            is_correct=payload.is_correct,
            response_time_ms=payload.response_time_ms,
            hint_count=payload.hint_count,
            attempt_count=payload.attempt_count,
            session_id=payload.session_id,
            task_id=payload.task_id,
            source_event_id=payload.source_event_id,
            error_pattern_id=payload.error_pattern_id,
            resource_type=payload.resource_type,
            raw_payload=payload.raw_payload,
        )
        db.refresh(evidence)
        return evidence
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/evidence/user/{user_id}", summary="获取用户学习证据列表")
def list_user_evidence(
    user_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    evidence_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    service = EvidenceService(db)
    items = service.get_user_evidence(user_id, limit=limit, offset=offset, evidence_type=evidence_type)
    return {
        "user_id": user_id,
        "total": len(items),
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": e.id,
                "knowledge_node_id": e.knowledge_node_id,
                "evidence_type": e.evidence_type,
                "score": e.score,
                "max_score": e.max_score,
                "normalized_score": e.normalized_score,
                "is_correct": e.is_correct,
                "response_time_ms": e.response_time_ms,
                "attempt_count": e.attempt_count,
                "hint_count": e.hint_count,
                "session_id": e.session_id,
                "task_id": e.task_id,
                "source_event_id": e.source_event_id,
                "profile_version_before": e.profile_version_before,
                "profile_version_after": e.profile_version_after,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in items
        ],
    }


@router.get("/evidence/user/{user_id}/knowledge/{node_code}", summary="通过node_code获取学习证据")
def get_user_node_evidence(
    user_id: int,
    node_code: str,
    course_code: str = Query(..., description="课程代码"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    service = EvidenceService(db)
    items = service.get_user_node_evidence_by_code(
        user_id, course_code=course_code, node_code=node_code, limit=limit
    )
    return {
        "user_id": user_id,
        "course_code": course_code,
        "node_code": node_code,
        "total": len(items),
        "items": [
            {
                "id": e.id,
                "evidence_type": e.evidence_type,
                "score": e.score,
                "normalized_score": e.normalized_score,
                "is_correct": e.is_correct,
                "response_time_ms": e.response_time_ms,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in items
        ],
    }


@router.post("/profile/recalculate", summary="基于学习证据重新计算画像")
def recalculate_profile(
    user_id: int = Body(..., embed=True),
    knowledge_node_ids: Optional[List[int]] = Body(None, embed=True),
    reason: str = Body("API触发重新计算", embed=True),
    db: Session = Depends(get_db),
):
    """可解释的画像更新：记录更新前后画像、使用的证据、权重、公式等"""
    service = ProfileUpdateService(db)
    try:
        result = service.update_profile(
            user_id=user_id,
            knowledge_node_ids=knowledge_node_ids,
            reason=reason,
        )
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/profile/snapshots/{user_id}", summary="获取画像更新历史")
def get_profile_snapshots(
    user_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    from models.database_models import ProfileSnapshot
    from sqlalchemy import desc
    items = db.query(ProfileSnapshot).filter(
        ProfileSnapshot.student_id == user_id
    ).order_by(desc(ProfileSnapshot.created_at)).limit(limit).all()
    
    return {
        "user_id": user_id,
        "total": len(items),
        "snapshots": [
            {
                "id": s.id,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "profile_version_before": s.profile_version_before,
                "profile_version_after": s.profile_version_after,
                "knowledge_mastery": s.knowledge_mastery,
                "learning_stability": s.learning_stability,
                "response_speed": s.response_speed,
                "update_reason": s.update_reason,
                "updated_nodes_count": len(s.evidence_summary or []),
                "affected_plans_count": len(s.affected_plans or []),
            }
            for s in items
        ],
    }
