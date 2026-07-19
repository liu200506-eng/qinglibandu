from pydantic import BaseModel, Field
from datetime import datetime


class Student(BaseModel):
    id: str = Field(..., description="学生ID")
    name: str = Field(..., description="学生姓名")
    grade: str = Field(..., description="年级")
    subject: str = Field(..., description="学科")
    learning_goal: str = Field("", description="学习目标")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class StudentCreate(BaseModel):
    name: str = Field(..., description="学生姓名")
    grade: str = Field(..., description="年级")
    subject: str = Field(..., description="学科")
    learning_goal: str = Field("", description="学习目标")


class StudentUpdate(BaseModel):
    name: str = Field(None, description="学生姓名")
    grade: str = Field(None, description="年级")
    subject: str = Field(None, description="学科")
    learning_goal: str = Field(None, description="学习目标")