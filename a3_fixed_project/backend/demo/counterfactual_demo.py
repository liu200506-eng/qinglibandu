#!/usr/bin/env python
"""
反事实画像对比演示脚本

针对同一个"TCP慢启动"知识点，展示三种不同学生画像的教学决策差异：
- 学生A：基础薄弱型
- 学生B：理论较好但计算易错型
- 学生C：编程实践型

演示内容：
1. 诊断结论不同
2. 学习路径不同
3. 资源类型不同
4. 练习题难度不同
5. Agent决策理由不同
"""

import json
import sys
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class KnowledgeState:
    node_id: str = ""
    name: str = ""
    mastery: float = 0.0
    stability: float = 0.0
    error_count: int = 0
    correct_count: int = 0


class ProfileType:
    WEAK_FOUNDATION = "weak_foundation"
    CONFUSION_PRONE = "confusion_prone"
    STRONG_PRACTICE = "strong_practice"


@dataclass
class LearningProfile:
    student_id: str
    knowledge_mastery: float = 50.0
    prerequisite_gap: float = 0.0
    error_pattern_score: float = 50.0
    learning_efficiency: float = 50.0
    learning_persistence: float = 50.0
    learning_goals_constraints: dict = field(default_factory=dict)
    resource_preference: dict = field(default_factory=dict)
    confidence_scores: dict = field(default_factory=dict)
    evidence_sources: dict = field(default_factory=dict)
    emotional_state: float = 70.0
    cognitive_preference: str = "visual"
    self_driven_score: float = 50.0
    transfer_ability: float = 50.0
    knowledge_states: dict = field(default_factory=dict)
    error_distribution: dict = field(default_factory=dict)
    grade: str = ""
    subject: str = ""
    subjects: list = field(default_factory=list)
    learning_goal: str = ""
    weak_points: list = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    update_history: list = field(default_factory=list)
    profile_type: str = ""

    @classmethod
    def create_weak_foundation(cls, student_id: str) -> "LearningProfile":
        return cls(
            student_id=student_id,
            knowledge_mastery=25.0,
            prerequisite_gap=75.0,
            error_pattern_score=60.0,
            learning_efficiency=40.0,
            learning_persistence=50.0,
            learning_goals_constraints={"exam_date": "2026-08-15", "target_score": 60, "daily_available_minutes": 20},
            resource_preference={"visual": 0.7, "animation": 0.6, "exercise": 0.8},
            confidence_scores={"knowledge_mastery": 0.75, "prerequisite_gap": 0.60},
            evidence_sources={"knowledge_mastery": "诊断测试5题答对1题", "prerequisite_gap": "前置知识点TCP连接掌握度20%"},
            profile_type=ProfileType.WEAK_FOUNDATION,
        )

    @classmethod
    def create_confusion_prone(cls, student_id: str) -> "LearningProfile":
        return cls(
            student_id=student_id,
            knowledge_mastery=55.0,
            prerequisite_gap=30.0,
            error_pattern_score=75.0,
            learning_efficiency=70.0,
            learning_persistence=60.0,
            learning_goals_constraints={"exam_date": "2026-08-20", "target_score": 80, "daily_available_minutes": 45},
            resource_preference={"text": 0.8, "exercise": 0.9, "code": 0.5},
            confidence_scores={"knowledge_mastery": 0.85, "error_pattern_score": 0.70},
            evidence_sources={"knowledge_mastery": "理论题正确率80%", "error_pattern_score": "计算题错误率60%"},
            profile_type=ProfileType.CONFUSION_PRONE,
        )

    @classmethod
    def create_strong_practice(cls, student_id: str) -> "LearningProfile":
        return cls(
            student_id=student_id,
            knowledge_mastery=75.0,
            prerequisite_gap=10.0,
            error_pattern_score=40.0,
            learning_efficiency=85.0,
            learning_persistence=80.0,
            learning_goals_constraints={"exam_date": "2026-08-25", "target_score": 90, "daily_available_minutes": 60},
            resource_preference={"code": 0.9, "visual": 0.6, "experiment": 0.8},
            confidence_scores={"knowledge_mastery": 0.90, "learning_efficiency": 0.85},
            evidence_sources={"knowledge_mastery": "多次实践验证", "learning_efficiency": "单位时间掌握增量高"},
            profile_type=ProfileType.STRONG_PRACTICE,
        )

    def to_radar_data(self):
        return {
            "dimensions": [
                {"name": "知识掌握度", "value": self.knowledge_mastery},
                {"name": "先修知识缺口", "value": self.prerequisite_gap},
                {"name": "错误模式", "value": self.error_pattern_score},
                {"name": "学习效率", "value": self.learning_efficiency},
                {"name": "学习持续性", "value": self.learning_persistence},
                {"name": "资源偏好", "value": max(self.resource_preference.values()) if self.resource_preference else 50.0},
                {"name": "学习目标", "value": self.learning_goals_constraints.get("target_score", 50)},
            ]
        }


