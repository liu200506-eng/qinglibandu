from pydantic import BaseModel, Field
from typing import Optional, List


class KnowledgeNode(BaseModel):
    id: str = Field(..., description="知识点ID")
    name: str = Field(..., description="知识点名称")
    subject: str = Field(..., description="学科")
    description: str = Field("", description="知识点描述")
    difficulty: float = Field(0.5, ge=0.0, le=1.0, description="难度")
    dependencies: List[str] = Field(default_factory=list, description="前置知识点ID")
    dependents: List[str] = Field(default_factory=list, description="后续知识点ID")
    mastery: float = Field(0.0, ge=0.0, le=1.0, description="掌握度")


class KnowledgeNodeCreate(BaseModel):
    name: str = Field(..., description="知识点名称")
    subject: str = Field(..., description="学科")
    description: str = Field("", description="知识点描述")
    difficulty: float = Field(0.5, ge=0.0, le=1.0)
    dependencies: List[str] = Field(default_factory=list)