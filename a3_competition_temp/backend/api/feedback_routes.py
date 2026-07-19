from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from engines import ProfileEngine, ErrorAnalysisEngine
from models import ErrorRecordCreate, FeedbackCreate

router = APIRouter(prefix="/feedback", tags=["feedback"])

profile_engine = ProfileEngine()
error_engine = ErrorAnalysisEngine()

# 存储反馈历史（内存中）
feedback_history: list = []


class FeedbackSubmitRequest(BaseModel):
    student_id: str
    description: str
    feedback_type: str
    subject: str
    rating: float


@router.post("/submit")
async def submit_feedback_v2(req: FeedbackSubmitRequest):
    """提交用户反馈"""
    feedback_entry = {
        "id": len(feedback_history) + 1,
        "student_id": req.student_id,
        "description": req.description,
        "feedback_type": req.feedback_type,
        "subject": req.subject,
        "rating": req.rating,
        "created_at": datetime.now().isoformat()
    }
    feedback_history.append(feedback_entry)

    return {"status": "success", "feedback": feedback_entry}


@router.get("/history/{student_id}")
async def get_feedback_history(student_id: str):
    """获取用户反馈历史"""
    user_feedback = [f for f in feedback_history if f["student_id"] == student_id]
    return {"status": "success", "history": user_feedback}


@router.post("/submit-answer")
async def submit_answer(student_id: str, question_id: str, answer: str, is_correct: bool):
    profile = profile_engine.get_profile(student_id)
    if not profile:
        return {"status": "error", "message": "Profile not found"}

    knowledge_point = question_id
    profile = profile_engine.update_knowledge_state(
        student_id,
        node_id=knowledge_point,
        name=knowledge_point,
        correct=is_correct
    )

    return {
        "status": "success",
        "profile": profile_engine.serialize_profile(profile)
    }


@router.post("/analyze-error")
async def analyze_error(error_record: ErrorRecordCreate):
    analysis = error_engine.analyze_error(
        question=error_record.question,
        student_answer=error_record.student_answer,
        correct_answer=error_record.correct_answer,
        knowledge_point=error_record.knowledge_point
    )

    profile = profile_engine.get_profile(error_record.student_id)
    if profile:
        profile_engine.update_knowledge_state(
            error_record.student_id,
            node_id=error_record.knowledge_point,
            name=error_record.knowledge_point,
            correct=False,
            error_cause=analysis.get("error_type", "unknown")
        )

    return {
        "status": "success",
        "analysis": analysis
    }


@router.post("/submit-feedback")
async def submit_feedback(feedback: FeedbackCreate):
    profile = profile_engine.get_profile(feedback.student_id)
    if not profile:
        return {"status": "error", "message": "Profile not found"}

    improvement_summary = f"任务{feedback.task_id}完成，正确率{feedback.accuracy:.0%}，得分{feedback.score:.0f}"

    return {
        "status": "success",
        "improvement_summary": improvement_summary,
        "accuracy": feedback.accuracy,
        "score": feedback.score
    }


@router.get("/{student_id}/error-patterns")
async def get_error_patterns(student_id: str):
    profile = profile_engine.get_profile(student_id)
    if not profile:
        return {"status": "error", "message": "Profile not found"}

    patterns = error_engine.get_error_patterns(profile)
    return {"status": "success", "patterns": patterns}