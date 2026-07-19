from langgraph.graph import StateGraph, END
from graph.state import MagicStudyState, TutoringMode
from agents import SocraticAgent, InstructorAgent, EmotionalAgent


def create_tutoring_graph():
    workflow = StateGraph(MagicStudyState)

    socratic_agent = SocraticAgent()
    instructor_agent = InstructorAgent()
    emotional_agent = EmotionalAgent()

    workflow.add_node("socratic", socratic_agent)
    workflow.add_node("direct", instructor_agent)
    workflow.add_node("emotional", emotional_agent)

    def route_tutoring_mode(state: MagicStudyState):
        mode = state.get("tutoring_mode", TutoringMode.DIRECT)
        if mode == TutoringMode.SOCRATIC:
            return "socratic"
        return "direct"

    workflow.set_conditional_entry_point(route_tutoring_mode, {
        "socratic": "socratic",
        "direct": "direct"
    })

    workflow.add_edge("socratic", "emotional")
    workflow.add_edge("direct", "emotional")
    workflow.add_edge("emotional", END)

    return workflow.compile()


tutoring_graph = create_tutoring_graph()