def generate_tcp_slow_start_diagnosis(profile: LearningProfile):
    """生成TCP慢启动诊断结论"""
    diagnosis = {
        "student_id": profile.student_id,
        "profile_type": profile.profile_type,
        "target_knowledge": "TCP慢启动",
        "diagnosis_time": datetime.now().isoformat(),
    }

    if profile.profile_type == ProfileType.WEAK_FOUNDATION:
        diagnosis.update({
            "diagnosis": "基础薄弱，概念理解不清",
            "key_issues": [
                "混淆拥塞窗口(cwnd)与接收窗口(rwnd)",
                "不理解慢启动阶段的指数增长机制",
                "缺乏TCP连接建立的基础知识",
            ],
            "mastery_estimate": 25,
            "recommendation": "先补窗口概念，再看动画演示，最后完成基础题",
            "estimated_time_minutes": 90,
        })
    elif profile.profile_type == ProfileType.CONFUSION_PRONE:
        diagnosis.update({
            "diagnosis": "理论较好，但计算易出错",
            "key_issues": [
                "RTT计算不准确",
                "分阶段计算容易混淆",
                "对ssthresh阈值理解不深",
            ],
            "mastery_estimate": 55,
            "recommendation": "直接进行RTT推导和分阶段计算训练",
            "estimated_time_minutes": 60,
        })
    elif profile.profile_type == ProfileType.STRONG_PRACTICE:
        diagnosis.update({
            "diagnosis": "编程能力强，偏好实践",
            "key_issues": [
                "缺乏真实网络环境下的实践经验",
                "对Reno/Cubic算法细节理解不够",
                "需要更深入的参数调优实践",
            ],
            "mastery_estimate": 75,
            "recommendation": "生成Python仿真代码和参数实验任务",
            "estimated_time_minutes": 45,
        })

    return diagnosis


