from fastapi import APIRouter
from pydantic import BaseModel
from engines import ProfileEngine, StrategyEngine
from graph.state import MagicStudyState, TutoringMode, LearningProfile
from graph.learning_graph import learning_graph
from agents import SocraticAgent, InstructorAgent, EmotionalAgent
from utils.llm_client import invoke_llm
import logging
import re
from datetime import datetime

router = APIRouter(prefix="/tutoring", tags=["tutoring"])
logger = logging.getLogger(__name__)

profile_engine = ProfileEngine()
strategy_engine = StrategyEngine()
socratic_agent = SocraticAgent()
instructor_agent = InstructorAgent()
emotional_agent = EmotionalAgent()


class ChatRequest(BaseModel):
    student_id: str = "default"
    message: str
    mode: str = "direct"


class OnboardingRequest(BaseModel):
    student_id: str = "default"
    step: int = 0
    answer: str = ""


_ONBOARDING_QUESTIONS = [
    {
        "step": 1,
        "question": "你是什么专业的？",
        "field": "grade",
        "description": "用于了解你的知识背景",
    },
    {
        "step": 2,
        "question": "哪门课程让你最头疼？",
        "field": "weak_points",
        "description": "用于识别知识薄弱点",
    },
    {
        "step": 3,
        "question": "你更喜欢通过视频学习还是刷题练习？",
        "field": "cognitive_preference",
        "description": "用于匹配学习方式",
    },
    {
        "step": 4,
        "question": "最近一次考试成绩大概是多少分？",
        "field": "knowledge_mastery",
        "description": "用于评估知识掌握程度",
    },
]


_EMPTY_PHRASES = (
    "请提供一个具体的知识点",
    "请补充一个具体的薄弱知识点名称",
    "提供具体知识点",
    "请告诉我你具体想学习什么内容",
    "请告诉我具体想学习什么内容",
    "请选择具体学科和单元",
    "你可以从以下几个方向尝试",
    "建议从基础开始",
    "建议你先完成一份题目",
    "当前还未设置薄弱知识点",
    "你还没有选择薄弱知识点",
    "请先做一份题目来生成你的薄弱点",
    "请告诉我你想学习的学科",
    "暂时没有找到匹配的知识点",
)


def _llm_response_is_empty(text: str) -> bool:
    if not text or not text.strip():
        return True
    t = text.strip()
    if len(t) < 20:
        return True
    if any(p in t for p in _EMPTY_PHRASES):
        return True
    if re.search(r'(TODO|TBD|待定|未设置|\{response\})', t):
        return True
    return False


def _try_search_enhanced_answer(message: str, level_desc: str = "高中水平学生") -> dict:
    try:
        from agents.search_agent import search_agent
        from utils.llm_client import invoke_llm
    except Exception as e:
        logger.warning('search agent import failed: %s', e)
        return {"ok": False}

    try:
        sources = search_agent.gather(message, max_sources=3)
        if not sources:
            return {"ok": False, "reason": "no_sources"}
        prompt = search_agent.build_enhanced_prompt(message, sources, level_desc=level_desc)
        answer = invoke_llm(
            prompt=prompt,
            system_message=("你是一名经验丰富、讲课通俗易懂的一线中学/大学老师，擅长把复杂问题讲明白，"
                             "语气像老师在讲课，而不是机器。"),
        )
        return {"ok": True, "answer": answer, "sources": sources}
    except Exception as e:
        logger.warning('search-enhanced answer failed: %s', e)
        return {"ok": False, "reason": str(e)}


def _guess_level(profile) -> str:
    if not profile:
        return "高中水平学生"
    score = getattr(profile, 'knowledge_mastery', 60) or 60
    grade = getattr(profile, 'grade', '') or ''
    if '大' in str(grade) or 'college' in str(grade).lower():
        return "大学水平学生"
    if '初' in str(grade):
        return "初中水平学生"
    if score < 40:
        return "高中基础较弱学生"
    if score > 80:
        return "高中基础较好学生"
    return "高中水平学生"


def _build_decision_summary(profile, tutoring_mode: str) -> str:
    try:
        mastery = float(getattr(profile, "knowledge_mastery", 0) or 0)
        emotion = float(getattr(profile, "emotional_state", 50) or 50)
    except Exception:
        mastery, emotion = 50.0, 70.0

    if mastery < 40:
        return "基础较薄弱，使用苏格拉底引导帮你理清思路"
    if emotion < 40:
        return "情绪状态偏低，选择苏格拉底引导减轻压力"
    if tutoring_mode == "socratic":
        return "综合当前画像状态，采用苏格拉底引导逐步引导思考"
    return "综合当前画像状态，采用直接讲解高效推进"


