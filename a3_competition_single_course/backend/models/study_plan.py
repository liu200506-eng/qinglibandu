from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from models.learning_task import LearningTask


class StudyPlan(BaseModel):
    plan_id: str = Field(..., description="计划ID")
    student_id: str = Field(..., description="学生ID")
    strategy_mode: str = Field("balanced", description="策略模式")
    tasks: List[LearningTask] = Field(default_factory=list, description="任务列表")
    explanation: str = Field("", description="计划说明")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_tasks: List[str] = Field(default_factory=list, description="已完成任务ID")


class StudyPlanCreate(BaseModel):
    student_id: str = Field(..., description="学生ID")
    strategy_mode: str = Field("balanced", description="策略模式")