def generate_learning_path(profile: LearningProfile):
    """生成学习路径"""
    path = {
        "student_id": profile.student_id,
        "target_knowledge": "TCP慢启动",
        "path_id": f"path_{profile.student_id}",
    }

    if profile.profile_type == ProfileType.WEAK_FOUNDATION:
        path["steps"] = [
            {
                "step": 1,
                "title": "窗口概念基础",
                "duration_minutes": 20,
                "resource_type": "video",
                "description": "动画演示拥塞窗口和接收窗口的区别",
                "learning_objective": "理解cwnd和rwnd的概念",
                "difficulty": 0.3,
            },
            {
                "step": 2,
                "title": "TCP三次握手",
                "duration_minutes": 15,
                "resource_type": "lecture",
                "description": "详细讲解TCP连接建立过程",
                "learning_objective": "掌握三次握手流程",
                "difficulty": 0.4,
            },
            {
                "step": 3,
                "title": "慢启动动画演示",
                "duration_minutes": 25,
                "resource_type": "animation",
                "description": "动态展示cwnd指数增长过程",
                "learning_objective": "直观理解慢启动机制",
                "difficulty": 0.5,
            },
            {
                "step": 4,
                "title": "基础练习题",
                "duration_minutes": 30,
                "resource_type": "exercise",
                "description": "5道基础概念题",
                "learning_objective": "巩固基本概念",
                "difficulty": 0.4,
            },
        ]
    elif profile.profile_type == ProfileType.CONFUSION_PRONE:
        path["steps"] = [
            {
                "step": 1,
                "title": "RTT计算原理",
                "duration_minutes": 15,
                "resource_type": "lecture",
                "description": "详细讲解RTT定义和计算方法",
                "learning_objective": "准确计算RTT",
                "difficulty": 0.6,
            },
            {
                "step": 2,
                "title": "分阶段计算练习",
                "duration_minutes": 25,
                "resource_type": "exercise",
                "description": "10道分阶段计算题",
                "learning_objective": "掌握cwnd增长计算",
                "difficulty": 0.7,
            },
            {
                "step": 3,
                "title": "ssthresh阈值分析",
                "duration_minutes": 15,
                "resource_type": "lecture",
                "description": "讲解阈值对拥塞控制的影响",
                "learning_objective": "理解ssthresh作用",
                "difficulty": 0.6,
            },
            {
                "step": 4,
                "title": "综合计算题",
                "duration_minutes": 5,
                "resource_type": "exercise",
                "description": "2道综合应用题",
                "learning_objective": "综合运用知识",
                "difficulty": 0.8,
            },
        ]
    elif profile.profile_type == ProfileType.STRONG_PRACTICE:
        path["steps"] = [
            {
                "step": 1,
                "title": "TCP拥塞控制仿真",
                "duration_minutes": 20,
                "resource_type": "code",
                "description": "Python代码实现TCP慢启动仿真",
                "learning_objective": "理解算法实现",
                "difficulty": 0.7,
            },
            {
                "step": 2,
                "title": "参数调优实验",
                "duration_minutes": 15,
                "resource_type": "code",
                "description": "调整ssthresh观察不同效果",
                "learning_objective": "掌握参数影响",
                "difficulty": 0.8,
            },
            {
                "step": 3,
                "title": "Reno vs Cubic对比",
                "duration_minutes": 10,
                "resource_type": "lecture",
                "description": "分析不同拥塞控制算法差异",
                "learning_objective": "理解算法演进",
                "difficulty": 0.8,
            },
            {
                "step": 4,
                "title": "实践项目",
                "duration_minutes": 0,
                "resource_type": "code",
                "description": "实现一个简化的拥塞控制模拟器",
                "learning_objective": "综合实践能力",
                "difficulty": 0.9,
            },
        ]

    return path


