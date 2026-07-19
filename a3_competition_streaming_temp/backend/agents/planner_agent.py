from agents.base_agent import BaseAgent
from graph.state import (
    MagicStudyState, StrategyMode, LearningTask, LearningProfile
)
from utils.llm_client import get_llm
import json
import uuid


class PlannerAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="PlannerAgent",
            description="基于画像和诊断生成个性化学习策略与任务序列"
        )
        self.llm = get_llm()

    def execute(self, state: MagicStudyState) -> MagicStudyState:
        profile = state.get("profile")
        diagnosis = state.get("diagnosis", {})
        weak_points = state.get("weak_points", [])
        strategy_mode = state.get("strategy_mode", StrategyMode.BALANCED)

        if strategy_mode == StrategyMode.BALANCED:
            strategy_mode = self._auto_select_strategy(profile, diagnosis)
            state["strategy_mode"] = strategy_mode

        tasks = self._generate_task_sequence(
            profile, diagnosis, weak_points, strategy_mode
        )

        explanation = self._generate_explanation(
            profile, strategy_mode, tasks, weak_points
        )

        state["study_plan"] = tasks
        state["plan_explanation"] = explanation
        state["_reasoning"] = (
            f"策略模式: {strategy_mode.value}, "
            f"生成{len(tasks)}个任务, "
            f"覆盖{len(weak_points)}个薄弱点"
        )

        return state

    def _auto_select_strategy(
        self, profile: LearningProfile, diagnosis: dict
    ) -> StrategyMode:
        if not profile:
            return StrategyMode.BALANCED

        if profile.knowledge_mastery < 40:
            return StrategyMode.WEAKNESS_FIX

        if profile.emotional_state < 40:
            return StrategyMode.EXAM_SPRINT

        if profile.knowledge_mastery >= 60 and profile.transfer_ability < 50:
            return StrategyMode.SCORE_BOOST

        return StrategyMode.BALANCED

    def _generate_task_sequence(
        self,
        profile: LearningProfile,
        diagnosis: dict,
        weak_points: list[str],
        strategy_mode: StrategyMode
    ) -> list[LearningTask]:
        tasks = []

        if strategy_mode == StrategyMode.WEAKNESS_FIX:
            tasks = self._weakness_fix_plan(profile, weak_points)
        elif strategy_mode == StrategyMode.SCORE_BOOST:
            tasks = self._score_boost_plan(profile, weak_points)
        elif strategy_mode == StrategyMode.EXAM_SPRINT:
            tasks = self._exam_sprint_plan(profile, weak_points)
        else:
            tasks = self._balanced_plan(profile, weak_points)

        tasks = self._insert_checkpoints(tasks)

        return tasks

    def _weakness_fix_plan(
        self, profile: LearningProfile, weak_points: list[str]
    ) -> list[LearningTask]:
        tasks = []
        priority = 0

        for wp in weak_points[:5]:
            ks = profile.knowledge_states.get(wp) if profile else None

            if ks and ks.dependencies:
                for dep in ks.dependencies:
                    dep_ks = profile.knowledge_states.get(dep)
                    if dep_ks and dep_ks.mastery < 0.7:
                        tasks.append(LearningTask(
                            task_id=str(uuid.uuid4())[:8],
                            title=f"补充前置: {dep_ks.name}",
                            task_type="lesson",
                            knowledge_points=[dep],
                            difficulty=0.3,
                            estimated_minutes=15,
                            expected_gain=0.6,
                            priority=priority,
                            explanation=f"'{ks.name if ks else wp}'依赖此前置知识，需要先掌握"
                        ))
                        priority += 1

            tasks.append(LearningTask(
                task_id=str(uuid.uuid4())[:8],
                title=f"重点讲解: {ks.name if ks else wp}",
                task_type="lesson",
                knowledge_points=[wp],
                difficulty=0.4,
                estimated_minutes=20,
                expected_gain=0.7,
                priority=priority,
                explanation=f"该知识点掌握度仅{ks.mastery:.0%}，需要系统复习" if ks else "诊断发现的薄弱点"
            ))
            priority += 1

            tasks.append(LearningTask(
                task_id=str(uuid.uuid4())[:8],
                title=f"专项练习: {ks.name if ks else wp}",
                task_type="exercise",
                knowledge_points=[wp],
                difficulty=0.5,
                estimated_minutes=15,
                expected_gain=0.5,
                priority=priority,
                explanation="通过练习巩固刚学习的内容"
            ))
            priority += 1

        return tasks

    def _score_boost_plan(
        self, profile: LearningProfile, weak_points: list[str]
    ) -> list[LearningTask]:
        tasks = []
        priority = 0

        medium_points = []
        if profile and profile.knowledge_states:
            for kid, ks in profile.knowledge_states.items():
                if 0.4 <= ks.mastery <= 0.75:
                    medium_points.append((kid, ks))

        medium_points.sort(key=lambda x: x[1].mastery, reverse=True)

        for kid, ks in medium_points[:6]:
            tasks.append(LearningTask(
                task_id=str(uuid.uuid4())[:8],
                title=f"强化训练: {ks.name}",
                task_type="exercise",
                knowledge_points=[kid],
                difficulty=0.6,
                estimated_minutes=20,
                expected_gain=0.8,
                priority=priority,
                explanation=f"掌握度{ks.mastery:.0%}，接近突破点，强化训练性价比最高"
            ))
            priority += 1

        return tasks

    def _exam_sprint_plan(
        self, profile: LearningProfile, weak_points: list[str]
    ) -> list[LearningTask]:
        tasks = []

        tasks.append(LearningTask(
            task_id=str(uuid.uuid4())[:8],
            title="模拟诊断测试",
            task_type="diagnosis",
            knowledge_points=weak_points[:10],
            difficulty=0.7,
            estimated_minutes=30,
            expected_gain=0.3,
            priority=0,
            explanation="先通过模拟测试精准定位当前水平"
        ))

        for i, wp in enumerate(weak_points[:3]):
            tasks.append(LearningTask(
                task_id=str(uuid.uuid4())[:8],
                title=f"考点速攻: {wp}",
                task_type="exercise",
                knowledge_points=[wp],
                difficulty=0.7,
                estimated_minutes=15,
                expected_gain=0.6,
                priority=i + 1,
                explanation="高频考点集中突破"
            ))

        tasks.append(LearningTask(
            task_id=str(uuid.uuid4())[:8],
            title="再次模拟检测",
            task_type="diagnosis",
            knowledge_points=weak_points[:10],
            difficulty=0.7,
            estimated_minutes=25,
            expected_gain=0.4,
            priority=len(tasks),
            explanation="验证冲刺效果"
        ))

        return tasks

    def _balanced_plan(
        self, profile: LearningProfile, weak_points: list[str]
    ) -> list[LearningTask]:
        tasks = []
        priority = 0

        for wp in weak_points[:2]:
            tasks.append(LearningTask(
                task_id=str(uuid.uuid4())[:8],
                title=f"知识补强: {wp}",
                task_type="lesson",
                knowledge_points=[wp],
                difficulty=0.4,
                estimated_minutes=20,
                expected_gain=0.6,
                priority=priority,
                explanation="均衡安排中的基础补强环节"
            ))
            priority += 1

        tasks.append(LearningTask(
            task_id=str(uuid.uuid4())[:8],
            title="综合练习",
            task_type="exercise",
            knowledge_points=weak_points[:4],
            difficulty=0.6,
            estimated_minutes=25,
            expected_gain=0.5,
            priority=priority,
            explanation="综合练习提升知识迁移能力"
        ))
        priority += 1

        tasks.append(LearningTask(
            task_id=str(uuid.uuid4())[:8],
            title="周期复习",
            task_type="review",
            knowledge_points=weak_points[:6],
            difficulty=0.3,
            estimated_minutes=15,
            expected_gain=0.4,
            priority=priority,
            explanation="间隔复习防止遗忘"
        ))

        return tasks

    def _insert_checkpoints(self, tasks: list[LearningTask]) -> list[LearningTask]:
        result = []
        for i, task in enumerate(tasks):
            result.append(task)
            if (i + 1) % 4 == 0 and i < len(tasks) - 1:
                result.append(LearningTask(
                    task_id=str(uuid.uuid4())[:8],
                    title="阶段检测",
                    task_type="diagnosis",
                    knowledge_points=[t.knowledge_points[0] for t in tasks[max(0,i-3):i+1] if t.knowledge_points],
                    difficulty=0.5,
                    estimated_minutes=10,
                    expected_gain=0.2,
                    priority=task.priority + 1,
                    explanation="定期检测以判断是否需要调整学习路径"
                ))
        return result

    def _generate_explanation(
        self,
        profile: LearningProfile,
        strategy: StrategyMode,
        tasks: list[LearningTask],
        weak_points: list[str]
    ) -> str:
        strategy_names = {
            StrategyMode.WEAKNESS_FIX: "补弱优先",
            StrategyMode.SCORE_BOOST: "提分优先",
            StrategyMode.EXAM_SPRINT: "考前冲刺",
            StrategyMode.BALANCED: "均衡发展",
        }

        explanation_parts = [
            f"📋 学习策略: {strategy_names.get(strategy, '均衡')}",
            f"📊 诊断发现 {len(weak_points)} 个薄弱知识点",
            f"📝 共安排 {len(tasks)} 个学习任务",
            "",
            "🔍 策略选择原因:",
        ]

        if strategy == StrategyMode.WEAKNESS_FIX:
            explanation_parts.append(
                f"  你的知识掌握度({profile.knowledge_mastery:.0f}/100)偏低，"
                "当前阶段应优先夯实基础，从薄弱知识点和它们的前置知识开始补起。"
            )
        elif strategy == StrategyMode.SCORE_BOOST:
            explanation_parts.append(
                f"  你的基础掌握较好({profile.knowledge_mastery:.0f}/100)，"
                f"但迁移能力({profile.transfer_ability:.0f}/100)有提升空间。"
                "建议集中突破中等难度知识点，性价比最高。"
            )
        elif strategy == StrategyMode.EXAM_SPRINT:
            explanation_parts.append(
                "  检测到你当前压力较大，推测临近考试。"
                "采用'模拟-突破-再测'的冲刺策略。"
            )

        explanation_parts.append("")
        explanation_parts.append("📌 任务安排逻辑:")
        for task in tasks[:5]:
            explanation_parts.append(f"  • {task.title}: {task.explanation}")

        if len(tasks) > 5:
            explanation_parts.append(f"  ... 还有 {len(tasks) - 5} 个任务")

        return "\n".join(explanation_parts)