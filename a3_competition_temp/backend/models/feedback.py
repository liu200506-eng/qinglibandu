from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class Feedback(BaseModel):
    feedback_id: str = Field(..., description="反馈ID")
    student_id: str = Field(..., description="学生ID")
    task_id: str = Field(..., description="任务ID")
    accuracy: float = Field(0.0, ge=0.0, le=1.0, description="正确率")
    score: float = Field(0.0, ge=0.0, le=100.0, description="得分")
    improvement_summary: str = Field("", description="提升摘要")
    profile_diff: dict = Field(default_factory=dict, description="画像变化")
    created_at: datetime = Field(default_factory=datetime.now)


class FeedbackCreate(BaseModel):
    student_id: str = Field(..., description="学生ID")
    task_id: str = Field(..., description="任务ID")
    accuracy: float = Field(..., ge=0.0, le=1.0)
    score: float = Field(..., ge=0.0, le=100.0)