def generate_exercises(profile: LearningProfile):
    """生成练习题"""
    exercises = {
        "student_id": profile.student_id,
        "target_knowledge": "TCP慢启动",
        "exercise_count": 5,
    }

    if profile.profile_type == ProfileType.WEAK_FOUNDATION:
        exercises["exercises"] = [
            {
                "id": 1,
                "type": "concept",
                "difficulty": 0.3,
                "question": "TCP拥塞窗口(cwnd)的作用是什么？",
                "options": [
                    "限制发送方的数据量",
                    "限制接收方的数据量",
                    "测量网络延迟",
                    "加密数据传输",
                ],
                "correct_answer": 0,
                "hint": "拥塞窗口是发送方用来控制发送速率的",
            },
            {
                "id": 2,
                "type": "concept",
                "difficulty": 0.4,
                "question": "慢启动阶段cwnd如何增长？",
                "options": [
                    "线性增长",
                    "指数增长",
                    "恒定不变",
                    "随机增长",
                ],
                "correct_answer": 1,
                "hint": "每个RTT，cwnd翻倍",
            },
            {
                "id": 3,
                "type": "simple_calc",
                "difficulty": 0.4,
                "question": "cwnd初始值为1，经过2个RTT后cwnd等于多少？",
                "options": ["2", "4", "8", "16"],
                "correct_answer": 1,
                "hint": "每次RTT翻倍：1 -> 2 -> 4",
            },
            {
                "id": 4,
                "type": "concept",
                "difficulty": 0.5,
                "question": "当cwnd达到ssthresh时，TCP进入什么阶段？",
                "options": [
                    "慢启动",
                    "拥塞避免",
                    "快速重传",
                    "快速恢复",
                ],
                "correct_answer": 1,
                "hint": "ssthresh是慢启动阈值",
            },
            {
                "id": 5,
                "type": "simple_calc",
                "difficulty": 0.5,
                "question": "cwnd=1, ssthresh=8。需要几个RTT才能达到ssthresh？",
                "options": ["2", "3", "4", "8"],
                "correct_answer": 2,
                "hint": "1 -> 2 -> 4 -> 8，共3个RTT",
            },
        ]
    elif profile.profile_type == ProfileType.CONFUSION_PRONE:
        exercises["exercises"] = [
            {
                "id": 1,
                "type": "calculation",
                "difficulty": 0.6,
                "question": "cwnd=4, ssthresh=16。一个RTT内收到4个ACK，cwnd变为？",
                "options": ["4", "8", "12", "16"],
                "correct_answer": 1,
                "hint": "慢启动阶段每个ACK增加1，收到4个ACK增加4",
            },
            {
                "id": 2,
                "type": "calculation",
                "difficulty": 0.7,
                "question": "cwnd=10, ssthresh=10。一个RTT后cwnd变为？",
                "options": ["10", "11", "20", "15"],
                "correct_answer": 1,
                "hint": "达到ssthresh，进入拥塞避免，线性增长",
            },
            {
                "id": 3,
                "type": "calculation",
                "difficulty": 0.7,
                "question": "cwnd=15, ssthresh=10。连续2个RTT后cwnd变为？",
                "options": ["15", "16", "17", "30"],
                "correct_answer": 2,
                "hint": "拥塞避免阶段每个RTT增加1",
            },
            {
                "id": 4,
                "type": "analysis",
                "difficulty": 0.8,
                "question": "RTT=200ms, cwnd=8, ssthresh=32。发送完8个报文段后，至少等待多久才能发送新数据？",
                "options": ["200ms", "400ms", "800ms", "1600ms"],
                "correct_answer": 0,
                "hint": "需要等待ACK返回，一个RTT",
            },
            {
                "id": 5,
                "type": "analysis",
                "difficulty": 0.8,
                "question": "cwnd=1, ssthresh=64。发送速率随时间如何变化？",
                "options": [
                    "匀速增加",
                    "指数增加直到ssthresh，然后线性增加",
                    "一直指数增加",
                    "恒定不变",
                ],
                "correct_answer": 1,
                "hint": "慢启动指数增长，拥塞避免线性增长",
            },
        ]
    elif profile.profile_type == ProfileType.STRONG_PRACTICE:
        exercises["exercises"] = [
            {
                "id": 1,
                "type": "code",
                "difficulty": 0.7,
                "question": "编写Python代码模拟TCP慢启动过程，cwnd从1开始，每收到一个ACK增加1",
                "code_template": "def slow_start_simulation(initial_cwnd, ssthresh, num_acks):\n    cwnd = initial_cwnd\n    # 请补充代码\n    return cwnd",
                "hint": "循环处理每个ACK，当cwnd < ssthresh时增加",
            },
            {
                "id": 2,
                "type": "code",
                "difficulty": 0.8,
                "question": "修改代码，加入拥塞避免逻辑",
                "code_template": "def congestion_control(cwnd, ssthresh, event_type):\n    # event_type: 'ack' or 'loss'\n    # 请补充代码\n    return cwnd",
                "hint": "loss时cwnd减半，ssthresh=cwnd/2",
            },
            {
                "id": 3,
                "type": "analysis",
                "difficulty": 0.8,
                "question": "比较Reno和Cubic算法在高带宽延迟积网络中的表现差异",
                "hint": "Cubic使用三次函数，Reno使用线性增长",
            },
            {
                "id": 4,
                "type": "code",
                "difficulty": 0.9,
                "question": "实现一个完整的TCP拥塞控制模拟器，支持参数配置",
                "code_template": "class TCPCongestionControl:\n    def __init__(self, algorithm='reno', ssthresh=64):\n        pass\n    def simulate(self, duration):\n        pass",
                "hint": "需要跟踪cwnd、ssthresh、RTT等状态",
            },
            {
                "id": 5,
                "type": "experiment",
                "difficulty": 0.9,
                "question": "设计实验对比不同ssthresh值对吞吐量的影响",
                "hint": "固定RTT，改变ssthresh，测量稳态吞吐量",
            },
        ]

    return exercises


