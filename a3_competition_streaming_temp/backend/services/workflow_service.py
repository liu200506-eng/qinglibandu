from engines import ProfileEngine
from graph.state import MagicStudyState
from graph.learning_graph import learning_graph
from agents import ExplainerAgent

profile_engine = ProfileEngine()
explainer_agent = ExplainerAgent()


def start_learning(student_id: str, user_message: str = "") -> dict:
    profile = profile_engine.get_profile(student_id)
    if not profile:
        profile = profile_engine.create_profile(student_id=student_id)

    initial_state: MagicStudyState = {
        "user_message": user_message,
        "conversation_history": [],
        "session_id": student_id,
        "profile": profile,
        "agent_traces": []
    }

    return learning_graph.invoke(initial_state)


def explain_workflow(student_id: str) -> str:
    profile = profile_engine.get_profile(student_id)
    if not profile:
        return ""

    state: MagicStudyState = {
        "profile": profile,
        "strategy_mode": "balanced",
        "study_plan": [],
        "diagnosis": {},
        "weak_points": []
    }

    result = explainer_agent(state)
    return result.get("workflow_explanation", "")