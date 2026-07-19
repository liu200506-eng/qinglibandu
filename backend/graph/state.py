from __future__ import annotations
from typing import TypedDict, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class StrategyMode(str, Enum):
    WEAKNESS_FIX = "weakness_fix"
    SCORE_BOOST = "score_boost"
    EXAM_SPRINT = "exam_sprint"
    BALANCED = "balanced"


class TutoringMode(str, Enum):
    DIRECT = "direct"
    SOCRATIC = "socratic"


class ErrorCause(str, Enum):
    CONCEPT_UNCLEAR = "concept_unclear"
    CALCULATION_ERROR = "calculation_error"
    QUESTION_MISREAD = "question_misread"
    TRANSFER_WEAK = "transfer_weak"
    MEMORY_FADE = "memory_fade"
    METHOD_WRONG = "method_wrong"


class ProfileType(str, Enum):
    WEAK_FOUNDATION = "weak_foundation"
    CONFUSION_PRONE = "confusion_prone"
    STRONG_PRACTICE = "strong_practice"


@dataclass
class KnowledgeState:
    node_id: str
    name: str
    mastery: float = 0.0
    stability: float = 0.5
    last_practiced: Optional[datetime] = None
    error_count: int = 0
    correct_count: int = 0
    primary_error_cause: Optional[ErrorCause] = None
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)


@dataclass
class LearningProfile:
    student_id: str

    knowledge_mastery: float = 50.0
    prerequisite_gap: float = 0.0
    error_pattern_score: float = 50.0
    learning_efficiency: float = 50.0
    learning_persistence: float = 50.0
    learning_goals_constraints: dict = field(default_factory=dict)
    resource_preference: dict = field(default_factory=dict)

    cognitive_preference: str = "visual"
    self_driven_score: float = 50.0
    transfer_ability: float = 50.0
    emotional_state: float = 70.0

    knowledge_states: dict[str, KnowledgeState] = field(default_factory=dict)
    error_distribution: dict[str, int] = field(default_factory=dict)
    update_history: list[dict] = field(default_factory=list)
    confidence_scores: dict = field(default_factory=dict)
    evidence_sources: dict = field(default_factory=dict)

    grade: str = ""
    subject: str = ""
    subjects: list[str] = field(default_factory=list)
    learning_goal: str = ""
    weak_points: list[str] = field(default_factory=list)
    last_updated: Optional[datetime] = None

    profile_type: Optional[ProfileType] = None

    @classmethod
    def create_weak_foundation(cls, student_id: str) -> "LearningProfile":
        return cls(
            student_id=student_id,
            knowledge_mastery=25.0,
            prerequisite_gap=75.0,
            error_pattern_score=30.0,
            learning_efficiency=40.0,
            learning_persistence=50.0,
            learning_goals_constraints={
                "exam_date": "2026-08-15",
                "target_score": 60,
                "daily_available_minutes": 20,
            },
            resource_preference={
                "visual": 0.7,
                "text": 0.2,
                "code": 0.1,
                "animation": 0.6,
                "exercise": 0.8,
            },
            cognitive_preference="visual",
            self_driven_score=45.0,
            transfer_ability=30.0,
            emotional_state=60.0,
            profile_type=ProfileType.WEAK_FOUNDATION,
            weak_points=["TCP慢启动", "TCP拥塞控制", "TCP三次握手", "HTTP协议"],
            learning_goal="掌握计算机网络基础概念",
            confidence_scores={
                "knowledge_mastery": 0.75,
                "prerequisite_gap": 0.60,
                "error_pattern_score": 0.55,
                "learning_efficiency": 0.50,
                "learning_persistence": 0.65,
                "learning_goals_constraints": 0.90,
                "resource_preference": 0.60,
            },
            evidence_sources={
                "knowledge_mastery": "诊断测试5题答对1题",
                "prerequisite_gap": "前置知识点TCP连接掌握度20%",
                "error_pattern_score": "8次概念混淆错误",
                "learning_efficiency": "平均答题时间45秒/题",
                "learning_persistence": "连续3天登录",
                "learning_goals_constraints": "用户填写表单",
                "resource_preference": "偏好点击图解和动画",
            },
        )

    @classmethod
    def create_confusion_prone(cls, student_id: str) -> "LearningProfile":
        return cls(
            student_id=student_id,
            knowledge_mastery=55.0,
            prerequisite_gap=30.0,
            error_pattern_score=40.0,
            learning_efficiency=60.0,
            learning_persistence=65.0,
            learning_goals_constraints={
                "exam_date": "2026-08-20",
                "target_score": 80,
                "daily_available_minutes": 40,
            },
            resource_preference={
                "visual": 0.3,
                "text": 0.8,
                "code": 0.5,
                "animation": 0.4,
                "exercise": 0.7,
            },
            cognitive_preference="text",
            self_driven_score=60.0,
            transfer_ability=45.0,
            emotional_state=65.0,
            profile_type=ProfileType.CONFUSION_PRONE,
            weak_points=["TCP与UDP区别", "流量控制与拥塞控制", "HTTP与HTTPS"],
            learning_goal="理清易混淆概念",
            error_distribution={"concept_unclear": 8, "transfer_weak": 5, "memory_fade": 3},
            confidence_scores={
                "knowledge_mastery": 0.80,
                "prerequisite_gap": 0.70,
                "error_pattern_score": 0.75,
                "learning_efficiency": 0.65,
                "learning_persistence": 0.70,
                "learning_goals_constraints": 0.85,
                "resource_preference": 0.55,
            },
            evidence_sources={
                "knowledge_mastery": "诊断测试5题答对3题",
                "prerequisite_gap": "前置知识点掌握度70%",
                "error_pattern_score": "8次概念混淆错误",
                "learning_efficiency": "平均答题时间25秒/题",
                "learning_persistence": "连续7天登录",
                "learning_goals_constraints": "用户填写表单",
                "resource_preference": "偏好阅读文字解析",
            },
        )

    @classmethod
    def create_strong_practice(cls, student_id: str) -> "LearningProfile":
        return cls(
            student_id=student_id,
            knowledge_mastery=75.0,
            prerequisite_gap=10.0,
            error_pattern_score=65.0,
            learning_efficiency=75.0,
            learning_persistence=80.0,
            learning_goals_constraints={
                "exam_date": "2026-08-25",
                "target_score": 95,
                "daily_available_minutes": 60,
            },
            resource_preference={
                "visual": 0.4,
                "text": 0.3,
                "code": 0.9,
                "animation": 0.5,
                "exercise": 0.9,
            },
            cognitive_preference="kinesthetic",
            self_driven_score=75.0,
            transfer_ability=70.0,
            emotional_state=75.0,
            profile_type=ProfileType.STRONG_PRACTICE,
            weak_points=["TCP Reno算法细节", "QoS实现", "网络安全实践"],
            learning_goal="深入实践应用",
            confidence_scores={
                "knowledge_mastery": 0.85,
                "prerequisite_gap": 0.80,
                "error_pattern_score": 0.70,
                "learning_efficiency": 0.75,
                "learning_persistence": 0.85,
                "learning_goals_constraints": 0.90,
                "resource_preference": 0.80,
            },
            evidence_sources={
                "knowledge_mastery": "诊断测试5题答对4题",
                "prerequisite_gap": "前置知识点掌握度90%",
                "error_pattern_score": "3次计算错误",
                "learning_efficiency": "平均答题时间15秒/题",
                "learning_persistence": "连续14天登录",
                "learning_goals_constraints": "用户填写表单",
                "resource_preference": "偏好代码实战和练习",
            },
        )

    def to_radar_data(self) -> dict:
        return {
            "dimensions": [
                {"name": "知识掌握度", "value": self.knowledge_mastery},
                {"name": "先修知识缺口", "value": self.prerequisite_gap},
                {"name": "错误模式", "value": self.error_pattern_score},
                {"name": "学习效率", "value": self.learning_efficiency},
                {"name": "学习持续性", "value": self.learning_persistence},
                {"name": "目标约束", "value": self._goals_constraints_score()},
                {"name": "资源偏好", "value": self._resource_preference_score()},
            ],
            "cognitive_preference": self.cognitive_preference,
            "confidence_scores": self.confidence_scores,
            "evidence_sources": self.evidence_sources,
        }

    def _goals_constraints_score(self) -> float:
        if not self.learning_goals_constraints:
            return 50.0
        has_date = 1.0 if "exam_date" in self.learning_goals_constraints else 0.0
        has_score = 1.0 if "target_score" in self.learning_goals_constraints else 0.0
        has_time = 1.0 if "daily_available_minutes" in self.learning_goals_constraints else 0.0
        return (has_date + has_score + has_time) / 3.0 * 100.0

    def _resource_preference_score(self) -> float:
        if not self.resource_preference:
            return 50.0
        values = list(self.resource_preference.values())
        return sum(values) / len(values) * 100.0


