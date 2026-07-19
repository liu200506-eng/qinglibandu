from .student import Student, StudentCreate, StudentUpdate
from .profile import LearningProfileModel, KnowledgeStateModel
from .knowledge_node import KnowledgeNode, KnowledgeNodeCreate
from .learning_task import LearningTask, LearningTaskCreate
from .study_plan import StudyPlan, StudyPlanCreate
from .resource_pack import ResourcePack
from .error_record import ErrorRecord, ErrorRecordCreate
from .feedback import Feedback, FeedbackCreate
from .workflow_trace import WorkflowTrace, AgentTrace
from .database_models import (
    Student as StudentModel,
    StudentProfile,
    Subject,
    KnowledgeNode as KnowledgeNodeModel,
    Course,
    CourseKnowledgeNode,
    StudyPlan as StudyPlanModel,
    LearningTask as LearningTaskModel,
    ResourcePack as ResourcePackModel,
    Feedback as FeedbackModel,
    ChatMessage,
    WorkflowRecord,
    ErrorRecord as ErrorRecordModel,
)

__all__ = [
    # Pydantic模型（用于API）
    "Student",
    "StudentCreate",
    "StudentUpdate",
    "LearningProfileModel",
    "KnowledgeStateModel",
    "KnowledgeNode",
    "KnowledgeNodeCreate",
    "LearningTask",
    "LearningTaskCreate",
    "StudyPlan",
    "StudyPlanCreate",
    "ResourcePack",
    "ErrorRecord",
    "ErrorRecordCreate",
    "Feedback",
    "FeedbackCreate",
    "WorkflowTrace",
    "AgentTrace",
    # SQLAlchemy模型（用于数据库）
    "StudentModel",
    "StudentProfile",
    "Subject",
    "KnowledgeNodeModel",
    "Course",
    "CourseKnowledgeNode",
    "StudyPlanModel",
    "LearningTaskModel",
    "ResourcePackModel",
    "FeedbackModel",
    "ChatMessage",
    "WorkflowRecord",
    "ErrorRecordModel",
]
