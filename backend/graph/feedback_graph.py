from langgraph.graph import StateGraph, END
from graph.state import MagicStudyState
from agents import DiagnosticAgent, PlannerAgent, EmotionalAgent


def create_feedback_graph():
    workflow = StateGraph(MagicStudyState)

    diagnostic_agent = DiagnosticAgent()
    planner_agent = PlannerAgent()
    emotional_agent = EmotionalAgent()

    workflow.add_node("diagnose", diagnostic_agent)
    workflow.add_node("replan", planner_agent)
    workflow.add_node("emotional", emotional_agent)

    workflow.set_entry_point("diagnose")

    def need_replan(state: MagicStudyState):
        weak_points = state.get("weak_points", [])
        if len(weak_points) > 0:
            return "replan"
        return "emotional"

    workflow.add_conditional_edges(
        "diagnose",
        need_replan,
        {
            "replan": "replan",
            "emotional": "emotional"
        }
    )

    workflow.add_edge("replan", "emotional")
    workflow.add_edge("emotional", END)

    return workflow.compile()


feedback_graph = create_feedback_graph()