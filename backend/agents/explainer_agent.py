from agents.base_agent import BaseAgent
from graph.state import MagicStudyState
from utils.llm_client import get_llm


class ExplainerAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="ExplainerAgent",
            description="生成可解释的决策说明，让学生理解AI的推荐逻辑"
        )
        self.llm = get_llm()

    def execute(self, state: MagicStudyState) -> MagicStudyState:
        profile = state.get("profile")
        strategy_mode = state.get("strategy_mode")
        study_plan = state.get("study_plan", [])
        diagnosis = state.get("diagnosis", {})
        weak_points = state.get("weak_points", [])

        explanation = self._generate_workflow_explanation(
            profile, strategy_mode, study_plan, diagnosis, weak_points
        )

        state["workflow_explanation"] = explanation
        state["_reasoning"] = "生成了可解释的决策说明"

        return state

    def _generate_workflow_explanation(
        self, profile, strategy_mode, study_plan, diagnosis, weak_points
    ) -> str:
        parts = []
        parts.append("本次学习推荐的决策过程如下：")
        parts.append("")

        parts.append("第一步：学习状态诊断")
        if diagnosis:
            parts.append(f"   - 诊断结果: {diagnosis.get('summary', '')[:100]}...")
        if weak_points:
            parts.append(f"   - 识别薄弱点: {', '.join(weak_points[:3])}{'等' if len(weak_points) > 3 else ''}")

        parts.append("")
        parts.append("第二步：策略选择")
        if strategy_mode:
            mode_names = {
                "weakness_fix": "补弱优先策略",
                "score_boost": "提分优先策略",
                "exam_sprint": "考前冲刺策略",
                "balanced": "均衡发展策略",
            }
            mode_value = getattr(strategy_mode, 'value', strategy_mode)
            parts.append(f"   - 选中策略: {mode_names.get(mode_value, mode_value)}")

        parts.append("")
        parts.append("第三步：任务生成")
        if study_plan:
            parts.append(f"   - 共生成 {len(study_plan)} 个学习任务")
            for task in study_plan[:3]:
                title = getattr(task, 'title', str(task))
                parts.append(f"   • {title}")

        parts.append("")
        parts.append("为什么这样安排？")
        if profile:
            parts.append(f"   - 当前知识掌握度: {profile.knowledge_mastery:.0f}/100")
            stability = getattr(profile, 'learning_stability', 50)
            parts.append(f"   - 学习稳定性: {stability:.0f}/100")
            parts.append(f"   - 认知偏好: {profile.cognitive_preference}")

        parts.append("")
        parts.append("预期效果：")
        if study_plan:
            try:
                total_gain = sum(getattr(t, 'expected_gain', 0) for t in study_plan)
                parts.append(f"   - 完成全部任务预计提升: {total_gain * 100:.0f}分")
            except Exception:
                parts.append("   - 完成任务后将逐步提升知识掌握度")

        return "\n".join(parts)