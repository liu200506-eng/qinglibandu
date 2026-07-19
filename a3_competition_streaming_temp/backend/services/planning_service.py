from engines import StrategyEngine, ProfileEngine
from graph.state import StrategyMode, LearningTask

strategy_engine = StrategyEngine()
profile_engine = ProfileEngine()


def recommend_strategy(student_id: str) -> StrategyMode:
    profile = profile_engine.get_profile(student_id)
    if not profile:
        return StrategyMode.BALANCED
    return strategy_engine.recommend_strategy(profile)


def generate_plan(student_id: str, strategy_mode: str = "balanced") -> list[LearningTask]:
    profile = profile_engine.get_profile(student_id)
    if not profile:
        return []

    weak_points = [
        kid for kid, ks in profile.knowledge_states.items()
        if ks.mastery < 0.6
    ]

    strategy = StrategyMode(strategy_mode)
    return strategy_engine.generate_learning_path(profile, weak_points, strategy)


def adjust_plan(student_id: str, task_results: list[dict]) -> list[LearningTask]:
    profile = profile_engine.get_profile(student_id)
    if not profile:
        return []

    weak_points = [
        kid for kid, ks in profile.knowledge_states.items()
        if ks.mastery < 0.6
    ]

    strategy = strategy_engine.recommend_strategy(profile)
    tasks = strategy_engine.generate_learning_path(profile, weak_points, strategy)

    from engines.adaptive_engine import AdaptiveEngine
    adaptive_engine = AdaptiveEngine()
    return adaptive_engine.adjust_task_sequence(profile, tasks, task_results)