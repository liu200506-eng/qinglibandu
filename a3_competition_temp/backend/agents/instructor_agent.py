# -*- coding: utf-8 -*-
from agents.base_agent import BaseAgent
from graph.state import MagicStudyState, ResourcePack
from utils.llm_client import get_llm
import uuid
import json


class InstructorAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="InstructorAgent",
            description="直接回应用户的问题，结合薄弱知识点做个性化讲解"
        )
        self.llm = get_llm()
        self._rag_engine = None

    def _get_rag_engine(self):
        if self._rag_engine is None:
            try:
                from rag.engine import RAGEngine
                self._rag_engine = RAGEngine()
            except Exception:
                self._rag_engine = None
        return self._rag_engine

    def execute(self, state: MagicStudyState) -> MagicStudyState:
        profile = state.get("profile")
        weak_points = state.get("weak_points", [])
        diagnosis = state.get("diagnosis", {})
        user_message = state.get("user_message", "").strip()

        style = self._determine_style(profile)
        level_desc = self._describe_level(profile)

        retrieved_context = self._retrieve_context(user_message, weak_points)
        prompt = self._build_prompt(user_message, profile, weak_points, diagnosis, style, level_desc, retrieved_context)
        response = self.llm.invoke(prompt)

        if retrieved_context:
            state["retrieved_documents"] = retrieved_context

        pack = state.get("resource_pack") or ResourcePack(
            pack_id=str(uuid.uuid4())[:8],
            target_knowledge=weak_points
        )
        pack.lecture_text = response.content

        topics = weak_points or self._guess_topics(user_message)
        pack.mind_map = self._generate_mindmap_structure(topics, response.content)
        pack.flash_cards = self._generate_flash_cards(topics, response.content)

        state["resource_pack"] = pack
        state["tutoring_response"] = response.content
        state["_reasoning"] = "针对用户问题生成了%s风格的讲解" % style
        return state

    def _determine_style(self, profile) -> str:
        if not profile:
            return "balanced"
        pref = profile.cognitive_preference
        if pref == "visual":
            return "图示化讲解，多用示意图和结构化表格"
        if pref == "interactive":
            return "问答式讲解，穿插思考问题"
        return "详细文字讲解，逻辑清晰"

    def _describe_level(self, profile) -> str:
        if not profile:
            return "高中水平学生"
        score = getattr(profile, "knowledge_mastery", 60) or 60
        grade = getattr(profile, "grade", "") or ""
        if "大" in str(grade) or "college" in str(grade).lower():
            return "大学水平学生"
        if "初" in str(grade):
            return "初中水平学生"
        if score < 40:
            return "高中基础较弱学生"
        if score > 80:
            return "高中基础较好学生"
        return "高中水平学生"

    def _guess_topics(self, text: str) -> list:
        keywords = [
            "数学", "物理", "化学", "英语", "语文", "历史", "地理", "生物",
            "编程", "牛顿", "定律", "async", "await", "方程", "函数",
            "公式", "语法", "时态",
        ]
        found = [k for k in keywords if k.lower() in text.lower()]
        return found or ["当前问题"]

    def _retrieve_context(self, user_message: str, weak_points: list) -> list:
        rag_engine = self._get_rag_engine()
        if not rag_engine:
            return []

        try:
            queries = [user_message]
            if weak_points:
                queries.extend(weak_points[:3])

            all_results = []
            seen_sources = set()
            for query in queries:
                results = rag_engine.retrieve(query, top_k=3)
                for r in results:
                    source = r.get("metadata", {}).get("source_file", "")
                    if source and source not in seen_sources:
                        seen_sources.add(source)
                        all_results.append(r)
                    elif not source:
                        all_results.append(r)

            return all_results[:5]
        except Exception as e:
            print(f"[InstructorAgent] RAG检索失败: {e}")
            return []

    def _build_prompt(self, user_message, profile, weak_points, diagnosis, style, level_desc, retrieved_context=None) -> str:
        level_tip = self._describe_level(profile) if profile else level_desc
        wp_text = ("已知薄弱知识点（供你参考，不必逐条讲）：%s" % ", ".join(weak_points[:8])) if weak_points else "没有明确薄弱知识点记录"
        diag_text = ""
        if diagnosis:
            diag_text = "诊断信息：%s" % json.dumps(diagnosis, ensure_ascii=False)[:400]

        parts = [
            "你是一名经验丰富的一线辅导老师，讲课通俗易懂，会用类比帮助学生理解。",
            "学生水平定位：%s" % level_tip,
            "讲解风格偏好：%s" % style,
            wp_text,
        ]
        if diag_text:
            parts.append(diag_text)

        if retrieved_context and len(retrieved_context) > 0:
            context_parts = ["", "【知识库参考资料】"]
            for i, doc in enumerate(retrieved_context, 1):
                source_name = doc.get("metadata", {}).get("source_file", f"资料{i}")
                node_name = doc.get("metadata", {}).get("node_name", "")
                if node_name:
                    source_name = f"{source_name} - {node_name}"
                text = doc.get("text", "")[:1500]
                context_parts.append(f"资料{i}（{source_name}）：")
                context_parts.append(text)
                context_parts.append("")
            parts.extend(context_parts)
            parts.append("【重要】请结合以上知识库内容进行讲解，确保回答准确且有依据。")

        parts.extend([
            "",
            "学生现在问了你一个具体问题，请你直接回答这个问题，给出一份清晰的讲解。",
            "",
            "学生的问题：「%s」" % user_message,
            "",
            "讲解结构（请按这个来）：",
            "1. 先用 1 句话给一个开门见山的结论/定义（让学生立刻明白原来是什么意思）",
            "2. 核心概念详细解释（用自己的话，不要堆砌术语）",
            "3. 关键点拆解（可列 1-2-3，有公式/规则就解释每一项）",
            "4. 一个小例子或生活类比帮助理解",
            "5. 常见误区 / 易混点提醒",
            "",
            "额外要求：",
            "- Markdown 排版，适当加粗关键名词",
            "- 口吻像老师在讲课，不要说下面这些空话：",
            "   * 抱歉，你还没有指定具体知识点",
            "   * 请告诉我你具体想学习什么内容",
            "   * 请补充一个具体的薄弱知识点名称",
            "- 不要让学生再补充信息；假设问题就是它本身，直接讲",
            "",
            "如果学生的问题比较模糊（例如只说了量子、牛顿、async），请你先在心里猜它想了解的是哪方面的意思，然后选择最常见/最重要的那个角度来讲解，并在开头用一句话说明你默认的理解。",
        ])
        return "\n".join(parts)

    def _generate_mindmap_structure(self, topics: list, content: str) -> dict:
        root = topics[0] if topics else "学习主题"
        children = []
        for t in topics[:5]:
            children.append({
                "name": t,
                "children": [
                    {"name": "核心概念"},
                    {"name": "关键要点"},
                    {"name": "典型例子"},
                    {"name": "常见误区"},
                ],
            })
        if not children:
            children = [{"name": "核心概念"}, {"name": "关键要点"}, {"name": "常见误区"}]
        return {"root": root, "children": children}

    def _generate_flash_cards(self, topics: list, content: str) -> list:
        cards = []
        for i, t in enumerate(topics[:4]):
            cards.append({
                "card_id": i + 1,
                "front": "%s 的核心概念是什么？" % t,
                "back": "参见上面关于 %s 的讲解" % t,
                "difficulty": "medium",
                "tags": [t],
            })
        if not cards:
            cards.append({
                "card_id": 1,
                "front": "这道题/这个概念的核心是什么？",
                "back": "参见上面的讲解",
                "difficulty": "medium",
                "tags": ["当前问题"],
            })
        return cards
