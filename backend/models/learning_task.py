from pydantic import BaseModel, Field
from typing import Optional, List


class LearningTask(BaseModel):
    task_id: str = Field(..., description="任务ID")
    title: str = Field(..., description="任务标题")
    task_type: str = Field(..., description="任务类型")
    knowledge_points: List[str] = Field(default_factory=list, description="涉及知识点")
    difficulty: float = Field(0.5, ge=0.0, le=1.0, description="难度")
    estimated_minutes: int = Field(15, ge=1, description="预计时长(分钟)")
    expected_gain: float = Field(0.5, ge=0.0, le=1.0, description="预期收益")
    status: str = Field("pending", description="状态")
    priority: int = Field(0, description="优先级")
    explanation: str = Field("", description="任务说明")


class LearningTaskCreate(BaseModel):
    title: str = Field(..., description="任务标题")
    task_type: str = Field(..., description="任务类型")
    knowledge_points: List[str] = Field(default_factory=list)
    difficulty: float = Field(0.5, ge=0.0, le=1.0)
    estimated_minutes: int = Field(15, ge=1)
    expected_gain: float = Field(0.5, ge=0.0, le=1.0)