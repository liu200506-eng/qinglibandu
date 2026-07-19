from agents.base_agent import BaseAgent
from graph.state import MagicStudyState
from utils.llm_client import get_llm
import json


class TrainerAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="TrainerAgent",
            description="生成个性化练习题目和解析"
        )
        self.llm = get_llm()

    def execute(self, state: MagicStudyState) -> MagicStudyState:
        profile = state.get("profile")
        weak_points = state.get("weak_points", [])
        error_analysis = state.get("error_analysis", [])

        difficulty_dist = self._calculate_difficulty(profile)
        focus_areas = self._determine_focus(error_analysis)

        prompt = f"""你是一位出题专家。请针对以下知识点出练习题。

知识点：{', '.join(weak_points[:5])}
难度分布：简单{difficulty_dist['easy']}题，中等{difficulty_dist['medium']}题，困难{difficulty_dist['hard']}题
错因侧重：{json.dumps(focus_areas, ensure_ascii=False)}

请生成JSON格式的题目，每题包含：
- question: 题目内容
- options: 选项(如有)
- answer: 正确答案
- difficulty: easy/medium/hard
- knowledge_point: 对应知识点
- solution: 详细解题过程
- common_mistakes: 常见错误及原因
- similar_variation: 一道变式题(用于举一反三训练)

请输出JSON数组格式。
"""

        response = self.llm.invoke(prompt)
        exercises = self._parse_exercises(response.content)

        pack = state.get("resource_pack")
        if pack:
            pack.exercises = exercises

        state["resource_pack"] = pack
        state["_reasoning"] = f"生成{len(exercises)}道练习题，难度分布: {difficulty_dist}"

        return state

    def _calculate_difficulty(self, profile) -> dict:
        if not profile:
            return {"easy": 3, "medium": 4, "hard": 3}

        mastery = profile.knowledge_mastery
        if mastery < 40:
            return {"easy": 5, "medium": 3, "hard": 1}
        elif mastery < 70:
            return {"easy": 2, "medium": 5, "hard": 3}
        else:
            return {"easy": 1, "medium": 3, "hard": 5}

    def _determine_focus(self, error_analysis: list) -> list[str]:
        if not error_analysis:
            return ["综合练习"]

        focus = []
        for ea in error_analysis[:3]:
            cause = ea.get("cause", "")
            if cause == "concept_unclear":
                focus.append("概念辨析题")
            elif cause == "calculation_error":
                focus.append("计算强化题")
            elif cause == "transfer_weak":
                focus.append("变式应用题")
            elif cause == "question_misread":
                focus.append("审题训练题")
            else:
                focus.append("综合练习题")

        return focus

    def _parse_exercises(self, content: str) -> list[dict]:
        try:
            start = content.find("[")
            end = content.rfind("]") + 1
            if start != -1 and end > start:
                return json.loads(content[start:end])
        except json.JSONDecodeError:
            pass

        return [{"question": content, "answer": "", "difficulty": "medium"}]