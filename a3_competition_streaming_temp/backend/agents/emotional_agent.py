from agents.base_agent import BaseAgent
from graph.state import MagicStudyState, LearningProfile
from utils.llm_client import get_llm
import re


class EmotionalAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="EmotionalAgent",
            description="感知学生情绪状态，提供情感支持和激励"
        )
        self.llm = get_llm()
        self.positive_keywords = ["太棒了", "太好了", "懂了", "会了", "开心", "自信"]
        self.negative_keywords = ["太难了", "不会", "不懂", "焦虑", "压力", "烦", "郁闷"]

    def execute(self, state: MagicStudyState) -> MagicStudyState:
        user_message = state.get("user_message", "")
        conversation_history = state.get("conversation_history", [])
        profile = state.get("profile")

        emotion_score = self._analyze_emotion(user_message, conversation_history)

        if profile:
            profile.emotional_state = emotion_score
            profile.last_updated = __import__('datetime').datetime.now()
            state["profile"] = profile
            state["profile_updated"] = True

        encouragement = self._generate_encouragement(emotion_score, user_message)
        state["emotional_feedback"] = encouragement
        state["_reasoning"] = f"情绪分析得分: {emotion_score:.0f}, 生成了对应的激励语"

        return state

    def _analyze_emotion(self, user_message, conversation_history) -> float:
        score = 70.0
        text = user_message.lower()

        for keyword in self.positive_keywords:
            if keyword in user_message:
                score += 10

        for keyword in self.negative_keywords:
            if keyword in user_message:
                score -= 15

        if conversation_history:
            recent_messages = conversation_history[-3:]
            for msg in recent_messages:
                content = msg.get("content", "").lower()
                for keyword in self.negative_keywords:
                    if keyword in content:
                        score -= 5

        difficulty_indicators = ["这题好难", "不会做", "怎么做", "太难了"]
        for indicator in difficulty_indicators:
            if indicator in user_message:
                score -= 10

        return max(20, min(100, score))

    def _generate_encouragement(self, emotion_score, user_message) -> str:
        if emotion_score >= 80:
            return "🎉 太棒了！继续保持这份热情，你正在稳步前进！"
        elif emotion_score >= 60:
            return "👍 不错！继续努力，你离目标越来越近了。有任何问题随时告诉我！"
        elif emotion_score >= 40:
            return "💪 别灰心，学习是循序渐进的过程。让我们一起分析问题，找到解决方法！"
        else:
            return "😔 我感受到你现在可能有些压力。我们可以先休息一下，或者从简单的题目开始。相信自己，你一定可以的！"