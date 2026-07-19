from agents.base_agent import BaseAgent
from graph.state import MagicStudyState
import re


class SafetyAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="SafetyAgent",
            description="内容安全Agent - 检测并过滤违规、危险和敏感内容"
        )

    def execute(self, state: MagicStudyState) -> MagicStudyState:
        generated_content = state.get("generated_content", "")
        safety_result = {
            "passed": True,
            "violations": [],
            "filtered_content": generated_content
        }

        violations = []

        if self._detect_malicious_code(generated_content):
            violations.append("检测到恶意代码")
            safety_result["passed"] = False

        if self._detect_academic_cheating(generated_content):
            violations.append("检测到学术作弊相关内容")
            safety_result["passed"] = False

        if self._detect_dangerous_behavior(generated_content):
            violations.append("检测到危险行为描述")
            safety_result["passed"] = False

        if self._detect_privacy_info(generated_content):
            violations.append("检测到隐私信息")
            safety_result["passed"] = False

        if self._detect_illegal_content(generated_content):
            violations.append("检测到违法内容")
            safety_result["passed"] = False

        if violations:
            safety_result["violations"] = violations
            safety_result["filtered_content"] = self._filter_content(generated_content)

        state["safety_result"] = safety_result

        if not safety_result["passed"]:
            current_check = state.get("resource_quality_check", {})
            current_check["passed"] = False
            current_check["reason"] = current_check.get("reason", "") + "; 内容安全检查未通过"
            state["resource_quality_check"] = current_check

        return state

    def _detect_malicious_code(self, content: str) -> bool:
        patterns = [
            r"(rm\s+-rf\s+/)",
            r"(format\s+\w:)",
            r"(del\s+/f\s+/s\s+/q)",
            r"(curl.*|wget.*|bash.*|python.*)",
            r"(exec\(|eval\(|system\()",
            r"(<script>|<iframe>)"
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)

    def _detect_academic_cheating(self, content: str) -> bool:
        keywords = [
            "代写", "代考", "替考", "作弊", "抄答案",
            "帮我写", "帮我做", "替我写", "替我做",
            "作业代写", "论文代写", "考试代考"
        ]
        return any(keyword in content for keyword in keywords)

    def _detect_dangerous_behavior(self, content: str) -> bool:
        keywords = [
            "自杀", "自残", "杀人", "放火", "爆炸",
            "毒品", "枪支", "暴力", "攻击", "入侵"
        ]
        return any(keyword in content for keyword in keywords)

    def _detect_privacy_info(self, content: str) -> bool:
        patterns = [
            r"1[3-9]\d{9}",
            r"\d{18}",
            r"[\w.-]+@[\w.-]+\.\w+",
            r"身份证号", "银行卡号", "手机号"
        ]
        return any(re.search(pattern, content) for pattern in patterns)

    def _detect_illegal_content(self, content: str) -> bool:
        keywords = [
            "赌博", "色情", "诈骗", "传销", "洗钱",
            "违法", "犯罪", "走私", "盗版", "侵权"
        ]
        return any(keyword in content for keyword in keywords)

    def _filter_content(self, content: str) -> str:
        filtered = content
        patterns_to_remove = [
            r"(rm\s+-rf\s+/.*)",
            r"(<script>.*?</script>)",
            r"(1[3-9]\d{9})",
            r"(\d{18})"
        ]
        for pattern in patterns_to_remove:
            filtered = re.sub(pattern, "[已过滤]", filtered)
        return filtered
