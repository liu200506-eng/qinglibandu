from agents.base_agent import BaseAgent
from graph.state import MagicStudyState
from utils.llm_client import get_llm
import json


class ReviewerAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="ReviewerAgent",
            description="校验生成资源的质量、答案和覆盖度"
        )
        self.llm = get_llm()

    def execute(self, state: MagicStudyState) -> MagicStudyState:
        pack = state.get("resource_pack")
        profile = state.get("profile")
        weak_points = state.get("weak_points", [])

        if not pack:
            state["resource_quality_check"] = {"passed": False, "reason": "无资源包"}
            return state

        try:
            checks = {
                "content_quality": self._check_content_quality(pack),
                "difficulty_match": self._check_difficulty_match(pack, profile),
                "coverage": self._check_coverage(pack, weak_points),
                "answer_validity": self._check_answers(pack),
            }

            overall_score = sum(c["score"] for c in checks.values()) / len(checks)
            passed = overall_score >= 0.6

            try:
                pack.quality_score = overall_score
            except Exception:
                pass

            state["resource_pack"] = pack
            state["resource_quality_check"] = {
                "passed": passed,
                "overall_score": overall_score,
                "details": checks,
                "suggestions": self._generate_improvement_suggestions(checks)
            }
            state["_reasoning"] = f"质量评分: {overall_score:.2f}, {'通过' if passed else '需改进'}"
        except Exception as e:
            state["resource_quality_check"] = {
                "passed": False,
                "reason": f"校验失败: {str(e)[:50]}",
                "details": {},
                "suggestions": []
            }
            state["_reasoning"] = f"校验异常: {str(e)[:30]}"

        return state

    def _check_content_quality(self, pack) -> dict:
        score = 0.5
        issues = []

        if pack.lecture_text and len(pack.lecture_text) > 200:
            score += 0.3
        else:
            issues.append("讲解内容过短")

        if pack.mind_map and pack.mind_map.get("children"):
            score += 0.1
        else:
            issues.append("缺少思维导图")

        if pack.flash_cards and len(pack.flash_cards) >= 3:
            score += 0.1
        else:
            issues.append("记忆卡片不足")

        return {"score": min(score, 1.0), "issues": issues}

    def _check_difficulty_match(self, pack, profile) -> dict:
        score = 0.6
        issues = []

        if not profile:
            return {"score": score, "issues": issues}

        avg_difficulty = sum(e.get("difficulty", 0.5) for e in pack.exercises) / max(len(pack.exercises), 1)
        expected_diff = profile.knowledge_mastery / 100

        if abs(avg_difficulty - expected_diff) > 0.3:
            score -= 0.2
            issues.append(f"难度匹配度较低(期望:{expected_diff:.2f},实际:{avg_difficulty:.2f})")

        return {"score": max(score, 0), "issues": issues}

    def _check_coverage(self, pack, weak_points) -> dict:
        if not weak_points:
            return {"score": 0.8, "issues": []}

        covered = set()
        if pack.exercises:
            for ex in pack.exercises:
                kp = ex.get("knowledge_point", "")
                if kp in weak_points:
                    covered.add(kp)

        coverage_rate = len(covered) / len(weak_points)
        score = min(coverage_rate * 1.2, 1.0)

        issues = []
        if coverage_rate < 0.5:
            issues.append(f"知识点覆盖不足(仅覆盖{len(covered)}/{len(weak_points)})")

        return {"score": score, "issues": issues}

    def _check_answers(self, pack) -> dict:
        score = 0.7
        issues = []

        for i, ex in enumerate(pack.exercises):
            if not ex.get("answer"):
                score -= 0.1
                issues.append(f"第{i+1}题缺少答案")
            if not ex.get("solution"):
                score -= 0.1
                issues.append(f"第{i+1}题缺少解析")

        return {"score": max(score, 0), "issues": issues}

    def _generate_improvement_suggestions(self, checks) -> list[str]:
        suggestions = []

        if checks["content_quality"]["score"] < 0.6:
            suggestions.append("建议增加讲解内容的详细程度，补充思维导图和记忆卡片")

        if checks["difficulty_match"]["score"] < 0.6:
            suggestions.append("建议调整题目难度，使其更匹配学生当前水平")

        if checks["coverage"]["score"] < 0.6:
            suggestions.append("建议增加题目数量，确保覆盖所有薄弱知识点")

        if checks["answer_validity"]["score"] < 0.6:
            suggestions.append("建议补充完整的答案和解析内容")

        if not suggestions:
            suggestions.append("资源包质量良好，无需调整")

        return suggestions