def _convert_agent_traces(traces) -> list:
    out = []
    if not traces:
        return out
    for t in traces:
        if isinstance(t, dict):
            out.append({
                "agent_name": t.get("agent_name", "Agent"),
                "status": t.get("status", "completed"),
                "reasoning": t.get("reasoning", ""),
            })
        else:
            out.append({
                "agent_name": getattr(t, "agent_name", "Agent"),
                "status": getattr(t, "status", "completed"),
                "reasoning": getattr(t, "reasoning", ""),
            })
    return out


def _mode_label(mode: str) -> str:
    return "苏格拉底引导" if mode == "socratic" else "直接讲解"


def _strategy_mode_label(mode) -> str:
    try:
        return mode.value
    except Exception:
        return str(mode)


def _build_fallback_with_search_hint(question: str) -> str:
    try:
        from agents.search_agent import search_agent
        from utils.llm_client import invoke_llm
    except Exception:
        return _get_fallback_response(question)

    try:
        sources = search_agent.gather(question, max_sources=2)
        if not sources:
            return _get_fallback_response(question)
        summary_parts = []
        for s in sources[:2]:
            summary_parts.append(f"• 《{s.get('title','')}》: {s.get('snippet','')}")
        ref_block = '\n'.join(summary_parts)
        prompt = (
            f"学生问：「{question}」\n\n"
            f"联网检索到的线索：\n{ref_block}\n\n"
            f"请面向高中学生，用通俗易懂的话给一个清晰回答，含 1 句话结论 + 3 个要点 + 1 个小例子。"
        )
        try:
            answer = invoke_llm(prompt)
            return answer
        except Exception:
            pass
    except Exception as e:
        logger.warning('fallback search failed: %s', e)

    return _get_fallback_response(question)


def _get_fallback_response(question: str) -> str:
    question_lower = question.lower()

    if any(kw in question_lower for kw in ["数学", "计算", "方程", "函数"]):
        return """数学学习需要系统的方法！让我给你一些建议：

**1. 夯实基础**
- 熟练掌握基本概念和公式
- 理解公式的推导过程，而不只是死记硬背

**2. 多做练习**
- 从简单题开始，逐步增加难度
- 整理错题本，分析错误原因

**3. 掌握解题方法**
- 学会分析题目条件
- 掌握常用解题技巧

**4. 考试技巧**
- 先易后难，合理分配时间
- 认真检查，确保会做的题不丢分

如果你有具体的数学问题，欢迎继续问我！"""

    if any(kw in question_lower for kw in ["英语", "语法", "单词", "词汇"]):
        return """英语学习需要积累和方法！建议如下：

**1. 词汇积累**
- 每天背诵一定量的单词
- 使用词根词缀记忆法
- 在语境中学习单词

**2. 语法学习**
- 掌握基本句型结构
- 学习时态、语态等语法规则
- 通过例句理解语法点

**3. 听说读写**
- 多听英语材料
- 坚持阅读英文文章
- 练习写作表达

**4. 学习资源**
- 使用英语学习APP
- 观看英文视频
- 与他人用英语交流

有具体的英语问题吗？"""

    if any(kw in question_lower for kw in ["计划", "安排", "学习计划"]):
        return """制定学习计划需要考虑以下几个方面：

**1. 明确目标**
- 确定短期和长期学习目标
- 目标要具体、可衡量

**2. 分析现状**
- 评估当前知识水平
- 识别薄弱知识点

**3. 合理安排时间**
- 制定每日/每周学习计划
- 分配时间给不同科目
- 留出复习和休息时间

**4. 执行与调整**
- 坚持执行计划
- 定期评估效果
- 根据实际情况调整

我可以帮你制定个性化的学习计划，需要了解更多关于你的学习情况！"""

    return """你好！我是你的智能学习助手。

我可以帮助你：
- 解答各学科的学习问题
- 分析知识薄弱点
- 提供学习方法和技巧
- 制定学习计划

请告诉我你具体想学习什么内容？"""


