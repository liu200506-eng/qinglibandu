from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AgentTrace(BaseModel):
    agent_name: str = Field(..., description="Agent名称")
    started_at: datetime = Field(default_factory=datetime.now)
    finished_at: Optional[datetime] = Field(None)
    input_summary: str = Field("", description="输入摘要")
    output_summary: str = Field("", description="输出摘要")
    reasoning: str = Field("", description="推理过程")
    next_agent: Optional[str] = Field(None, description="下一个Agent")
    status: str = Field("running", description="状态")


class WorkflowTrace(BaseModel):
    trace_id: str = Field(..., description="轨迹ID")
    session_id: str = Field(..., description="会话ID")
    student_id: str = Field(..., description="学生ID")
    agent_traces: list[AgentTrace] = Field(default_factory=list, description="Agent执行轨迹")
    workflow_explanation: str = Field("", description="工作流解释")
    started_at: datetime = Field(default_factory=datetime.now)
    finished_at: Optional[datetime] = Field(None)