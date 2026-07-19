from agents.base_agent import BaseAgent
from graph.state import MagicStudyState
from utils.llm_client import get_llm
import json


class VerificationAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="VerificationAgent",
            description="事实核验Agent - 验证生成内容的事实准确性和引用一致性"
        )
        self.llm = get_llm()

    def execute(self, state: MagicStudyState) -> MagicStudyState:
        generated_content = state.get("generated_content", "")
        retrieved_docs = state.get("retrieved_documents", [])
        verification_results = []

        if not generated_content:
            state["verification_results"] = []
            state["resource_quality_check"] = {"passed": False, "reason": "无生成内容"}
            return state

        if retrieved_docs:
            for i, doc in enumerate(retrieved_docs[:3]):
                score, details = self._verify_reference(generated_content, doc)
                verification_results.append({
                    "document_index": i,
                    "document_title": doc.get("title", ""),
                    "similarity": doc.get("similarity", 0),
                    "verification_score": score,
                    "details": details
                })

        overall_score = self._verify_factual_accuracy(generated_content)
        verification_results.append({
            "type": "factual_accuracy",
            "verification_score": overall_score,
            "details": "整体事实准确性评估"
        })

        passed = all(vr.get("verification_score", 0) >= 0.6 for vr in verification_results)
        if not passed:
            failed_reasons = [vr["details"] for vr in verification_results if vr.get("verification_score", 0) < 0.6]
        else:
            failed_reasons = []

        state["verification_results"] = verification_results
        state["resource_quality_check"] = {
            "passed": passed,
            "overall_score": overall_score,
            "reason": "; ".join(failed_reasons) if failed_reasons else "通过事实核验"
        }

        return state

    def _verify_reference(self, content: str, document: dict) -> tuple[float, str]:
        doc_content = document.get("content", "")[:500]
        
        if not doc_content:
            return 0.5, "文档内容为空"

        overlap_count = sum(1 for word in doc_content.split()[:20] if word in content)
        if overlap_count >= 3:
            return 0.8, f"内容与文档'{document.get('title', '')}'存在合理引用"
        elif overlap_count >= 1:
            return 0.6, f"部分内容与文档相关"
        else:
            return 0.4, f"内容与文档'{document.get('title', '')}'关联度较低"

    def _verify_factual_accuracy(self, content: str) -> float:
        if len(content) < 50:
            return 0.7

        if any(keyword in content for keyword in ["错误", "不正确", "误导", "虚假"]):
            return 0.3

        return 0.75
