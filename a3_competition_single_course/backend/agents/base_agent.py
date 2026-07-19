from abc import ABC, abstractmethod
from datetime import datetime
from graph.state import MagicStudyState, AgentTrace
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def __call__(self, state: MagicStudyState) -> MagicStudyState:
        trace = AgentTrace(
            agent_name=self.name,
            started_at=datetime.now(),
            input_summary=self._summarize_input(state),
            status="running"
        )

        state["current_agent"] = self.name
        traces = list(state.get("agent_traces", []))
        traces.append(trace)

        try:
            logger.info(f"[{self.name}] 开始执行...")
            result = self.execute(state)

            trace.status = "completed"
            trace.finished_at = datetime.now()
            trace.output_summary = self._summarize_output(result)
            trace.reasoning = result.get("_reasoning", "")

            logger.info(f"[{self.name}] 执行完成")

        except Exception as e:
            trace.status = "failed"
            trace.finished_at = datetime.now()
            trace.output_summary = f"Error: {str(e)}"
            logger.error(f"[{self.name}] 执行失败: {e}")
            result = state

        traces[-1] = trace
        result["agent_traces"] = traces

        return result

    @abstractmethod
    def execute(self, state: MagicStudyState) -> MagicStudyState:
        pass

    def _summarize_input(self, state: MagicStudyState) -> str:
        msg = state.get("user_message", "")
        return msg[:100] if msg else "No direct user message"

    def _summarize_output(self, state: MagicStudyState) -> str:
        resp = state.get("final_response", "")
        return resp[:100] if resp else "State updated"