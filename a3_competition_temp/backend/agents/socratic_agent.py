from agents.base_agent import BaseAgent
from graph.state import MagicStudyState, TutoringMode
from utils.llm_client import get_llm
from prompts.socratic_prompts import SOCRATIC_PROMPT


class SocraticAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="SocraticAgent",
            description="采用苏格拉底式提问引导学生自主思考"
        )
        self.llm = get_llm()

    def execute(self, state: MagicStudyState) -> MagicStudyState:
        user_message = state.get("user_message", "")
        conversation_history = state.get("conversation_history", [])
        diagnosis = state.get("diagnosis", {})
        weak_points = state.get("weak_points", [])

        hints = state.get("hints", [])
        current_hint_index = state.get("current_hint_index", 0)

        if current_hint_index == 0:
            hints = self._generate_hint_sequence(user_message, diagnosis, weak_points)
            state["hints"] = hints
            state["current_hint_index"] = 0

        if current_hint_index < len(hints):
            response = hints[current_hint_index]
            state["tutoring_response"] = response
            state["current_hint_index"] = current_hint_index + 1
            state["_reasoning"] = f"提供第{current_hint_index + 1}/{len(hints)}个苏格拉底提示"
        else:
            response = self._generate_final_summary(user_message, conversation_history)
            state["tutoring_response"] = response
            state["_reasoning"] = "苏格拉底引导结束，生成总结"

        state["tutoring_mode"] = TutoringMode.SOCRATIC

        return state

    def _generate_hint_sequence(self, user_message, diagnosis, weak_points) -> list[str]:
        prompt = SOCRATIC_PROMPT.format(
            user_message=user_message,
            weak_points=", ".join(weak_points[:3]),
            diagnosis_summary=diagnosis.get("summary", "")[:200]
        )

        response = self.llm.invoke(prompt)
        content = response.content

        hints = []
        for i, line in enumerate(content.split("\n")):
            line = line.strip()
            if line and (line.startswith(f"{i+1}.") or line.startswith("-")):
                hints.append(line.replace(f"{i+1}.", "").replace("-", "").strip())

        if not hints:
            hints = [
                "让我们先想一想这个问题涉及哪些知识点？",
                "你觉得解决这个问题的关键在哪里？",
                "如果从另一个角度看，这个问题会怎样？",
                "你以前遇到过类似的问题吗？当时是怎么解决的？",
                "让我来帮你梳理一下思路..."
            ]

        return hints[:5]

    def _generate_final_summary(self, user_message, conversation_history) -> str:
        recent = conversation_history[-5:] if conversation_history else []
        history_str = "\n".join([f"{m.get('role', '')}: {m.get('content', '')[:50]}" for m in recent])

        prompt = f"""请对以下对话进行总结，给出最终答案和学习建议。

用户问题：{user_message}
对话历史：
{history_str}

请总结：
1. 用户最终理解了什么？
2. 问题的正确答案是什么？
3. 相关的知识点有哪些？
4. 学习建议是什么？
"""

        response = self.llm.invoke(prompt)
        return response.content