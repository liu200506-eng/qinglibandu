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
    from models.database_models import StudentProfile, KnowledgeNode, Subject

    profile = db.query(StudentProfile).filter(StudentProfile.student_id == int(req.student_id)).first()
    
    if req.subject:
        subject_name = req.subject
    elif profile and profile.subjects:
        try:
            import json
            subjects = json.loads(profile.subjects)
            subject_name = subjects[0] if subjects else "计算机网络"
        except:
            subject_name = "计算机网络"
    else:
        subject_name = "计算机网络"

    subject = db.query(Subject).filter(Subject.name == subject_name).first()
    if not subject:
        subject = db.query(Subject).filter(Subject.name == "计算机网络").first()
        if subject:
            subject_name = "计算机网络"

    all_knowledge_nodes = []
    if subject:
        all_knowledge_nodes = db.query(KnowledgeNode).filter(
            KnowledgeNode.subject_id == subject.id
        ).all()

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

    if not weak_points and all_knowledge_nodes:
        weak_points = [n.name for n in sorted(all_knowledge_nodes, key=lambda x: x.mastery)[:5]]
    elif not weak_points:
        weak_points = ["TCP", "UDP", "HTTP", "IP协议", "路由协议"]

    weak_points = list(set(weak_points))[:10]

    task_type_names = {
        "lecture": "视频讲解",
        "exercise": "强化练习",
        "review": "知识回顾",
        "quiz": "模拟测验",
        "practice": "实战训练",
        "flashcard": "闪卡记忆"
    }

    subject_task_templates = {
        "计算机网络": {
            "TCP": {
                "title": "TCP协议详解",
                "desc": "深入理解TCP三次握手、四次挥手、滑动窗口、拥塞控制等核心机制",
                "tasks": [
                    {"type": "lecture", "title": "TCP连接管理", "desc": "三次握手与四次挥手的完整过程"},
                    {"type": "lecture", "title": "TCP可靠传输", "desc": "滑动窗口、累计确认、超时重传"},
                    {"type": "lecture", "title": "TCP拥塞控制", "desc": "慢启动、拥塞避免、快重传、快恢复"},
                    {"type": "exercise", "title": "TCP习题演练", "desc": "MSS计算、RTT分析、拥塞窗口变化"},
                    {"type": "flashcard", "title": "TCP核心概念", "desc": "通过闪卡快速记忆关键公式和流程"}
                ]
            },
            "UDP": {
                "title": "UDP协议详解",
                "desc": "理解UDP无连接特性、适用场景、与TCP的对比",
                "tasks": [
                    {"type": "lecture", "title": "UDP基础特性", "desc": "无连接、不可靠、低延迟"},
                    {"type": "lecture", "title": "UDP应用场景", "desc": "DNS、视频通话、实时游戏"},
                    {"type": "exercise", "title": "TCP vs UDP对比", "desc": "分析不同场景下的协议选择"},
                    {"type": "flashcard", "title": "UDP关键要点", "desc": "闪卡记忆UDP特点和适用场景"}
                ]
            },
            "HTTP": {
                "title": "HTTP协议详解",
                "desc": "掌握HTTP请求响应流程、状态码、缓存机制、HTTPS",
                "tasks": [
                    {"type": "lecture", "title": "HTTP请求响应", "desc": "请求方法、状态码、报文结构"},
                    {"type": "lecture", "title": "HTTP缓存机制", "desc": "Cache-Control、ETag、Last-Modified"},
                    {"type": "lecture", "title": "HTTPS原理", "desc": "SSL/TLS握手、证书验证"},
                    {"type": "exercise", "title": "HTTP实战分析", "desc": "抓包分析、状态码判断"},
                    {"type": "flashcard", "title": "HTTP核心概念", "desc": "闪卡记忆常用状态码和请求方法"}
                ]
            },
            "IP协议": {
                "title": "IP协议详解",
                "desc": "掌握IP地址、子网划分、路由选择、NAT等核心概念",
                "tasks": [
                    {"type": "lecture", "title": "IP地址与子网", "desc": "IPv4地址结构、子网掩码、CIDR"},
                    {"type": "lecture", "title": "IP路由", "desc": "路由表、最长前缀匹配"},
                    {"type": "lecture", "title": "NAT技术", "desc": "网络地址转换、端口映射"},
                    {"type": "exercise", "title": "IP地址计算", "desc": "子网划分、广播地址计算"},
                    {"type": "flashcard", "title": "IP核心概念", "desc": "闪卡记忆地址分类和路由规则"}
                ]
            },
            "路由协议": {
                "title": "路由协议详解",
                "desc": "理解RIP、OSPF、BGP等路由协议的原理和应用",
                "tasks": [
                    {"type": "lecture", "title": "距离矢量路由", "desc": "RIP协议原理和收敛"},
                    {"type": "lecture", "title": "链路状态路由", "desc": "OSPF协议、SPF算法"},
                    {"type": "lecture", "title": "边界网关协议", "desc": "BGP在互联网中的应用"},
                    {"type": "exercise", "title": "路由配置练习", "desc": "静态路由、动态路由配置"},
                    {"type": "flashcard", "title": "路由协议要点", "desc": "闪卡记忆各协议特点"}
                ]
            },
            "数据链路层": {
                "title": "数据链路层详解",
                "desc": "掌握帧结构、CRC校验、MAC地址、以太网协议",
                "tasks": [
                    {"type": "lecture", "title": "帧与差错检测", "desc": "CRC校验、奇偶校验"},
                    {"type": "lecture", "title": "以太网技术", "desc": "CSMA/CD、MAC地址、交换机"},
                    {"type": "exercise", "title": "以太网分析", "desc": "帧格式分析、碰撞检测"},
                    {"type": "flashcard", "title": "数据链路层要点", "desc": "闪卡记忆关键概念"}
                ]
            },
            "网络安全": {
                "title": "网络安全基础",
                "desc": "理解加密算法、认证机制、SSL/TLS、VPN等安全技术",
                "tasks": [
                    {"type": "lecture", "title": "加密与解密", "desc": "对称加密、非对称加密、哈希函数"},
                    {"type": "lecture", "title": "SSL/TLS协议", "desc": "证书体系、握手过程"},
                    {"type": "lecture", "title": "VPN技术", "desc": "IPsec、SSL VPN"},
                    {"type": "exercise", "title": "安全协议分析", "desc": "HTTPS抓包分析"},
                    {"type": "flashcard", "title": "网络安全要点", "desc": "闪卡记忆安全协议特点"}
                ]
            },
            "OSI/RM、TCP/IP": {
                "title": "网络体系结构",
                "desc": "理解OSI七层模型和TCP/IP四层模型的对应关系",
                "tasks": [
                    {"type": "lecture", "title": "OSI七层模型", "desc": "各层功能和协议"},
                    {"type": "lecture", "title": "TCP/IP模型", "desc": "与OSI的对应关系"},
                    {"type": "exercise", "title": "分层分析", "desc": "数据在各层的封装过程"},
                    {"type": "flashcard", "title": "网络模型要点", "desc": "闪卡记忆各层功能"}
                ]
            },
            "DNS": {
                "title": "DNS域名系统",
                "desc": "掌握DNS解析过程、域名结构、缓存机制",
                "tasks": [
                    {"type": "lecture", "title": "DNS解析流程", "desc": "递归查询、迭代查询"},
                    {"type": "lecture", "title": "DNS记录类型", "desc": "A、AAAA、CNAME、MX记录"},
                    {"type": "exercise", "title": "DNS配置", "desc": "域名解析配置和调试"},
                    {"type": "flashcard", "title": "DNS要点", "desc": "闪卡记忆DNS解析过程"}
                ]
            },
            "TLS/SSL": {
                "title": "SSL/TLS协议",
                "desc": "深入理解SSL/TLS握手过程、证书验证、加密套件",
                "tasks": [
                    {"type": "lecture", "title": "TLS握手", "desc": "完整的TLS1.2/TLS1.3握手过程"},
                    {"type": "lecture", "title": "证书体系", "desc": "CA、证书链、证书验证"},
                    {"type": "exercise", "title": "TLS分析", "desc": "抓包分析TLS握手"},
                    {"type": "flashcard", "title": "TLS要点", "desc": "闪卡记忆握手流程"}
                ]
            }
        },
        "数学": {
            "一元二次方程": {
                "title": "一元二次方程求根公式",
                "desc": "掌握配方法和公式法，理解判别式意义",
                "tasks": [
                    {"type": "lecture", "title": "配方法推导", "desc": "从一般式到配方式的转化"},
                    {"type": "lecture", "title": "求根公式", "desc": "判别式与根的关系"},
                    {"type": "exercise", "title": "方程求解", "desc": "各类方程求解练习"},
                    {"type": "flashcard", "title": "公式记忆", "desc": "闪卡记忆求根公式"}
                ]
            },
            "二次函数": {
                "title": "二次函数图像与性质",
                "desc": "掌握抛物线开口方向、顶点坐标、对称轴",
                "tasks": [
                    {"type": "lecture", "title": "函数图像", "desc": "开口方向、顶点、对称轴"},
                    {"type": "lecture", "title": "解析式", "desc": "一般式、顶点式、交点式"},
                    {"type": "exercise", "title": "图像分析", "desc": "根据解析式画图"},
                    {"type": "flashcard", "title": "性质要点", "desc": "闪卡记忆函数性质"}
                ]
            },
            "几何证明": {
                "title": "几何证明题技巧",
                "desc": "学习辅助线添加方法，掌握全等三角形判定",
                "tasks": [
                    {"type": "lecture", "title": "辅助线添加", "desc": "常用辅助线类型"},
                    {"type": "lecture", "title": "全等判定", "desc": "SSS、SAS、ASA、AAS、HL"},
                    {"type": "exercise", "title": "证明练习", "desc": "综合证明题"},
                    {"type": "flashcard", "title": "判定定理", "desc": "闪卡记忆判定条件"}
                ]
            },
            "三角函数": {
                "title": "三角函数基础",
                "desc": "掌握正弦、余弦、正切定义及特殊角值",
                "tasks": [
                    {"type": "lecture", "title": "三角函数定义", "desc": "单位圆与三角函数"},
                    {"type": "lecture", "title": "特殊角", "desc": "30°、45°、60°的三角函数值"},
                    {"type": "exercise", "title": "三角计算", "desc": "三角函数求值练习"},
                    {"type": "flashcard", "title": "特殊角值", "desc": "闪卡记忆特殊角三角函数"}
                ]
            },
            "数列": {
                "title": "数列求和",
                "desc": "掌握等差数列、等比数列求和公式",
                "tasks": [
                    {"type": "lecture", "title": "等差数列", "desc": "通项公式、求和公式"},
                    {"type": "lecture", "title": "等比数列", "desc": "通项公式、求和公式"},
                    {"type": "exercise", "title": "数列计算", "desc": "各类数列求和"},
                    {"type": "flashcard", "title": "求和公式", "desc": "闪卡记忆求和公式"}
                ]
            }
        },
        "英语": {
            "词汇": {
                "title": "词汇记忆技巧",
                "desc": "掌握词根词缀记忆法，扩大词汇量",
                "tasks": [
                    {"type": "lecture", "title": "词根词缀", "desc": "常见词根词缀及含义"},
                    {"type": "exercise", "title": "词汇练习", "desc": "根据词根词缀猜词义"},
                    {"type": "flashcard", "title": "词汇记忆", "desc": "闪卡记忆高频词汇"}
                ]
            },
            "语法": {
                "title": "语法时态复习",
                "desc": "复习一般现在时、过去时、将来时用法",
                "tasks": [
                    {"type": "lecture", "title": "时态用法", "desc": "各种时态的用法和标志词"},
                    {"type": "exercise", "title": "时态填空", "desc": "时态填空练习"},
                    {"type": "flashcard", "title": "时态要点", "desc": "闪卡记忆时态规则"}
                ]
            },
            "阅读": {
                "title": "阅读理解技巧",
                "desc": "学习快速阅读和细节定位方法",
                "tasks": [
                    {"type": "lecture", "title": "阅读技巧", "desc": "略读、寻读、推断"},
                    {"type": "exercise", "title": "阅读练习", "desc": "篇章阅读训练"},
                    {"type": "flashcard", "title": "题型要点", "desc": "闪卡记忆题型技巧"}
                ]
            }
        },
        "物理": {
            "力学": {
                "title": "牛顿运动定律",
                "desc": "理解惯性、加速度、作用力与反作用力",
                "tasks": [
                    {"type": "lecture", "title": "三大定律", "desc": "惯性定律、加速度定律、作用反作用"},
                    {"type": "exercise", "title": "力学计算", "desc": "各类力学题求解"},
                    {"type": "flashcard", "title": "定律要点", "desc": "闪卡记忆定律内容"}
                ]
            },
            "能量": {
                "title": "机械能守恒",
                "desc": "掌握动能定理和势能转化",
                "tasks": [
                    {"type": "lecture", "title": "动能定理", "desc": "合外力做功与动能变化"},
                    {"type": "lecture", "title": "势能转化", "desc": "重力势能、弹性势能"},
                    {"type": "exercise", "title": "能量计算", "desc": "能量守恒应用"},
                    {"type": "flashcard", "title": "能量公式", "desc": "闪卡记忆公式"}
                ]
            }
        },
        "化学": {
            "方程式": {
                "title": "化学方程式配平",
                "desc": "掌握配平方法和氧化还原反应",
                "tasks": [
                    {"type": "lecture", "title": "配平方法", "desc": "最小公倍数法、奇偶法"},
                    {"type": "exercise", "title": "配平练习", "desc": "各类方程式配平"},
                    {"type": "flashcard", "title": "配平要点", "desc": "闪卡记忆方法"}
                ]
            },
            "周期律": {
                "title": "元素周期律",
                "desc": "理解原子结构和元素性质递变",
                "tasks": [
                    {"type": "lecture", "title": "周期表结构", "desc": "周期、族、分区"},
                    {"type": "exercise", "title": "性质推断", "desc": "根据位置推断性质"},
                    {"type": "flashcard", "title": "周期律要点", "desc": "闪卡记忆递变规律"}
                ]
            }
        }
    }

    templates = subject_task_templates.get(subject_name, subject_task_templates["计算机网络"])

    tasks = []
    task_id_counter = 0
    weak_point_info = {}
    
    for wp in weak_points:
        matched_template = None
        for template_key, template_value in templates.items():
            if wp in template_key or template_key in wp:
                matched_template = template_value
                break
        
        if matched_template:
            weak_point_info[wp] = matched_template
            for j, subtask in enumerate(matched_template.get("tasks", [])):
                tasks.append({
                    "task_id": f"task_{task_id_counter}",
                    "title": f"{task_type_names.get(subtask['type'], '学习')}: {subtask['title']}",
                    "task_type": subtask['type'],
                    "knowledge_points": [wp],
                    "difficulty": min(0.9, 0.3 + task_id_counter * 0.08),
                    "estimated_minutes": 15 + task_id_counter * 5,
                    "expected_gain": max(0.05, 0.2 - task_id_counter * 0.02),
                    "status": "pending",
                    "priority": task_id_counter,
                    "explanation": subtask['desc']
                })
                task_id_counter += 1
        else:
            task_types = ["lecture", "exercise", "flashcard"]
            for j, task_type in enumerate(task_types):
                tasks.append({
                    "task_id": f"task_{task_id_counter}",
                    "title": f"{task_type_names.get(task_type, '学习')}: {wp}",
                    "task_type": task_type,
                    "knowledge_points": [wp],
                    "difficulty": min(0.9, 0.4 + task_id_counter * 0.05),
                    "estimated_minutes": 20 + task_id_counter * 3,
                    "expected_gain": max(0.05, 0.15 - task_id_counter * 0.01),
                    "status": "pending",
                    "priority": task_id_counter,
                    "explanation": f"针对薄弱点'{wp}'进行{task_type_names.get(task_type, '学习')}"
                })
                task_id_counter += 1

    tasks = tasks[:10]

    strategy_explanation = ""
    if req.strategy_mode == "weakness_fix":
        strategy_explanation = "采用补弱优先策略，优先针对掌握度较低的知识点进行系统复习和强化训练"
    elif req.strategy_mode == "score_boost":
        strategy_explanation = "采用提分优先策略，重点突破中等难度知识点，性价比最高"
    elif req.strategy_mode == "exam_sprint":
        strategy_explanation = "采用考前冲刺策略，高频考点集中突破，模拟检测验证效果"
    else:
        strategy_explanation = "采用均衡发展策略，兼顾基础补强和综合提升"

    return {
        "status": "success",
        "strategy": req.strategy_mode,
        "tasks": tasks,
        "explanation": f"📋 学习策略: {strategy_explanation}\n\n📊 诊断发现 {len(weak_points)} 个薄弱知识点: {', '.join(weak_points)}\n\n📝 共安排 {len(tasks)} 个学习任务，针对性提升薄弱环节"
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