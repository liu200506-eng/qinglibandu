from langgraph.graph import StateGraph, END
from graph.state import MagicStudyState
from agents import InstructorAgent, TrainerAgent, ReviewerAgent
from agents.verification_agent import VerificationAgent
from agents.safety_agent import SafetyAgent


def create_resource_pipeline():
    workflow = StateGraph(MagicStudyState)

    instructor_agent = InstructorAgent()
    trainer_agent = TrainerAgent()
    reviewer_agent = ReviewerAgent()
    verification_agent = VerificationAgent()
    safety_agent = SafetyAgent()

    workflow.add_node("generate_lecture", instructor_agent)
    workflow.add_node("generate_exercises", trainer_agent)
    workflow.add_node("quality_review", reviewer_agent)
    workflow.add_node("fact_verification", verification_agent)
    workflow.add_node("content_safety", safety_agent)

    workflow.set_entry_point("generate_lecture")

    workflow.add_edge("generate_lecture", "generate_exercises")
    workflow.add_edge("generate_exercises", "quality_review")
    workflow.add_edge("quality_review", "fact_verification")
    workflow.add_edge("fact_verification", "content_safety")

    def safety_check_decision(state: MagicStudyState):
        safety_result = state.get("safety_result", {})
        quality_check = state.get("resource_quality_check", {})
        
        if safety_result.get("passed", False) and quality_check.get("passed", False):
            state["resource_final_status"] = "completed"
            return END
        else:
            state["resource_final_status"] = "failed"
            return END

    workflow.add_conditional_edges(
        "content_safety",
        safety_check_decision,
        {
            END: END
        }
    )

    return workflow.compile()


resource_pipeline = create_resource_pipeline()