@router.post("/chat")
async def chat(req: ChatRequest):
    profile = profile_engine.get_profile(req.student_id)
    if not profile:
        profile = profile_engine.create_profile(student_id=req.student_id)

    tutoring_mode_obj = TutoringMode(req.mode)
    tutoring_mode = req.mode

    state: MagicStudyState = {
        "user_message": req.message,
        "conversation_history": [],
        "profile": profile,
        "tutoring_mode": tutoring_mode_obj,
        "hints": [],
        "current_hint_index": 0,
        "agent_traces": [],
    }

    use_graph = True
    graph_exception = None
    try:
        result = learning_graph.invoke(state)
    except Exception as e:
        logger.error('learning_graph.invoke failed: %s', e)
        graph_exception = e
        use_graph = False
        if tutoring_mode_obj == TutoringMode.SOCRATIC:
            result = socratic_agent(state)
        else:
            result = instructor_agent(state)
        result = emotional_agent(result)
        traces = [{"agent_name": "direct", "status": "completed", "reasoning": "fallback: graph invoke failed"}]
        workflow_pipeline = ["direct"]

    if use_graph:
        traces = _convert_agent_traces(result.get("agent_traces", []))
        workflow_pipeline = ["diagnose", "plan", "instruct", "train", "review", "explain", "emotional"]
        if tutoring_mode == "socratic":
            workflow_pipeline.append("socratic")

    profile_engine.auto_snapshot_if_needed(req.student_id)

    response_text = (result.get("tutoring_response", "") or
                     result.get("final_response", "") or
                     result.get("workflow_explanation", ""))

    if _llm_response_is_empty(response_text):
        logger.info('本地回答为空/泛泛而谈，尝试联网搜索增强：%s', req.message[:60])
        level_desc = _guess_level(profile)
        search_answer = _try_search_enhanced_answer(req.message, level_desc=level_desc)
        if search_answer.get("ok"):
            response_text = search_answer["answer"]
            sources = search_answer.get("sources", [])
            if sources and '来源：' not in response_text:
                refs = '、'.join(f'《{s.get("title","")}》' for s in sources[:3])
                response_text += f"\n\n> （已结合网络资料整理，主要来源：{refs}）"
        else:
            response_text = _build_fallback_with_search_hint(req.message)

    try:
        strategy_mode_obj = strategy_engine.recommend_strategy(profile)
    except Exception:
        strategy_mode_obj = "balanced"

    try:
        learning_state = profile_engine.serialize_profile(profile)
    except Exception:
        learning_state = {}

    return {
        "status": "success",
        "response": response_text,
        "emotional_feedback": result.get("emotional_feedback", ""),
        "mode": tutoring_mode,
        "learning_state": learning_state,
        "tutoring_mode": tutoring_mode,
        "mode_label": _mode_label(tutoring_mode),
        "strategy_mode": _strategy_mode_label(strategy_mode_obj),
        "agent_traces": traces,
        "workflow_pipeline": workflow_pipeline,
        "decision_summary": _build_decision_summary(profile, tutoring_mode),
    }


@router.get("/state/{student_id}")
async def get_state(student_id: str):
    profile = profile_engine.get_profile(student_id)
    if not profile:
        profile = profile_engine.create_profile(student_id=student_id)

    try:
        strategy_mode_obj = strategy_engine.recommend_strategy(profile)
    except Exception:
        strategy_mode_obj = "balanced"

    try:
        profile_dict = profile_engine.serialize_profile(profile)
    except Exception:
        profile_dict = {}

    return {
        "status": "success",
        "learning_state": profile_dict,
        "strategy_mode": _strategy_mode_label(strategy_mode_obj),
        "weak_points": getattr(profile, "weak_points", []),
        "knowledge_mastery": getattr(profile, "knowledge_mastery", 0),
        "learning_stability": getattr(profile, "learning_stability", 0),
        "response_speed": getattr(profile, "response_speed", 0),
        "emotional_state": getattr(profile, "emotional_state", 0),
        "self_driven_score": getattr(profile, "self_driven_score", 0),
        "transfer_ability": getattr(profile, "transfer_ability", 0),
        "cognitive_preference": getattr(profile, "cognitive_preference", ""),
        "grade": getattr(profile, "grade", ""),
        "subject": getattr(profile, "subject", ""),
        "subjects": getattr(profile, "subjects", []),
        "learning_goal": getattr(profile, "learning_goal", ""),
        "last_updated": profile.last_updated.isoformat() if getattr(profile, "last_updated", None) else None,
    }


@router.post("/next-hint")
async def next_hint(student_id: str):
    profile = profile_engine.get_profile(student_id)
    if not profile:
        return {"status": "error", "message": "Profile not found"}

    state: MagicStudyState = {
        "user_message": "",
        "profile": profile,
        "tutoring_mode": TutoringMode.SOCRATIC,
        "hints": [],
        "current_hint_index": 0,
        "agent_traces": [],
    }

    result = socratic_agent(state)

    return {
        "status": "success",
        "hint": result.get("tutoring_response", ""),
        "hint_index": result.get("current_hint_index", 0),
        "total_hints": len(result.get("hints", []))
    }


@router.post("/switch-mode")
async def switch_mode(student_id: str, mode: str):
    return {
        "status": "success",
        "message": f"已切换到{'苏格拉底引导' if mode == 'socratic' else '直接讲解'}模式",
        "mode": mode
    }