def generate_resource_pack(profile: LearningProfile):
    """生成资源包"""
    resource_pack = {
        "student_id": profile.student_id,
        "target_knowledge": "TCP慢启动",
        "pack_id": f"pack_{profile.student_id}",
    }

    if profile.profile_type == ProfileType.WEAK_FOUNDATION:
        resource_pack["resources"] = [
            {"type": "video", "title": "TCP窗口概念动画", "duration": "3:20"},
            {"type": "animation", "title": "慢启动过程演示", "duration": "2:45"},
            {"type": "mind_map", "title": "TCP拥塞控制概念图"},
            {"type": "lecture", "title": "TCP慢启动讲义（基础版）", "pages": 8},
            {"type": "exercise", "title": "基础练习题", "count": 5},
        ]
        resource_pack["preferred_format"] = "visual"
        resource_pack["difficulty_level"] = "beginner"
    elif profile.profile_type == ProfileType.CONFUSION_PRONE:
        resource_pack["resources"] = [
            {"type": "lecture", "title": "RTT计算详解", "pages": 12},
            {"type": "lecture", "title": "ssthresh阈值分析", "pages": 6},
            {"type": "exercise", "title": "分阶段计算题", "count": 10},
            {"type": "exercise", "title": "综合应用题", "count": 2},
            {"type": "video", "title": "计算过程演示", "duration": "5:15"},
        ]
        resource_pack["preferred_format"] = "text"
        resource_pack["difficulty_level"] = "intermediate"
    elif profile.profile_type == ProfileType.STRONG_PRACTICE:
        resource_pack["resources"] = [
            {"type": "code", "title": "TCP仿真代码", "lines": 80},
            {"type": "code", "title": "参数调优实验", "lines": 50},
            {"type": "lecture", "title": "Reno/Cubic对比分析", "pages": 10},
            {"type": "exercise", "title": "编程实践题", "count": 3},
            {"type": "experiment", "title": "拥塞控制实验", "description": "测量不同参数下的性能"},
        ]
        resource_pack["preferred_format"] = "code"
        resource_pack["difficulty_level"] = "advanced"

    return resource_pack


