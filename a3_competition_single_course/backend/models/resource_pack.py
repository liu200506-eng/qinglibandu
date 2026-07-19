from pydantic import BaseModel, Field
from typing import Optional, List


class ResourcePack(BaseModel):
    pack_id: str = Field(..., description="资源包ID")
    target_knowledge: List[str] = Field(default_factory=list, description="目标知识点")
    lecture_text: str = Field("", description="讲解文本")
    exercises: List[dict] = Field(default_factory=list, description="练习题")
    error_analysis: List[dict] = Field(default_factory=list, description="错题解析")
    mind_map: Optional[dict] = Field(None, description="思维导图数据")
    flash_cards: List[dict] = Field(default_factory=list, description="记忆卡片")
    review_schedule: List[dict] = Field(default_factory=list, description="复习计划")
    quality_score: float = Field(0.0, ge=0.0, le=1.0, description="质量评分")