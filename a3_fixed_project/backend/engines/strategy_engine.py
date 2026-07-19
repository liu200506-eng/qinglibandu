from graph.state import StrategyMode, LearningProfile, LearningTask
import uuid


class StrategyEngine:

    def recommend_strategy(self, profile: LearningProfile) -> StrategyMode:
        if profile.knowledge_mastery < 40:
            return StrategyMode.WEAKNESS_FIX

        if profile.emotional_state < 40:
            return StrategyMode.EXAM_SPRINT

        if profile.knowledge_mastery >= 60 and profile.transfer_ability < 50:
            return StrategyMode.SCORE_BOOST

        return StrategyMode.BALANCED

    def generate_learning_path(
        self,
        profile: LearningProfile,
        weak_points: list[str],
        strategy_mode: StrategyMode
    ) -> list[LearningTask]:
        if strategy_mode == StrategyMode.WEAKNESS_FIX:
            return self._generate_weakness_fix_path(profile, weak_points)
        elif strategy_mode == StrategyMode.SCORE_BOOST:
            return self._generate_score_boost_path(profile, weak_points)
        elif strategy_mode == StrategyMode.EXAM_SPRINT:
            return self._generate_exam_sprint_path(profile, weak_points)
        else:
            return self._generate_balanced_path(profile, weak_points)

    def _generate_weakness_fix_path(
        self, profile: LearningProfile, weak_points: list[str]
    ) -> list[LearningTask]:
        tasks = []
        priority = 0

        for wp in weak_points[:5]:
            ks = profile.knowledge_states.get(wp)

            if ks and ks.dependencies:
                for dep in ks.dependencies:
                    dep_ks = profile.knowledge_states.get(dep)
                    if dep_ks and dep_ks.mastery < 0.7:
                        tasks.append(LearningTask(
                            task_id=str(uuid.uuid4())[:8],
                            title=f"补充前置: {dep_ks.name}",
                            task_type="lesson",
                            knowledge_points=[dep],
                            difficulty=0.3,
                            estimated_minutes=15,
                            expected_gain=0.6,
                            priority=priority,
                            explanation=f"'{ks.name}'依赖此前置知识"
                        ))
                        priority += 1

            tasks.append(LearningTask(
                task_id=str(uuid.uuid4())[:8],
                title=f"重点讲解: {ks.name if ks else wp}",
                task_type="lesson",
                knowledge_points=[wp],
                difficulty=0.4,
                estimated_minutes=20,
                expected_gain=0.7,
                priority=priority,
                explanation=f"掌握度仅{ks.mastery:.0%}" if ks else "诊断发现的薄弱点"
            ))
            priority += 1

            tasks.append(LearningTask(
                task_id=str(uuid.uuid4())[:8],
                title=f"专项练习: {ks.name if ks else wp}",
                task_type="exercise",
                knowledge_points=[wp],
                difficulty=0.5,
                estimated_minutes=15,
                expected_gain=0.5,
                priority=priority,
                explanation="通过练习巩固学习内容"
            ))
            priority += 1

        return tasks

    def _generate_score_boost_path(
        self, profile: LearningProfile, weak_points: list[str]
    ) -> list[LearningTask]:
        tasks = []
        priority = 0

        medium_points = []
        for kid, ks in profile.knowledge_states.items():
            if 0.4 <= ks.mastery <= 0.75:
                medium_points.append((kid, ks))

        medium_points.sort(key=lambda x: x[1].mastery, reverse=True)

        for kid, ks in medium_points[:6]:
            tasks.append(LearningTask(
                task_id=str(uuid.uuid4())[:8],
                title=f"强化训练: {ks.name}",
                task_type="exercise",
                knowledge_points=[kid],
                difficulty=0.6,
                estimated_minutes=20,
                expected_gain=0.8,
                priority=priority,
                explanation=f"掌握度{ks.mastery:.0%}，接近突破点"
            ))
            priority += 1

        return tasks

    def _generate_exam_sprint_path(
        self, profile: LearningProfile, weak_points: list[str]
    ) -> list[LearningTask]:
        tasks = []

        tasks.append(LearningTask(
            task_id=str(uuid.uuid4())[:8],
            title="模拟诊断测试",
            task_type="diagnosis",
            knowledge_points=weak_points[:10],
            difficulty=0.7,
            estimated_minutes=30,
            expected_gain=0.3,
            priority=0,
            explanation="精准定位当前水平"
        ))

        for i, wp in enumerate(weak_points[:3]):
            tasks.append(LearningTask(
                task_id=str(uuid.uuid4())[:8],
                title=f"考点速攻: {wp}",
                task_type="exercise",
                knowledge_points=[wp],
                difficulty=0.7,
                estimated_minutes=15,
                expected_gain=0.6,
                priority=i + 1,
                explanation="高频考点集中突破"
            ))

        tasks.append(LearningTask(
            task_id=str(uuid.uuid4())[:8],
            title="再次模拟检测",
            task_type="diagnosis",
            knowledge_points=weak_points[:10],
            difficulty=0.7,
            estimated_minutes=25,
            expected_gain=0.4,
            priority=len(tasks),
            explanation="验证冲刺效果"
        ))

        return tasks

    def _generate_balanced_path(
        self, profile: LearningProfile, weak_points: list[str]
    ) -> list[LearningTask]:
        tasks = []
        priority = 0

        for wp in weak_points[:2]:
            tasks.append(LearningTask(
                task_id=str(uuid.uuid4())[:8],
                title=f"知识补强: {wp}",
                task_type="lesson",
                knowledge_points=[wp],
                difficulty=0.4,
                estimated_minutes=20,
                expected_gain=0.6,
                priority=priority,
                explanation="基础补强环节"
            ))
            priority += 1

        tasks.append(LearningTask(
            task_id=str(uuid.uuid4())[:8],
            title="综合练习",
            task_type="exercise",
            knowledge_points=weak_points[:4],
            difficulty=0.6,
            estimated_minutes=25,
            expected_gain=0.5,
            priority=priority,
            explanation="提升知识迁移能力"
        ))
        priority += 1

        tasks.append(LearningTask(
            task_id=str(uuid.uuid4())[:8],
            title="周期复习",
            task_type="review",
            knowledge_points=weak_points[:6],
            difficulty=0.3,
            estimated_minutes=15,
            expected_gain=0.4,
            priority=priority,
            explanation="间隔复习防止遗忘"
        ))

        return tasks