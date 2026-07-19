from engines import ProfileEngine
from graph.state import MagicStudyState, TutoringMode
from agents import SocraticAgent, InstructorAgent, EmotionalAgent

profile_engine = ProfileEngine()
socratic_agent = SocraticAgent()
instructor_agent = InstructorAgent()
emotional_agent = EmotionalAgent()


def chat(student_id: str, message: str, mode: str = "direct") -> dict:
    profile = profile_engine.get_profile(student_id)
    if not profile:
        profile = profile_engine.create_profile(student_id=student_id)

    tutoring_mode = TutoringMode(mode)

    state: MagicStudyState = {
        "user_message": message,
        "conversation_history": [],
        "profile": profile,
        "tutoring_mode": tutoring_mode,
        "hints": [],
        "current_hint_index": 0
    }

    if tutoring_mode == TutoringMode.SOCRATIC:
        result = socratic_agent(state)
    else:
        result = instructor_agent(state)

    result = emotional_agent(result)

    return {
        "response": result.get("tutoring_response", ""),
        "emotional_feedback": result.get("emotional_feedback", ""),
        "mode": mode
    }


def next_hint(student_id: str) -> dict:
    profile = profile_engine.get_profile(student_id)
    if not profile:
        return {"hint": "", "hint_index": 0, "total_hints": 0}

    state: MagicStudyState = {
        "user_message": "",
        "profile": profile,
        "tutoring_mode": TutoringMode.SOCRATIC,
        "hints": [],
        "current_hint_index": 0
    }

    result = socratic_agent(state)

    return {
        "hint": result.get("tutoring_response", ""),
        "hint_index": result.get("current_hint_index", 0),
        "total_hints": len(result.get("hints", []))
    }