from graph.state import LearningProfile, LearningTask
from engines.strategy_engine import StrategyEngine


class AdaptiveEngine:

    def __init__(self):
        self.strategy_engine = StrategyEngine()

    def adjust_difficulty(self, profile: LearningProfile, task: LearningTask) -> float:
        mastery = profile.knowledge_mastery / 100
        base_difficulty = task.difficulty

        if profile.response_speed < 30:
            base_difficulty = max(0.1, base_difficulty - 0.1)

        if profile.learning_stability < 40:
            base_difficulty = max(0.1, base_difficulty - 0.15)

        if profile.transfer_ability < 40:
            base_difficulty = max(0.1, base_difficulty - 0.1)

        return round(base_difficulty, 2)

    def adjust_task_sequence(
        self,
        profile: LearningProfile,
        tasks: list[LearningTask],
        recent_results: list[dict]
    ) -> list[LearningTask]:
        if not recent_results:
            return tasks

        recent_accuracy = sum(r.get("correct", 0) for r in recent_results) / max(len(recent_results), 1)

        adjusted_tasks = []
        for task in tasks:
            if recent_accuracy > 0.8:
                task.difficulty = min(1.0, task.difficulty + 0.1)
                task.expected_gain = min(1.0, task.expected_gain + 0.1)
            elif recent_accuracy < 0.4:
                task.difficulty = max(0.1, task.difficulty - 0.15)
                task.expected_gain = max(0, task.expected_gain - 0.1)

            adjusted_tasks.append(task)

        return adjusted_tasks

    def recommend_next_task(
        self,
        profile: LearningProfile,
        completed_tasks: list[str],
        remaining_tasks: list[LearningTask]
    ) -> LearningTask | None:
        if not remaining_tasks:
            return None

        sorted_tasks = sorted(
            remaining_tasks,
            key=lambda t: (t.priority, -t.expected_gain)
        )

        return sorted_tasks[0]

    def should_rediagnose(self, profile: LearningProfile, session_count: int) -> bool:
        if session_count >= 5:
            return True

        if profile.knowledge_mastery < 30:
            return True

        if profile.emotional_state < 30:
            return True

        return False

    def should_replan(self, profile: LearningProfile, task_results: list[dict]) -> bool:
        if not task_results:
            return False

        recent_accuracy = sum(r.get("correct", 0) for r in task_results[-5:]) / min(len(task_results), 5)

        if recent_accuracy > 0.9:
            return True

        if recent_accuracy < 0.3:
            return True

        return False