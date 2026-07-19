from graph.state import LearningProfile, StrategyMode, LearningTask
from utils.llm_client import get_llm


class ExplanationEngine:

    def __init__(self):
        self.llm = get_llm()

    def explain_profile(self, profile: LearningProfile) -> str:
        radar_data = profile.to_radar_data()

        parts = []
        parts.append("📊 你的学习画像分析：")
        parts.append("")

        for dim in radar_data["dimensions"]:
            name = dim["name"]
            value = dim["value"]
            level = "优秀" if value >= 80 else "良好" if value >= 60 else "需要提升" if value >= 40 else "薄弱"
            parts.append(f"   - {name}: {value:.0f}分 ({level})")

        parts.append("")
        parts.append(f"🎯 认知偏好：{profile.cognitive_preference}")
        parts.append("")

        if profile.knowledge_states:
            weak_points = [
                ks for ks in profile.knowledge_states.values()
                if ks.mastery < 0.6
            ]
            if weak_points:
                parts.append("⚠️ 需要关注的知识点：")
                for ks in weak_points[:3]:
                    parts.append(f"   - {ks.name} (掌握度: {ks.mastery:.0%})")

        return "\n".join(parts)

    def explain_strategy(self, profile: LearningProfile, strategy: StrategyMode) -> str:
        strategy_names = {
            StrategyMode.WEAKNESS_FIX: "补弱优先策略",
            StrategyMode.SCORE_BOOST: "提分优先策略",
            StrategyMode.EXAM_SPRINT: "考前冲刺策略",
            StrategyMode.BALANCED: "均衡发展策略",
        }

        parts = []
        parts.append(f"🎯 推荐策略：{strategy_names.get(strategy, strategy.value)}")
        parts.append("")

        if strategy == StrategyMode.WEAKNESS_FIX:
            parts.append("📋 策略说明：")
            parts.append("   当前你的知识掌握度偏低，建议优先夯实基础。")
            parts.append("   我们将从薄弱知识点及其前置知识开始补起。")
            parts.append("")
            parts.append("✅ 预期效果：")
            parts.append("   - 快速提升基础知识点掌握度")
            parts.append("   - 建立完整的知识体系")
            parts.append("   - 为后续提升打下坚实基础")

        elif strategy == StrategyMode.SCORE_BOOST:
            parts.append("📋 策略说明：")
            parts.append("   你的基础掌握较好，但迁移能力有提升空间。")
            parts.append("   建议集中突破中等难度知识点，性价比最高。")
            parts.append("")
            parts.append("✅ 预期效果：")
            parts.append("   - 快速提升分数")
            parts.append("   - 增强知识迁移能力")
            parts.append("   - 掌握举一反三的解题技巧")

        elif strategy == StrategyMode.EXAM_SPRINT:
            parts.append("📋 策略说明：")
            parts.append("   检测到你当前压力较大，推测临近考试。")
            parts.append("   采用'模拟-突破-再测'的冲刺策略。")
            parts.append("")
            parts.append("✅ 预期效果：")
            parts.append("   - 快速定位薄弱点")
            parts.append("   - 集中突破高频考点")
            parts.append("   - 在短时间内最大化分数提升")

        else:
            parts.append("📋 策略说明：")
            parts.append("   均衡发展策略适合大多数学习场景。")
            parts.append("   补弱、强化、复习交替进行。")
            parts.append("")
            parts.append("✅ 预期效果：")
            parts.append("   - 全面发展各项能力")
            parts.append("   - 稳步提升学习水平")
            parts.append("   - 保持良好的学习节奏")

        return "\n".join(parts)

    def explain_task(self, task: LearningTask, profile: LearningProfile) -> str:
        parts = []
        parts.append(f"📝 任务：{task.title}")
        parts.append("")
        parts.append(f"📊 类型：{task.task_type}")
        parts.append(f"⏱️ 预计时长：{task.estimated_minutes}分钟")
        parts.append(f"🎯 难度：{'简单' if task.difficulty < 0.4 else '中等' if task.difficulty < 0.7 else '困难'}")
        parts.append(f"📈 预期收益：{task.expected_gain * 100:.0f}分")
        parts.append("")
        parts.append(f"💡 安排原因：{task.explanation}")

        if task.knowledge_points:
            parts.append("")
            parts.append("📚 涉及知识点：")
            for kp in task.knowledge_points[:3]:
                ks = profile.knowledge_states.get(kp) if profile else None
                if ks:
                    parts.append(f"   - {ks.name} (掌握度: {ks.mastery:.0%})")
                else:
                    parts.append(f"   - {kp}")

        return "\n".join(parts)