from langgraph.graph import StateGraph, END
from graph.state import MagicStudyState, StrategyMode
from agents import (
    DiagnosticAgent, PlannerAgent, InstructorAgent,
    TrainerAgent, ReviewerAgent, ExplainerAgent,
    SocraticAgent, EmotionalAgent
)


def create_learning_graph():
    workflow = StateGraph(MagicStudyState)

    diagnostic_agent = DiagnosticAgent()
    planner_agent = PlannerAgent()
    instructor_agent = InstructorAgent()
    trainer_agent = TrainerAgent()
    reviewer_agent = ReviewerAgent()
    explainer_agent = ExplainerAgent()
    socratic_agent = SocraticAgent()
    emotional_agent = EmotionalAgent()

    workflow.add_node("diagnose", diagnostic_agent)
    workflow.add_node("plan", planner_agent)
    workflow.add_node("instruct", instructor_agent)
    workflow.add_node("train", trainer_agent)
    workflow.add_node("review", reviewer_agent)
    workflow.add_node("explain", explainer_agent)
    workflow.add_node("socratic", socratic_agent)
    workflow.add_node("emotional", emotional_agent)

    workflow.set_entry_point("diagnose")

    workflow.add_edge("diagnose", "plan")
    workflow.add_edge("plan", "instruct")
    workflow.add_edge("instruct", "train")
    workflow.add_edge("train", "review")
    workflow.add_edge("review", "explain")
    workflow.add_edge("explain", "emotional")

    def decide_tutoring_mode(state: MagicStudyState):
        mode = state.get("tutoring_mode", StrategyMode.BALANCED)
        if mode == "socratic":
            return "socratic"
        return END

    workflow.add_conditional_edges(
        "emotional",
        decide_tutoring_mode,
        {
            "socratic": "socratic",
            END: END
        }
    )

    def after_socratic(state: MagicStudyState):
        if state.get("should_rediagnose", False):
            return "diagnose"
        return END

    workflow.add_conditional_edges(
        "socratic",
        after_socratic,
        {
            "diagnose": "diagnose",
            END: END
        }
    )

    return workflow.compile()


learning_graph = create_learning_graph()