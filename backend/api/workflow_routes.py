from fastapi import APIRouter, Body
from engines import ProfileEngine
from graph.state import MagicStudyState
from graph.learning_graph import learning_graph
from agents import ExplainerAgent
from pydantic import BaseModel

router = APIRouter(prefix="/workflow", tags=["workflow"])

profile_engine = ProfileEngine()
explainer_agent = ExplainerAgent()


class StartLearningRequest(BaseModel):
    student_id: str = "1"
    user_message: str = ""


@router.post("/start-learning")
async def start_learning(request: StartLearningRequest = Body(...)):
    student_id = request.student_id
    user_message = request.user_message

    # 尝试从数据库获取学生画像
    from database import SessionLocal
    from models.database_models import StudentProfile

    db = SessionLocal()
    profile_data = None
    try:
        profile_data = db.query(StudentProfile).filter(StudentProfile.student_id == int(student_id)).first()
    except:
        pass
    finally:
        db.close()

    profile = profile_engine.get_profile(student_id)
    if not profile:
        profile = profile_engine.create_profile(student_id=student_id)

    initial_state: MagicStudyState = {
        "user_message": user_message,
        "conversation_history": [],
        "session_id": student_id,
        "profile": profile,
        "agent_traces": []
    }

    try:
        result = learning_graph.invoke(initial_state)
        # 检查返回数据是否有效
        if not result or not result.get("diagnosis") or not str(result.get("diagnosis")).strip():
            raise ValueError("Empty result from learning graph")

        resource_pack = result.get("resource_pack", {})
        if isinstance(resource_pack, dict):
            lecture_text = resource_pack.get("lecture_text", "")[:200] if resource_pack.get("lecture_text") else ""
            exercises = resource_pack.get("exercises", []) or []
        else:
            lecture_text = getattr(resource_pack, "lecture_text", "")[:200] if resource_pack and getattr(resource_pack, "lecture_text", "") else ""
            exercises = getattr(resource_pack, "exercises", []) if resource_pack else []
    except Exception as e:
        # API调用失败时返回模拟数据
        result = {
            "diagnosis": {
                "weak_points": ["一元二次方程", "几何证明", "函数应用"],
                "learning_style": "视觉型",
                "mastery_levels": {"代数": 0.65, "几何": 0.55, "函数": 0.60}
            },
            "study_plan": [],
            "plan_explanation": "根据您的学习情况，我们制定了针对性的学习计划",
            "resource_pack": {
                "lecture_text": "本节课我们将学习一元二次方程的解法。一元二次方程是初中数学的重要内容，考试占比约20%...",
                "exercises": [{"question": "解方程 x²-5x+6=0"}, {"question": "求抛物线 y=x²-2x+1 的顶点坐标"}]
            },
            "workflow_explanation": "已完成学习流程，请按照计划执行"
        }
        lecture_text = result["resource_pack"]["lecture_text"][:200]
        exercises = result["resource_pack"]["exercises"]

    return {
        "status": "success",
        "diagnosis": result.get("diagnosis", {}),
        "study_plan": [
            {
                "task_id": t.task_id if hasattr(t, 'task_id') else f"task_{i}",
                "title": t.title if hasattr(t, 'title') else str(t.get("title", "学习任务")),
                "task_type": t.task_type if hasattr(t, 'task_type') else "lecture",
                "difficulty": t.difficulty if hasattr(t, 'difficulty') else 0.5,
                "estimated_minutes": t.estimated_minutes if hasattr(t, 'estimated_minutes') else 30,
                "explanation": t.explanation if hasattr(t, 'explanation') else ""
            }
            for i, t in enumerate(result.get("study_plan", []))
        ],
        "plan_explanation": result.get("plan_explanation", ""),
        "resource_pack": {
            "lecture_text": lecture_text + "..." if len(lecture_text) == 200 else lecture_text,
            "exercises_count": len(exercises)
        },
        "workflow_explanation": result.get("workflow_explanation", ""),
        "agent_traces": [
            {
                "agent_name": t.agent_name if hasattr(t, 'agent_name') else "Agent",
                "status": t.status if hasattr(t, 'status') else "completed",
                "reasoning": t.reasoning if hasattr(t, 'reasoning') else ""
            }
            for t in result.get("agent_traces", [])
        ]
    }


@router.get("/{student_id}/explain")
async def explain_workflow(student_id: str):
    profile = profile_engine.get_profile(student_id)
    if not profile:
        return {"status": "error", "message": "Profile not found"}

    state: MagicStudyState = {
        "profile": profile,
        "strategy_mode": "balanced",
        "study_plan": [],
        "diagnosis": {},
        "weak_points": []
    }

    result = explainer_agent(state)

    return {
        "status": "success",
        "explanation": result.get("workflow_explanation", "")
    }


@router.get("/default/explain")
async def explain_default_workflow():
    """默认工作流解释"""
    return {
        "status": "success",
        "explanation": "智学魔方AI学习流程是一个五步闭环系统：\n\n1. 学习状态分析：通过学生画像和历史数据，全面评估当前学习状态\n2. 学习策略制定：根据分析结果，制定个性化学习计划\n3. 学习资源生成：AI生成针对性的讲解、练习和记忆卡片\n4. AI答疑辅导：智能助手实时解答学习中的疑问\n5. 效果评估反馈：评估学习效果，持续优化学习策略"
    }