@router.get("/onboarding/questions")
async def get_onboarding_questions():
    return {
        "status": "success",
        "questions": _ONBOARDING_QUESTIONS,
        "total_steps": len(_ONBOARDING_QUESTIONS),
    }


@router.post("/onboarding/next")
async def next_onboarding_step(req: OnboardingRequest):
    profile = profile_engine.get_profile(req.student_id)
    if not profile:
        profile = LearningProfile(student_id=req.student_id)
    
    updates = []
    
    if req.step > 0 and req.answer:
        prev_question = next((q for q in _ONBOARDING_QUESTIONS if q["step"] == req.step), None)
        if prev_question:
            field = prev_question["field"]
            if field == "weak_points":
                profile.weak_points = [req.answer.strip()]
            elif field == "cognitive_preference":
                if "视频" in req.answer:
                    profile.cognitive_preference = "visual"
                elif "刷题" in req.answer or "练习" in req.answer:
                    profile.cognitive_preference = "practice"
                else:
                    profile.cognitive_preference = "visual"
            elif field == "knowledge_mastery":
                try:
                    score = int(req.answer.strip())
                    profile.knowledge_mastery = min(max(score, 0), 100)
                except:
                    profile.knowledge_mastery = 60
            elif field == "grade":
                profile.grade = req.answer.strip()
            
            updates.append({
                "step": req.step,
                "question": prev_question["question"],
                "answer": req.answer,
                "field": field,
                "timestamp": datetime.now().isoformat(),
            })
    
    next_step = req.step + 1
    if next_step > len(_ONBOARDING_QUESTIONS):
        profile.last_updated = datetime.now()
        profile.update_history.extend(updates)
        profile_engine.save_profile(profile)
        
        return {
            "status": "completed",
            "message": "恭喜！画像构建完成，现在可以开始学习了",
            "step": next_step,
            "total_steps": len(_ONBOARDING_QUESTIONS),
            "profile": profile_engine.serialize_profile(profile),
            "updates": updates,
        }
    
    next_question = next((q for q in _ONBOARDING_QUESTIONS if q["step"] == next_step), None)
    
    return {
        "status": "success",
        "step": next_step,
        "total_steps": len(_ONBOARDING_QUESTIONS),
        "question": next_question["question"],
        "field": next_question["field"],
        "description": next_question["description"],
        "updates": updates,
    }


@router.post("/onboarding/complete")
async def complete_onboarding(student_id: str, answers: dict = None):
    profile = profile_engine.get_profile(student_id)
    if not profile:
        profile = LearningProfile(student_id=student_id)
    
    updates = []
    
    if answers:
        for step, answer in answers.items():
            try:
                step_num = int(step)
                question = next((q for q in _ONBOARDING_QUESTIONS if q["step"] == step_num), None)
                if question and answer:
                    field = question["field"]
                    if field == "weak_points":
                        profile.weak_points = [answer.strip()]
                    elif field == "cognitive_preference":
                        if "视频" in answer:
                            profile.cognitive_preference = "visual"
                        else:
                            profile.cognitive_preference = "practice"
                    elif field == "knowledge_mastery":
                        try:
                            profile.knowledge_mastery = int(answer.strip())
                        except:
                            profile.knowledge_mastery = 60
                    elif field == "grade":
                        profile.grade = answer.strip()
                    
                    updates.append({
                        "step": step_num,
                        "question": question["question"],
                        "answer": answer,
                        "field": field,
                        "timestamp": datetime.now().isoformat(),
                    })
            except:
                pass
    
    profile.last_updated = datetime.now()
    profile.update_history.extend(updates)
    profile_engine.save_profile(profile)
    
    return {
        "status": "success",
        "message": "画像构建完成！",
        "profile": profile_engine.serialize_profile(profile),
        "update_history": updates,
    }


@router.get("/onboarding/status/{student_id}")
async def get_onboarding_status(student_id: str):
    profile = profile_engine.get_profile(student_id)
    if not profile:
        return {
            "status": "not_started",
            "current_step": 0,
            "total_steps": len(_ONBOARDING_QUESTIONS),
        }
    
    history = getattr(profile, "update_history", [])
    completed_steps = len(history)
    
    if completed_steps >= len(_ONBOARDING_QUESTIONS):
        return {
            "status": "completed",
            "current_step": len(_ONBOARDING_QUESTIONS),
            "total_steps": len(_ONBOARDING_QUESTIONS),
            "update_history": history,
        }
    
    return {
        "status": "in_progress",
        "current_step": completed_steps,
        "total_steps": len(_ONBOARDING_QUESTIONS),
        "next_question": _ONBOARDING_QUESTIONS[completed_steps]["question"],
        "update_history": history,
    }
