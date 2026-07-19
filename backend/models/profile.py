from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class KnowledgeStateModel(BaseModel):
    node_id: str = Field(..., description="知识点ID")
    name: str = Field(..., description="知识点名称")
    mastery: float = Field(0.0, ge=0.0, le=1.0, description="掌握度")
    stability: float = Field(0.5, ge=0.0, le=1.0, description="稳定性")
    error_count: int = Field(0, ge=0, description="错误次数")
    correct_count: int = Field(0, ge=0, description="正确次数")


class LearningProfileModel(BaseModel):
    student_id: str = Field(..., description="学生ID")

    knowledge_mastery: float = Field(50.0, ge=0.0, le=100.0, description="知识掌握度：题目正确率、知识点覆盖率、最近作答结果")
    prerequisite_gap: float = Field(0.0, ge=0.0, le=100.0, description="先修知识缺口：知识图谱依赖关系、前置知识测试结果")
    error_pattern_score: float = Field(50.0, ge=0.0, le=100.0, description="错误模式：概念混淆、计算错误、协议流程错误、迁移失败")
    learning_efficiency: float = Field(50.0, ge=0.0, le=100.0, description="学习效率：答题时间、资源阅读时间、单位时间掌握增量")
    learning_persistence: float = Field(50.0, ge=0.0, le=100.0, description="学习持续性：登录频率、任务完成率、学习间隔")
    learning_goals_constraints: dict = Field(default_factory=dict, description="学习目标与约束：考试时间、目标分数、每日可用时间")
    resource_preference: dict = Field(default_factory=dict, description="资源交互偏好：图解、代码、文字、动画、练习等实际使用行为")

    cognitive_preference: str = Field("visual", description="认知偏好")
    self_driven_score: float = Field(50.0, ge=0.0, le=100.0)
    transfer_ability: float = Field(50.0, ge=0.0, le=100.0)
    emotional_state: float = Field(70.0, ge=0.0, le=100.0)

    knowledge_states: dict[str, KnowledgeStateModel] = Field(default_factory=dict)
    error_distribution: dict[str, int] = Field(default_factory=dict)

    grade: str = Field("", description="年级")
    subject: str = Field("", description="学科")
    learning_goal: str = Field("", description="学习目标")
    last_updated: Optional[datetime] = Field(None)
    
    update_history: list = Field(default_factory=list, description="画像变化时间线")
    confidence_scores: dict = Field(default_factory=dict, description="各维度置信度分数")
    evidence_sources: dict = Field(default_factory=dict, description="各维度证据来源")