from agents.base_agent import BaseAgent
from graph.state import MagicStudyState, ErrorCause, KnowledgeState
from utils.llm_client import get_llm
from prompts.diagnostic_prompts import DIAGNOSTIC_PROMPT
import json


class DiagnosticAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="DiagnosticAgent",
            description="诊断学生当前学习状态、薄弱知识点和错因分布"
        )
        self.llm = get_llm()

    def execute(self, state: MagicStudyState) -> MagicStudyState:
        profile = state.get("profile")
        conversation = state.get("conversation_history", [])
        user_message = state.get("user_message", "")
        task_result = state.get("task_result", {})

        context = self._build_diagnostic_context(profile, conversation, task_result)

        prompt = DIAGNOSTIC_PROMPT.format(
            context=context,
            user_message=user_message,
            current_profile=json.dumps(profile.to_radar_data(), ensure_ascii=False) if profile else "无",
            knowledge_states=self._format_knowledge_states(profile)
        )

        response = self.llm.invoke(prompt)
        diagnosis = self._parse_diagnosis(response.content)

        error_analysis = self._analyze_errors(diagnosis, profile)
        weak_points = self._identify_weak_points(diagnosis, profile)

        state["diagnosis"] = diagnosis
        state["error_analysis"] = error_analysis
        state["weak_points"] = weak_points
        state["_reasoning"] = f"诊断出{len(weak_points)}个薄弱知识点，主要错因: {diagnosis.get('primary_error_cause', '未知')}"

        return state

    def _build_diagnostic_context(self, profile, conversation, task_result) -> str:
        parts = []

        if profile and profile.knowledge_states:
            low_mastery = [
                f"{ks.name}(掌握度:{ks.mastery:.0%})"
                for ks in profile.knowledge_states.values()
                if ks.mastery < 0.6
            ]
            if low_mastery:
                parts.append(f"当前薄弱知识点: {', '.join(low_mastery)}")

        if task_result:
            parts.append(f"最近任务结果: 正确率{task_result.get('accuracy', 0):.0%}")
            if task_result.get("wrong_questions"):
                parts.append(f"错题数: {len(task_result['wrong_questions'])}")

        if conversation:
            recent = conversation[-5:]
            parts.append(f"最近{len(recent)}轮对话摘要已加载")

        return "\n".join(parts) if parts else "首次诊断，无历史数据"

    def _format_knowledge_states(self, profile) -> str:
        if not profile or not profile.knowledge_states:
            return "暂无知识点状态数据"

        lines = []
        for ks in sorted(profile.knowledge_states.values(), key=lambda x: x.mastery):
            lines.append(
                f"- {ks.name}: 掌握度{ks.mastery:.0%}, "
                f"稳定性{ks.stability:.0%}, "
                f"错{ks.error_count}次/对{ks.correct_count}次"
            )
        return "\n".join(lines[:20])

    def _parse_diagnosis(self, content: str) -> dict:
        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(content[start:end])
        except json.JSONDecodeError:
            pass

        return {
            "summary": content,
            "weak_areas": [],
            "primary_error_cause": "unknown",
            "confidence": 0.5,
            "suggestions": []
        }

    def _analyze_errors(self, diagnosis: dict, profile) -> list[dict]:
        errors = []

        if profile and profile.error_distribution:
            for cause, count in sorted(
                profile.error_distribution.items(),
                key=lambda x: x[1], reverse=True
            ):
                errors.append({
                    "cause": cause,
                    "count": count,
                    "percentage": count / max(sum(profile.error_distribution.values()), 1),
                    "suggestion": self._get_error_suggestion(cause)
                })

        return errors

    def _identify_weak_points(self, diagnosis: dict, profile) -> list[str]:
        weak = []

        if profile and profile.knowledge_states:
            for kid, ks in profile.knowledge_states.items():
                if ks.mastery < 0.6:
                    weak.append(kid)

        if diagnosis.get("weak_areas"):
            for area in diagnosis["weak_areas"]:
                if area not in weak:
                    weak.append(area)

        return weak

    def _get_error_suggestion(self, cause: str) -> str:
        suggestions = {
            "concept_unclear": "建议重新学习相关概念，通过讲解和示例加深理解",
            "calculation_error": "建议加强计算专项训练，注意步骤规范",
            "question_misread": "建议练习审题技巧，标注题目关键信息",
            "transfer_weak": "建议做综合题和变式训练，提升举一反三能力",
            "memory_fade": "建议安排间隔复习，使用记忆卡片强化",
            "method_wrong": "建议系统学习解题方法，对比正误解法",
        }
        return suggestions.get(cause, "建议针对性练习")