from engines import ProfileEngine
from graph.state import LearningProfile

profile_engine = ProfileEngine()


def create_profile(student_id: str, grade: str = "", subject: str = "") -> LearningProfile:
    return profile_engine.create_profile(student_id, grade, subject)


def get_profile(student_id: str) -> LearningProfile | None:
    return profile_engine.get_profile(student_id)


def update_profile(student_id: str, updates: dict) -> LearningProfile | None:
    return profile_engine.update_profile(student_id, updates)


def update_knowledge_state(
    student_id: str,
    node_id: str,
    name: str,
    correct: bool = False,
    error_cause: str | None = None
) -> LearningProfile | None:
    return profile_engine.update_knowledge_state(student_id, node_id, name, correct=correct, error_cause=error_cause)


def get_radar_data(student_id: str) -> dict | None:
    profile = profile_engine.get_profile(student_id)
    return profile.to_radar_data() if profile else None


def get_profile_history(student_id: str, limit: int = 10) -> list[dict]:
    return profile_engine.get_profile_history(student_id, limit)