def main():
    """主函数：生成三种画像的对比演示"""
    print("-" * 80)
    print("反事实画像对比演示 - TCP慢启动知识点")
    print("-" * 80)

    students = [
        ("student_A", "基础薄弱型学生", LearningProfile.create_weak_foundation("student_A")),
        ("student_B", "理论较好但计算易错型学生", LearningProfile.create_confusion_prone("student_B")),
        ("student_C", "编程实践型学生", LearningProfile.create_strong_practice("student_C")),
    ]

    all_results = {}

    for student_id, student_name, profile in students:
        print(f"\n{'-' * 80}")
        print(f"学生: {student_name} ({student_id})")
        print(f"{'-' * 80}")

        print("\n画像特征：")
        radar_data = profile.to_radar_data()
        for dim in radar_data["dimensions"]:
            print(f"  * {dim['name']}: {dim['value']:.1f}")

        print("\n诊断结论：")
        diagnosis = generate_tcp_slow_start_diagnosis(profile)
        print(f"  诊断结果: {diagnosis['diagnosis']}")
        print(f"  掌握度预估: {diagnosis['mastery_estimate']}%")
        print(f"  推荐策略: {diagnosis['recommendation']}")
        print(f"  预计时长: {diagnosis['estimated_time_minutes']}分钟")

        print("\n学习路径：")
        path = generate_learning_path(profile)
        for step in path["steps"]:
            print(f"  {step['step']}. [{step['resource_type']}] {step['title']} ({step['duration_minutes']}分钟) - 难度: {step['difficulty']}")

        print("\n练习题类型：")
        exercises = generate_exercises(profile)
        types = set(e["type"] for e in exercises["exercises"])
        print(f"  题型分布: {', '.join(types)}")
        avg_difficulty = sum(e["difficulty"] for e in exercises["exercises"]) / len(exercises["exercises"])
        print(f"  平均难度: {avg_difficulty:.2f}")

        print("\n资源包：")
        pack = generate_resource_pack(profile)
        print(f"  偏好格式: {pack['preferred_format']}")
        print(f"  难度级别: {pack['difficulty_level']}")
        for res in pack["resources"]:
            print(f"  * [{res['type']}] {res['title']}")

        all_results[student_id] = {
            "profile": profile.to_radar_data(),
            "diagnosis": diagnosis,
            "learning_path": path,
            "exercises": exercises,
            "resource_pack": pack,
        }

    print(f"\n{'-' * 80}")
    print("决策差异对比总结")
    print(f"{'-' * 80}")
    print(f"{'维度':<20} {'学生A (基础薄弱)':<30} {'学生B (理论强)':<30} {'学生C (实践型)':<30}")
    print(f"{'-' * 110}")
    print(f"{'诊断结论':<20} {all_results['student_A']['diagnosis']['diagnosis'][:28]:<30} {all_results['student_B']['diagnosis']['diagnosis'][:28]:<30} {all_results['student_C']['diagnosis']['diagnosis'][:28]:<30}")
    print(f"{'掌握度':<20} {str(all_results['student_A']['diagnosis']['mastery_estimate']) + '%':<30} {str(all_results['student_B']['diagnosis']['mastery_estimate']) + '%':<30} {str(all_results['student_C']['diagnosis']['mastery_estimate']) + '%':<30}")
    print(f"{'预计时长':<20} {str(all_results['student_A']['diagnosis']['estimated_time_minutes']) + '分钟':<30} {str(all_results['student_B']['diagnosis']['estimated_time_minutes']) + '分钟':<30} {str(all_results['student_C']['diagnosis']['estimated_time_minutes']) + '分钟':<30}")
    print(f"{'资源偏好':<20} {all_results['student_A']['resource_pack']['preferred_format']:<30} {all_results['student_B']['resource_pack']['preferred_format']:<30} {all_results['student_C']['resource_pack']['preferred_format']:<30}")
    print(f"{'难度级别':<20} {all_results['student_A']['resource_pack']['difficulty_level']:<30} {all_results['student_B']['resource_pack']['difficulty_level']:<30} {all_results['student_C']['resource_pack']['difficulty_level']:<30}")
    print(f"{'推荐策略':<20} {all_results['student_A']['diagnosis']['recommendation'][:28]:<30} {all_results['student_B']['diagnosis']['recommendation'][:28]:<30} {all_results['student_C']['diagnosis']['recommendation'][:28]:<30}")

    with open("demo/counterfactual_demo_output.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n完整数据已保存到: demo/counterfactual_demo_output.json")


if __name__ == "__main__":
    main()
