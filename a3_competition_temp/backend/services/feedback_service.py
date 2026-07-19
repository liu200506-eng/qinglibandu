from engines import ProfileEngine, ErrorAnalysisEngine

profile_engine = ProfileEngine()
error_engine = ErrorAnalysisEngine()


def submit_answer(student_id: str, question_id: str, answer: str, is_correct: bool) -> dict:
    profile = profile_engine.get_profile(student_id)
    if not profile:
        return {"status": "error", "message": "Profile not found"}

    profile_engine.update_knowledge_state(
        student_id,
        node_id=question_id,
        name=question_id,
        correct=is_correct
    )

    return {"status": "success"}


def analyze_error(student_id: str, question: str, student_answer: str, correct_answer: str, knowledge_point: str) -> dict:
    analysis = error_engine.analyze_error(question, student_answer, correct_answer, knowledge_point)

    profile = profile_engine.get_profile(student_id)
    if profile:
        profile_engine.update_knowledge_state(
            student_id,
            node_id=knowledge_point,
            name=knowledge_point,
            correct=False,
            error_cause=analysis.get("error_type", "unknown")
        )

    return analysis


def get_error_patterns(student_id: str) -> list[dict]:
    profile = profile_engine.get_profile(student_id)
    if not profile:
        return []
    return error_engine.get_error_patterns(profile)