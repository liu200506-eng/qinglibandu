from graph.state import ErrorCause, LearningProfile
from utils.llm_client import get_llm
import json


class ErrorAnalysisEngine:

    def __init__(self):
        self.llm = get_llm()

    def analyze_error(
        self,
        question: str,
        student_answer: str,
        correct_answer: str,
        knowledge_point: str
    ) -> dict:
        prompt = f"""请分析以下错题的错误原因。

题目：{question}
学生答案：{student_answer}
正确答案：{correct_answer}
涉及知识点：{knowledge_point}

请分析：
1. 错误类型（概念不清/计算失误/审题偏差/迁移不足/记忆遗忘/方法错误）
2. 具体错误原因
3. 改进建议
4. 相关知识点

请输出JSON格式。
"""

        response = self.llm.invoke(prompt)
        try:
            start = response.content.find("{")
            end = response.content.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(response.content[start:end])
        except json.JSONDecodeError:
            pass

        return {
            "error_type": "unknown",
            "reason": response.content,
            "suggestion": "请仔细分析题目，理解正确解法",
            "related_topics": []
        }

    def get_error_patterns(self, profile: LearningProfile) -> list[dict]:
        patterns = []

        if not profile.error_distribution:
            return patterns

        total_errors = sum(profile.error_distribution.values())
        sorted_causes = sorted(
            profile.error_distribution.items(),
            key=lambda x: x[1], reverse=True
        )

        for cause, count in sorted_causes[:3]:
            patterns.append({
                "cause": cause,
                "count": count,
                "percentage": count / total_errors if total_errors > 0 else 0,
                "suggestion": self._get_suggestion(cause)
            })

        return patterns

    def _get_suggestion(self, cause: str) -> str:
        suggestions = {
            "concept_unclear": "建议重新学习相关概念，通过讲解和示例加深理解",
            "calculation_error": "建议加强计算专项训练，注意步骤规范",
            "question_misread": "建议练习审题技巧，标注题目关键信息",
            "transfer_weak": "建议做综合题和变式训练，提升举一反三能力",
            "memory_fade": "建议安排间隔复习，使用记忆卡片强化",
            "method_wrong": "建议系统学习解题方法，对比正误解法",
            "unknown": "建议针对性练习"
        }
        return suggestions.get(cause, "建议针对性练习")

    def predict_error_risk(self, profile: LearningProfile, knowledge_point: str) -> float:
        ks = profile.knowledge_states.get(knowledge_point)
        if not ks:
            return 0.5

        error_rate = ks.error_count / max(ks.error_count + ks.correct_count, 1)
        stability_factor = ks.stability

        return (1 - stability_factor) * 0.5 + error_rate * 0.5