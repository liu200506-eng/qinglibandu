from langgraph.graph import StateGraph, END
from graph.state import MagicStudyState
from agents import DiagnosticAgent, ExplainerAgent


def create_diagnosis_graph():
    workflow = StateGraph(MagicStudyState)

    diagnostic_agent = DiagnosticAgent()
    explainer_agent = ExplainerAgent()

    workflow.add_node("diagnose", diagnostic_agent)
    workflow.add_node("explain", explainer_agent)

    workflow.set_entry_point("diagnose")
    workflow.add_edge("diagnose", "explain")
    workflow.add_edge("explain", END)

    return workflow.compile()


diagnosis_graph = create_diagnosis_graph()