@dataclass
class LearningTask:
    task_id: str
    title: str
    task_type: str
    knowledge_points: list[str]
    difficulty: float
    estimated_minutes: int
    expected_gain: float
    status: str = "pending"
    priority: int = 0
    explanation: str = ""
    related_resources: list[str] = field(default_factory=list)


@dataclass
class ResourcePack:
    pack_id: str
    target_knowledge: list[str]
    lecture_text: str = ""
    exercises: list[dict] = field(default_factory=list)
    error_analysis: list[dict] = field(default_factory=list)
    mind_map: Optional[dict] = None
    flash_cards: list[dict] = field(default_factory=list)
    review_schedule: list[dict] = field(default_factory=list)
    quality_score: float = 0.0


@dataclass
class AgentTrace:
    agent_name: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    input_summary: str = ""
    output_summary: str = ""
    reasoning: str = ""
    next_agent: Optional[str] = None
    status: str = "running"


class MagicStudyState(TypedDict, total=False):
    user_message: str
    conversation_history: list[dict]
    session_id: str

    profile: LearningProfile
    profile_updated: bool
    profile_diff: dict

    diagnosis: dict
    error_analysis: list[dict]
    weak_points: list[str]

    strategy_mode: StrategyMode
    study_plan: list[LearningTask]
    plan_explanation: str

    resource_pack: ResourcePack
    resource_quality_check: dict

    tutoring_mode: TutoringMode
    tutoring_response: str
    hints: list[str]
    current_hint_index: int

    task_result: dict
    accuracy_trend: list[float]
    profile_before: dict
    improvement_summary: str

    agent_traces: list[AgentTrace]
    current_agent: str
    workflow_explanation: str

    next_action: str
    should_rediagnose: bool
    should_replan: bool
    final_response: str