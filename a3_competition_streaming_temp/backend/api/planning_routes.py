from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from engines import ProfileEngine, StrategyEngine
from graph.state import StrategyMode, LearningProfile
from database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/planning", tags=["planning"])

profile_engine = ProfileEngine()
strategy_engine = StrategyEngine()


class GeneratePlanRequest(BaseModel):
    student_id: str
    strategy_mode: str = "balanced"
    weak_points: list[str] = []
    target_score: int = 0
    exam_period: str = ""
    subject: str = ""


@router.post("/recommend")
async def recommend_strategy(student_id: str):
    profile = profile_engine.get_profile(student_id)
    if not profile:
        return {"status": "error", "message": "Profile not found"}

    strategy = strategy_engine.recommend_strategy(profile)
    return {"status": "success", "strategy": strategy.value}


@router.post("/generate-plan")
async def generate_plan(req: GeneratePlanRequest, db: Session = Depends(get_db)):
    from models.database_models import StudentProfile, KnowledgeNode

    profile = db.query(StudentProfile).filter(StudentProfile.student_id == int(req.student_id)).first()
    
    weak_points = []
    if profile:
        if req.weak_points:
            weak_points = req.weak_points
        else:
            try:
                import json
                if profile.knowledge_states:
                    states = json.loads(profile.knowledge_states)
                    weak_points = [k for k, v in states.items() if v.get('mastery', 1) < 0.6]
            except:
                pass

        if profile.weak_points:
            try:
                import json
                weak_points.extend(json.loads(profile.weak_points))
            except:
                pass

    if not weak_points:
        weak_points = ["一元二次方程", "几何证明", "函数应用"]

    if req.subject:
        subject_name = req.subject
    elif profile and profile.subjects:
        try:
            import json
            subjects = json.loads(profile.subjects)
            subject_name = subjects[0] if subjects else "数学"
        except:
            subject_name = "数学"
    else:
        subject_name = "数学"

    task_type_names = {
        "lecture": "视频讲解",
        "exercise": "强化练习",
        "review": "知识回顾",
        "quiz": "模拟测验",
        "practice": "实战训练"
    }

    subject_tasks = {
        "数学": [
            {"title": "一元二次方程求根公式", "desc": "掌握配方法和公式法，理解判别式意义"},
            {"title": "二次函数图像与性质", "desc": "掌握抛物线开口方向、顶点坐标、对称轴"},
            {"title": "几何证明题技巧", "desc": "学习辅助线添加方法，掌握全等三角形判定"},
            {"title": "勾股定理应用", "desc": "掌握勾股定理及其逆定理，解决实际问题"},
            {"title": "一次函数与反比例函数", "desc": "理解函数概念，掌握图像变换"},
            {"title": "三角函数基础", "desc": "掌握正弦、余弦、正切定义及特殊角值"},
            {"title": "概率与统计", "desc": "理解概率计算，掌握统计图分析"},
            {"title": "数列求和", "desc": "掌握等差数列、等比数列求和公式"}
        ],
        "英语": [
            {"title": "词汇记忆技巧", "desc": "掌握词根词缀记忆法，扩大词汇量"},
            {"title": "语法时态复习", "desc": "复习一般现在时、过去时、将来时用法"},
            {"title": "阅读理解技巧", "desc": "学习快速阅读和细节定位方法"},
            {"title": "完形填空策略", "desc": "掌握上下文推理和词汇辨析"},
            {"title": "写作句型模板", "desc": "积累常用句型和连接词"}
        ],
        "语文": [
            {"title": "文言文实词虚词", "desc": "掌握常见实词虚词用法"},
            {"title": "现代文阅读分析", "desc": "学习概括主旨和分析表达技巧"},
            {"title": "古诗词鉴赏", "desc": "理解意境和情感表达"},
            {"title": "作文写作技巧", "desc": "掌握议论文结构和素材运用"}
        ],
        "物理": [
            {"title": "牛顿运动定律", "desc": "理解惯性、加速度、作用力与反作用力"},
            {"title": "机械能守恒", "desc": "掌握动能定理和势能转化"},
            {"title": "电路分析", "desc": "理解欧姆定律和串并联电路"}
        ],
        "化学": [
            {"title": "化学方程式配平", "desc": "掌握配平方法和氧化还原反应"},
            {"title": "元素周期律", "desc": "理解原子结构和元素性质递变"},
            {"title": "溶液浓度计算", "desc": "掌握质量分数和物质的量浓度"}
        ]
    }

    tasks_list = subject_tasks.get(subject_name, subject_tasks["数学"])
    tasks_list = [t for t in tasks_list if any(w in t["title"] for w in weak_points)]
    
    if not tasks_list:
        tasks_list = subject_tasks.get(subject_name, subject_tasks["数学"])

    tasks = []
    num_tasks = min(5, len(tasks_list))
    for i in range(num_tasks):
        task_info = tasks_list[i]
        task_types = ["lecture", "exercise", "review", "quiz", "practice"]
        task_type = task_types[i % 5]
        
        tasks.append({
            "task_id": f"task_{i}",
            "title": f"{task_type_names[task_type]}: {task_info['title']}",
            "task_type": task_type,
            "difficulty": min(0.9, 0.3 + i * 0.15),
            "estimated_minutes": 25 + i * 8,
            "expected_gain": max(0.05, 0.15 - i * 0.02),
            "explanation": task_info["desc"],
            "knowledge_point": task_info["title"],
            "subject": subject_name
        })

    return {
        "status": "success",
        "strategy": req.strategy_mode,
        "tasks": tasks,
        "explanation": f"根据您的{subject_name}学习需求和薄弱点{', '.join(weak_points[:3])}，已为您生成个性化学习计划"
    }


@router.post("/adjust-plan")
async def adjust_plan(student_id: str, task_results: list[dict]):
    profile = profile_engine.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    weak_points = [
        kid for kid, ks in profile.knowledge_states.items()
        if ks.mastery < 0.6
    ]

    strategy = strategy_engine.recommend_strategy(profile)
    tasks = strategy_engine.generate_learning_path(profile, weak_points, strategy)

    from engines.adaptive_engine import AdaptiveEngine
    adaptive_engine = AdaptiveEngine()
    adjusted_tasks = adaptive_engine.adjust_task_sequence(profile, tasks, task_results)

    return {
        "status": "success",
        "adjusted_tasks": [
            {
                "task_id": t.task_id,
                "title": t.title,
                "difficulty": t.difficulty,
                "expected_gain": t.expected_gain
            }
            for t in adjusted_tasks
        ]
    }