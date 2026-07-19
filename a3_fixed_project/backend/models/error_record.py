from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ErrorRecord(BaseModel):
    record_id: str = Field(..., description="记录ID")
    student_id: str = Field(..., description="学生ID")
    question: str = Field(..., description="题目内容")
    student_answer: str = Field(..., description="学生答案")
    correct_answer: str = Field(..., description="正确答案")
    knowledge_point: str = Field(..., description="涉及知识点")
    error_type: str = Field("unknown", description="错误类型")
    error_reason: str = Field("", description="错误原因")
    suggestion: str = Field("", description="改进建议")
    created_at: datetime = Field(default_factory=datetime.now)


class ErrorRecordCreate(BaseModel):
    student_id: str = Field(..., description="学生ID")
    question: str = Field(..., description="题目内容")
    student_answer: str = Field(..., description="学生答案")
    correct_answer: str = Field(..., description="正确答案")
    knowledge_point: str = Field(..., description="涉及知识点")